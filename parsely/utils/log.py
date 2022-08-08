# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/23 15:57
# @File    : log.py
# @Desc    : 进程安全级别的日志模块，支持输出到文件及标准输出

import logging
import multiprocessing


def create_logger():
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    #fh = logging.FileHandler('process.log')
    ch = logging.StreamHandler()
    fmt = '%(asctime)s - %(filename)s - Line: %(lineno)d - [%(levelname)s] - %(message)s'
    formatter = logging.Formatter(fmt)
    #fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    #logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


logger = create_logger()
