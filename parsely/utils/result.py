# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/27 11:55
# @File    : result.py
# @Desc    : 返回客户端的Result类


class Result:
    def __init__(self, errno, errmsg, data=None):
        """
        返回客户端的格式
        :param errno: 错误码
        :param errmsg: 错误消息
        :param data: 数据
        """
        self.errno = errno.get_code()
        self.errmsg = errmsg
        self.data = data

    def as_dict(self):
        """
        属性转dict，用于构造json返回给客户端
        :return:
        """
        return self.__dict__
