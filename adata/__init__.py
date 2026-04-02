# -*- coding: utf-8 -*-
"""
@desc: adata
@author: 1nchaos
@time: 2023/4/4
"""
# -*- coding: utf-8 -*-

import logging

from adata.__version__ import __version__
from adata.bond import bond
from adata.common.utils.sunrequests import SunProxy, sun_requests
from adata.fund import fund
from adata.sentiment import sentiment
from adata.stock import stock


def version():
    return __version__


def proxy(is_proxy=False, ip: str = None, proxy_url: str = None):
    """
    设置请求代理
    :param is_proxy: 是否启用代理，默认：否
    :param ip: 代理ip地址；格式样例：192.123.123.4:4568
    :param proxy_url: 能获取到代理的url，返回格式必须和ip一样
    """
    SunProxy.set('is_proxy', is_proxy)
    SunProxy.set('ip', ip)
    SunProxy.set('proxy_url', proxy_url)
    return


def rate_limit(limit: int = 30, window_seconds: int = 60, enabled: bool = True):
    """
    设置请求频率限制
    :param limit: 每个时间窗口内最大请求次数，默认30次
    :param window_seconds: 时间窗口（秒），默认60秒
    :param enabled: 是否启用频率限制，默认True
    """
    sun_requests.enable_rate_limit(enabled)
    if enabled:
        sun_requests.set_rate_limit(limit, window_seconds)
    return


def domain_rate_limit(domain: str, limit: int, window_seconds: int = 60):
    """
    为特定域名设置频率限制
    :param domain: 域名，如 'quote.eastmoney.com'
    :param limit: 时间窗口内最大请求次数
    :param window_seconds: 时间窗口（秒），默认60秒
    """
    sun_requests.set_domain_rate_limit(domain, limit, window_seconds)
    return


# set up logging
logger = logging.getLogger("adata")


def set_logger():
    format_string = "%(asctime)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%dT%H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)


set_logger()
