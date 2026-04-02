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
from adata.common.utils.sunrequests import SunProxy, set_rate_limit, get_rate_limit
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


def rate_limit(limit, domain=None):
    """
    设置频率限制
    :param limit: 每分钟请求次数
    :param domain: 域名，不传则设置全局默认限制
    """
    set_rate_limit(limit, domain)
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
