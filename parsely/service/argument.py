# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/27 10:53
# @File    : argument.py
# @Desc    : 请求参数类及参数类型枚举定义
import copy
import datetime
import itertools
import json
import os
from enum import Enum, unique

from flask_restful import reqparse
from werkzeug.datastructures import FileStorage

from parsely.utils.errno import PARAM_ERROR
from ..service.service_manager import _service_manager


class ReqArgument(object):
    def __init__(self, name, type, required, help='', extensions=None):
        """
        客户端请求构造参数类
        :param name: 参数名称，字符串
        :param type: 参数类型，ReqArgumentType类型，支持INT、STRING、FILE
        :param required: 是否必须传
        :param help: 错误提示
        :param 扩展名列表: list类型的扩展名列表，扩展名不限大小写，eg：['jpg','jpeg']，仅当type参数为FILE时生效
        """
        self.name = name
        self.type = type
        self.required = required
        self.help = help
        self.extensions = extensions


@unique
class ReqArgumentType(Enum):
    INT = int
    FLOAT = float
    STRING = str
    FILE = FileStorage

    def get_code(self):
        """
        根据枚举名称取错误码
        :return: 错误码
        """
        return self.value


# class OutputParams(object):
#     """
#     输出参数类，方便开发者构建输出参数
#     """
#
#     def __init__(self):
#         self._dict = dict()
#         self.file_list = list()
#
#     def add_param(self, key, value, use_cache_dir):
#         """
#         为output_params中添加键值对
#         :param key: 开发者指定的key
#         :param value: 对应key的值
#         :param use_cache_dir: bool类型，若为True，则输出结果文件记录在配置文件中的缓存输出目录下；否则直接记录键值对信息
#         :return:
#         """
#         if use_cache_dir:
#             self.file_list.append(key)
#             value = os.path.join(_service_manager.config['cache.root.dir'],
#                                  _service_manager.config['cache.output_files.dir'], value)
#         self._dict[key] = value
#
#     def as_dict(self):
#         self._dict["file_list"] = self.file_list
#         return self._dict
#

