# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/29 10:09
# @File    : errno.py
# @Desc    : 错误码枚举

from enum import Enum, unique


class PARAM_ERROR(Exception):
    pass


@unique
class ErrNo(Enum):
    SUCCESS = 0
    SYSTEM_ERROR = 10000
    PARAM_ERROR = 20000
    DB_ERROR = 30000
    NETWORK_ERROR = 40000
    TASK_ERROR = 50000
    UNKNOWN_ERROR = 60000

    def get_code(self):
        """
        根据枚举名称取错误码
        :return: 错误码
        """
        return self.value
