# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/30 9:15
# @File    : app_new.py
# @Desc    : 实现微服务发布


import os
from parsely.utils.log import logger
from parsely.service.argument import ReqArgument, ReqArgumentType#, OutputParams
from parsely.service.base_service import BaseService, GetTaskService, GetTasksService, DownloadService
from parsely.service.service_manager import _service_manager
from floater_detection import FloaterDetection


class FloaterDetectionService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def task_type(self):
        """
        设置Service的任务类型，由子类重写该方法，该值会记录在数据库任务表中任务类型字段中
        """
        return "floater_detection"

    def url(self):
        """
        设置Service的url，由子类重写该方法，该值会用于注册api接口，这样用户可以通过url访问该接口
        """
        return "/predict"

    def setup_models(self):
        """
        微服务启动前模型初始化工作，会开启子进程执行该函数。子类自行实现，需要确保模型仅在此函数中加载，而没有在主进程中加载，否则存在CUDA张量进程间通信问题。该方法不用子类调用
        """
        logger.info("floater detection model setup")
        # 实例化漂浮物检测器
        detector = FloaterDetection('model/weights.24-0.10.hdf5')
        self.detector = detector
        pass

    def params(self):
        """
        设置Service需要验证的参数列表，利用flask-restful自带的验证方法验证http请求参数。返回ReqArgument的list。需要子类自行实现
        """
        params_list = list()
        input_file = ReqArgument('inputfile', ReqArgumentType.FILE, True, "inputfile should upload jpg/jpeg/png file!",
                                 ['jpg', 'jpeg', 'png'])
        params_list.append(input_file)
        return params_list

    def check_params(self, params):
        """
        对用户发送的请求进行参数校验，子类自行实现校验方法，并返回校验结果，验证通过后，input_params和output_params会写入数据库task记录中。该方法不用子类调用
        该方法返回值中的input_params和output_params将作为参数传入do_task方法中，用于模型的预测。故需要开发者在这两个参数中记录do_task需要用到的信息，
        如输入路径、概率阈值放入input_params中，输出路径、输出文件名放入output_params中
        :param params: 用户请求参数dict
        :return: 校验结果，返回格式二元组(is_success, data),若成功，则data为(input_params, output_params)；若失败，则data为errmsg字符串
        """
        logger.info('check_params: {}'.format(params))
        if 'inputfile' not in params:
            return False, "inputfile should not be null"
        inputfile = params['inputfile']
        if not os.path.exists(inputfile):
            return False, "inputfile {} Not Exists".format(inputfile)
        # 输出结果文件名与输入文件名一样
        output_filename = os.path.basename(inputfile)
        # 输入参数信息
        input_params = {'inputfile': inputfile}
        # 构造输出参数对象
        output_params_obj = OutputParams()
        # 此处输出结果文件存放到缓存输出目录下
        output_params_obj.add_param("outputfile", output_filename, True)
        return True, (input_params, output_params_obj.as_dict())

    def do_task(self, task_id, input_params, output_params):
        """
        模型预测的函数，接收从数据库task记录中获取的input_params和output_params，子类自行实现调用模型预测相关脚本，并返回执行结果。该方法不用子类调用
        该方法返回值中的output_params将被用于更新数据库对应task记录中outputparams字段的内容。
        开发者可根据需要，修改返回体中output_params中的内容，如记录预测结果bbox数量、分类类别等信息，这样调用download接口时，即可查看对应预测结果信息
        e.g. output_params['count'] = 9
        若无需修改，则保持output_params不变返回
        :param task_id: 任务id
        :param input_params: 输入dict
        :param output_params: 输出dict
        :return: 执行结果，返回格式二元组(is_success, data),若成功，则data返回output_params；若失败，则data为errmsg字符串
        """
        logger.info("do task {}, input: {}, output: {}".format(task_id, input_params, output_params))
        input_image = input_params['inputfile']
        output_image = output_params['outputfile']
        # 调用模型预测的方法，并返回预测结果，如bbox预测数量
        is_success, data = self.detector.predict(input_image, output_image)
        if is_success:
            # 记录bbox预测数量到output_params中，后面会更新数据库对应task的output_params字段
            output_params['count'] = data
            data = output_params
        return is_success, data


if __name__ == "__main__":
    # 实例化开发者继承BaseService自定义的类
    service = FloaterDetectionService()
    # 调用__call__方法，传入子进程数，用于任务并行，子进程数最小为1
    service(_service_manager.config['service.floater_detection.num_woker'])
    # 实例化框架预定义的获取特定任务信息的service
    get_task = GetTaskService()
    # 实例化框架预定义的获取所有任务信息的service
    get_tasks = GetTasksService()
    # 实例化框架预定义的下载任务结果的service
    download = DownloadService()
    # 注册各service到_service_manager中
    _service_manager.register_service(service)
    _service_manager.register_service(get_task)
    _service_manager.register_service(get_tasks)
    _service_manager.register_service(download)
    # 启动微服务
    _service_manager.start()
    pass
