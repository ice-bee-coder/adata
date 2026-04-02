# -*- coding: utf-8 -*-
"""
代理:https://jahttp.zhimaruanjian.com/getapi/

@desc: adata 请求工具类
@author: 1nchaos
@time:2023/3/30
@log: 封装请求次数
"""

import threading
import time
from urllib.parse import urlparse

import requests


class SunProxy(object):
    _data = {}
    _instance_lock = threading.Lock()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(SunProxy, "_instance"):
            with SunProxy._instance_lock:
                if not hasattr(SunProxy, "_instance"):
                    SunProxy._instance = object.__new__(cls)

    @classmethod
    def set(cls, key, value):
        cls._data[key] = value

    @classmethod
    def get(cls, key):
        return cls._data.get(key)

    @classmethod
    def delete(cls, key):
        if key in cls._data:
            del cls._data[key]


class RateLimiter(object):
    """
    域名级别频率限制器
    默认每分钟每个域名30次请求
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._domain_records = {}
        self._lock = threading.Lock()
        self._default_limit = 30
        self._default_window = 60
        self._enabled = True

    def set_limit(self, limit: int, window_seconds: int = 60):
        """
        设置全局默认频率限制
        :param limit: 窗口期内最大请求次数
        :param window_seconds: 时间窗口（秒），默认60秒
        """
        with self._lock:
            self._default_limit = limit
            self._default_window = window_seconds

    def set_domain_limit(self, domain: str, limit: int, window_seconds: int = 60):
        """
        为特定域名设置频率限制
        :param domain: 域名，如 'quote.eastmoney.com'
        :param limit: 窗口期内最大请求次数
        :param window_seconds: 时间窗口（秒）
        """
        with self._lock:
            if domain not in self._domain_records:
                self._domain_records[domain] = {'timestamps': []}
            self._domain_records[domain]['limit'] = limit
            self._domain_records[domain]['window'] = window_seconds

    def enable(self, enabled: bool = True):
        """启用或禁用频率限制"""
        with self._lock:
            self._enabled = enabled

    def acquire(self, url: str):
        """
        请求频率限制，如果超过限制则等待
        :param url: 请求的URL
        :return: 等待的时间（秒）
        """
        if not self._enabled:
            return 0

        domain = self._extract_domain(url)
        now = time.time()

        with self._lock:
            if domain not in self._domain_records:
                self._domain_records[domain] = {
                    'timestamps': [],
                    'limit': self._default_limit,
                    'window': self._default_window
                }

            record = self._domain_records[domain]
            limit = record.get('limit', self._default_limit)
            window = record.get('window', self._default_window)

            # 清理过期的记录
            cutoff = now - window
            record['timestamps'] = [ts for ts in record['timestamps'] if ts > cutoff]

            # 检查是否需要等待
            if len(record['timestamps']) >= limit:
                # 计算需要等待的时间
                oldest = min(record['timestamps'])
                wait_time = window - (now - oldest)
                if wait_time > 0:
                    return wait_time

            # 记录当前请求
            record['timestamps'].append(now)
            return 0

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从URL中提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return url.lower()


class SunRequests(object):
    def __init__(self, sun_proxy: SunProxy = None) -> None:
        super().__init__()
        self.sun_proxy = sun_proxy
        self._rate_limiter = RateLimiter()

    def request(self, method='get', url=None, times=3, retry_wait_time=1588, proxies=None, wait_time=None,
                rate_limit: bool = True, **kwargs):
        """
        简单封装的请求，参考requests，增加循环次数和次数之间的等待时间
        :param proxies: 代理配置
        :param method: 请求方法： get；post
        :param url: url
        :param times: 次数，int
        :param retry_wait_time: 重试等待时间，毫秒
        :param wait_time: 等待时间：毫秒；表示每个请求的间隔时间，在请求之前等待sleep，主要用于防止请求太频繁的限制。
        :param rate_limit: 是否启用频率限制，默认True
        :param kwargs: 其它 requests 参数，用法相同
        :return: res
        """
        # 1. 频率限制检查
        if rate_limit and url:
            wait_seconds = self._rate_limiter.acquire(url)
            if wait_seconds > 0:
                time.sleep(wait_seconds)

        # 2. 获取设置代理
        proxies = self.__get_proxies(proxies)

        # 3. 请求数据结果
        res = None
        for i in range(times):
            if wait_time:
                time.sleep(wait_time / 1000)
            res = requests.request(method=method, url=url, proxies=proxies, **kwargs)
            if res.status_code in (200, 404):
                return res
            time.sleep(retry_wait_time / 1000)
            if i == times - 1:
                return res
        return res

    def set_rate_limit(self, limit: int, window_seconds: int = 60):
        """
        设置全局默认频率限制
        :param limit: 窗口期内最大请求次数，默认30
        :param window_seconds: 时间窗口（秒），默认60秒
        """
        self._rate_limiter.set_limit(limit, window_seconds)

    def set_domain_rate_limit(self, domain: str, limit: int, window_seconds: int = 60):
        """
        为特定域名设置频率限制
        :param domain: 域名，如 'quote.eastmoney.com'
        :param limit: 窗口期内最大请求次数
        :param window_seconds: 时间窗口（秒）
        """
        self._rate_limiter.set_domain_limit(domain, limit, window_seconds)

    def enable_rate_limit(self, enabled: bool = True):
        """
        启用或禁用频率限制
        :param enabled: True启用，False禁用
        """
        self._rate_limiter.enable(enabled)

    def __get_proxies(self, proxies):
        """
        获取代理配置
        """
        if proxies is None:
            proxies = {}
        is_proxy = SunProxy.get('is_proxy')
        ip = SunProxy.get('ip')
        proxy_url = SunProxy.get('proxy_url')
        if not ip and is_proxy and proxy_url:
            ip = requests.get(url=proxy_url).text.replace('\r\n', '') \
                .replace('\r', '').replace('\n', '').replace('\t', '')
        if is_proxy and ip:
            proxies = {'https': f"http://{ip}", 'http': f"http://{ip}"}
        return proxies


sun_requests = SunRequests()
