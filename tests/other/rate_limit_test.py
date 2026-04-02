# -*- coding: utf-8 -*-
"""
@desc: 频率限制测试
@author: 1nchaos
@time: 2023/4/4
"""
import sys
import time
import threading
from urllib.parse import urlparse

# 直接复制 RateLimiter 类进行测试（避免导入问题）

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


def test_rate_limiter_basic():
    """测试频率限制器基本功能"""
    print("=== 测试频率限制器基本功能 ===")
    
    # 重置单例
    RateLimiter._instance = None
    
    limiter = RateLimiter()
    limiter.enable(True)
    limiter.set_limit(5, window_seconds=10)  # 10秒内最多5次
    
    url = "https://quote.eastmoney.com/test"
    
    for i in range(7):
        wait_time = limiter.acquire(url)
        print(f"请求 {i+1}: 等待时间 = {wait_time:.2f}秒")
        if wait_time > 0:
            time.sleep(wait_time)


def test_rate_limiter_different_domains():
    """测试不同域名的独立限制"""
    print("\n=== 测试不同域名的独立限制 ===")
    
    # 重置单例
    RateLimiter._instance = None
    
    limiter = RateLimiter()
    limiter.enable(True)
    limiter.set_limit(3, window_seconds=10)
    
    # 为不同域名设置不同限制
    limiter.set_domain_limit('domain1.com', 2, 10)
    limiter.set_domain_limit('domain2.com', 5, 10)
    
    print("domain1.com 限制: 10秒2次")
    print("domain2.com 限制: 10秒5次")
    
    # 测试 domain1
    print("\n测试 domain1.com:")
    for i in range(4):
        wait_time = limiter.acquire("https://domain1.com/api")
        print(f"  请求 {i+1}: 等待时间 = {wait_time:.2f}秒")
        if wait_time > 0:
            time.sleep(wait_time)
    
    # 测试 domain2
    print("\n测试 domain2.com:")
    for i in range(4):
        wait_time = limiter.acquire("https://domain2.com/api")
        print(f"  请求 {i+1}: 等待时间 = {wait_time:.2f}秒")
        if wait_time > 0:
            time.sleep(wait_time)


def test_rate_limiter_thread_safe():
    """测试线程安全性"""
    print("\n=== 测试线程安全性 ===")
    
    # 重置单例
    RateLimiter._instance = None
    
    limiter = RateLimiter()
    limiter.enable(True)
    limiter.set_limit(10, window_seconds=10)
    
    results = []
    results_lock = threading.Lock()
    
    def worker(thread_id):
        for i in range(3):
            wait_time = limiter.acquire("https://test.com/api")
            with results_lock:
                results.append((thread_id, i, wait_time))
            if wait_time > 0:
                time.sleep(wait_time)
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"共 {len(results)} 个请求完成")
    waits = [r[2] for r in results if r[2] > 0]
    print(f"其中 {len(waits)} 个请求需要等待")


def test_domain_extraction():
    """测试域名提取功能"""
    print("\n=== 测试域名提取功能 ===")
    
    test_urls = [
        "https://quote.eastmoney.com/center/",
        "http://push2his.eastmoney.com/api",
        "https://web.sqt.gtimg.cn/q=sh601666",
        "https://finance.pae.baidu.com/vapi/v1/getquotation",
        "http://stock.finance.qq.com/api",
    ]
    
    for url in test_urls:
        domain = RateLimiter._extract_domain(url)
        print(f"{url[:50]:<50} -> {domain}")


def test_disable_enable():
    """测试启用禁用功能"""
    print("\n=== 测试启用禁用功能 ===")
    
    # 重置单例
    RateLimiter._instance = None
    
    limiter = RateLimiter()
    limiter.set_limit(2, window_seconds=10)
    
    # 启用状态
    limiter.enable(True)
    print("频率限制已启用")
    for i in range(4):
        wait_time = limiter.acquire("https://test.com/api")
        print(f"  请求 {i+1}: 等待时间 = {wait_time:.2f}秒")
        if wait_time > 0:
            time.sleep(wait_time)
    
    # 禁用状态
    limiter.enable(False)
    print("\n频率限制已禁用")
    for i in range(4):
        wait_time = limiter.acquire("https://test.com/api")
        print(f"  请求 {i+1}: 等待时间 = {wait_time:.2f}秒")


if __name__ == '__main__':
    # 运行测试
    test_rate_limiter_basic()
    test_rate_limiter_different_domains()
    test_rate_limiter_thread_safe()
    test_domain_extraction()
    test_disable_enable()
    print("\n=== 所有测试完成 ===")