class Params(object):
    """
    输出参数类，方便开发者构建输出参数
    """

    def __init__(self):
        self._input_params = dict()
        self._output_params = dict()

    def default_arguments(self):
        """
        通用的url参数，如添加回调URL等
        """
        return [
            ReqArgument('notify_url', ReqArgumentType.STRING, False, "tack call back url(POST)", )
        ]

    @classmethod
    def loads(cls, input_params_json, output_params_json):
        """
        加载PARAM
        :param input_params_json:从数据库读取的输入参数的json信息
        :param output_params_json:从数据库读取的输出参数的json信息
        :return:
        """
        params = cls()
        params._input_params = json.loads(input_params_json)
        params._output_params = json.loads(output_params_json)
        return params

    def dumps(self):
        """
        将参数序列化为json格式，返回结果为inputparams和outputparams序列化后的元组
        """
        return json.dumps(self._input_params, ensure_ascii=False), json.dumps(self._output_params, ensure_ascii=False)

    def add_reqArguments(self, reqArguments):
        """
        添加参数列表,这里参数列表是输入参数的列表
        :param reqArguments:ReqArgument类型的参数列表,框架里面的self.params用户定义的参数
        """
        parser = reqparse.RequestParser()
        # 用户上传文件因flask restful未实现验证相关功能，需要开发者自行实现
        upload_file_ext_dict = dict()
        # 根据self.params来构造parser的arguments
        for argument in itertools.chain(reqArguments, self.default_arguments()):
            if argument.type is ReqArgumentType.FILE:
                parser.add_argument(argument.name, type=argument.type.get_code(), required=argument.required,
                                    help=argument.help, location='files')
                upload_file_ext_dict[argument.name] = argument.extensions
            else:
                parser.add_argument(argument.name, type=argument.type.get_code(), required=argument.required,
                                    help=argument.help, location='form')
        args = parser.parse_args()
        for upload_file in upload_file_ext_dict:
            ufile = args[upload_file]
            if ufile.filename == '':
                errmsg = 'argument {} upload no file'.format(upload_file)
                raise PARAM_ERROR(errmsg)
                # return Result(ErrNo.PARAM_ERROR, errmsg).as_dict()
            ext = os.path.splitext(ufile.filename)[-1][1:]
            if ext.lower() not in upload_file_ext_dict[upload_file]:
                errmsg = 'argument {} file extension should be in {}'.format(upload_file,
                                                                             upload_file_ext_dict[upload_file])
                raise PARAM_ERROR(errmsg)
                # return Result(ErrNo.PARAM_ERROR, errmsg).as_dict()
        # 上传文件初步验证没有问题后，则保存到缓存目录下
        for upload_file in upload_file_ext_dict:
            file = args[upload_file]
            # 将用户上传文件保存到缓存目录，文件名以“当前时间_原文件名"命名
            input_filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S_') + file.filename
            input_filepath = os.path.join(_service_manager.config['cache.root.dir'],
                                          _service_manager.config['cache.input_files.dir'], input_filename)
            file.save(input_filepath)
            # 记录保存路径，格式为【原始文件名，服务器缓存文件路径】
            args[upload_file] = [file.filename, input_filepath]
        # #@print(args)
        self._input_params.update(args)

    def add_param(self, key, value, use_cache_dir=False):
        """
        为output_params中添加键值对
        :param key: 开发者指定的key
        :param value: 对应key的值
        :param use_cache_dir: bool类型，若为True，则输出结果文件记录在配置文件中的缓存输出目录下；否则直接记录键值对信息
        """
        if use_cache_dir:
            if "file_list" not in self._output_params:
                self._output_params["file_list"] = list()
            self._output_params["file_list"].append(key)
            value = os.path.join(_service_manager.config['cache.root.dir'],
                                 _service_manager.config['cache.output_files.dir'], value)
        self._output_params[key] = value

    def update_result(self, result_dict):
        """
        更新任务结果
        :param result_dict:任务完成结果的字典
        :return:
        """
        if isinstance(result_dict,dict):
            self._output_params.update(result_dict)


    def __getitem__(self, item):
        """
        实现字典的索引方法
        :return:满足键为item的值
        """
        if item in self._input_params:
            return self._input_params[item]
        elif item in self._output_params:
            return self._output_params[item]

    def __setitem__(self, key, value):
        """
        实现字典赋值方法,字典针对outputparams进行赋值,inputparams为用户仅可读参数
        :param key:
        :param value:
        :return:
        """
        self._output_params[key] = value

    def __contains__(self, item):
        """
        实现包含操作,判断键item是否在inputparams或者outputparams里面
        :return:
        """
        if item in self._input_params or item in self._output_params:
            return True
        return False

    def as_dict(self):
        """
        返回输入参数和输出参数的字典，不隐藏其实现细节,用于写数据库
        """
        return self._input_params, self._output_params

    @property
    def input_params(self):
        """
        用于返回用户需要的参数,隐蔽其实现细节
        :return: 输入参数字典
        """
        tmp_params = copy.deepcopy(self._input_params)
        for key,value in tmp_params.items():
            if isinstance(value,list) and len(value) == 2:
                tmp_params[key] = value[0]
        return tmp_params

    @property
    def output_params(self):
        """
        用于返回用户需要的参数,隐蔽其实现细节
        :return: 输出参数字典
        """
        tmp_params = copy.deepcopy(self._output_params)
        if "file_list" in tmp_params:
            for file_key in tmp_params['file_list']:
                # 此处的file_path不是文件在容器中的路径，因flask的static_folder在url中根目录是cache.root.dir的basename，需要重新拼接
                file_url = os.path.join(os.path.basename(_service_manager.config['cache.root.dir']),
                                        _service_manager.config['cache.output_files.dir'],
                                        os.path.basename(tmp_params[file_key]))
                tmp_params[file_key] = file_url
            tmp_params.pop("file_list")
        return tmp_params




