# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/30 9:15
# @File    : app_new.py
# @Desc    : 实现微服务发布


import os
from parsely.utils.log import logger
from parsely.service.argument import ReqArgument, ReqArgumentType#, OutputParams
from parsely.service.base_service import BaseService, StopService, GetTaskService, GetTasksService
from parsely.service.service_manager import _service_manager
from tools.ObjectDetection_new import ObjectDetection


class IllegalBuildingDetectionService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def task_type(self):
        """
        设置Service的任务类型，由子类重写该方法，该值会记录在数据库任务表中任务类型字段中
        """
        return "illegal_building_detection"

    def url(self):
        """
        设置Service的url，由子类重写该方法，该值会用于注册api接口，这样用户可以通过url访问该接口
        """
        return "/predict"

    def setup_models(self):
        """
        微服务启动前模型初始化工作，会开启子进程执行该函数。子类自行实现，需要确保模型仅在此函数中加载，而没有在主进程中加载，否则存在CUDA张量进程间通信问题。该方法不用子类调用
        """
        logger.info("illegal building detection model setup")
        # 定义投影坐标系
        prjWkt = 'PROJCS["CGCS2000_3_degree_Gauss_Kruger_CM_114E",GEOGCS["GCS_China_Geodetic_Coordinate_System_2000",DATUM["unknown",SPHEROID["Unknown",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",114],PARAMETER["scale_factor",1],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'

        # 实例化违建检测器
        detector = ObjectDetection(('__background__', 'unapprovedconstruction'), 'res101',
                                   'models/illegalbuilding/res101_faster_rcnn_iter_530000.ckpt')
        detector.setCropParamsByGeo(50, 50, 15, 15, prjWkt)
        self.detector = detector
        pass

    def params(self):
        """
        设置Service需要验证的参数列表，利用flask-restful自带的验证方法验证http请求参数。返回ReqArgument的list。需要子类自行实现
        """
        params_list = list()
        # 得分阈值，必填，float类型
        score_thresh = ReqArgument('scorethresh', ReqArgumentType.FLOAT, True, "scorethresh should be float!")
        # 输入影像服务器路径，必填，string类型
        input_image = ReqArgument('inputimage', ReqArgumentType.STRING, True, "inputimage cannot be blank!")
        # 输出shp服务器路径，必填，string类型
        output_shp = ReqArgument('outputshp', ReqArgumentType.STRING, True, "outputshp cannot be blank!")
        params_list.append(score_thresh)
        params_list.append(input_image)
        params_list.append(output_shp)
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
        score_thresh = params['scorethresh']
        if score_thresh >= 1.0 or score_thresh <= 0.0:
            return False, "scorethresh should between 0.0 and 1.0"
        input_image = params['inputimage']
        if not os.path.exists(input_image):
            return False, "inputimage {} Not Exists".format(input_image)
        output_shp = params['outputshp']
        output_shp_dirname = os.path.dirname(output_shp)
        # 如果shp目录不存在，则提示目录不存在
        if not os.path.exists(output_shp_dirname):
            return False, "Dir of outputshp {} Not Exists".format(output_shp)
        # 判断输出路径是否是shp文件，若不是，则提示
        ext = os.path.splitext(output_shp)[1]
        if ext != ".shp":
            return False, "Extention of outputshp {} Should Be .shp".format(output_shp)
        # 输入参数信息
        input_params = {'inputimage': input_image, 'scorethresh': score_thresh}
        # 构造输出参数对象
        output_params_obj = OutputParams()
        # 若输入文件为上传文件，则输出文件路径使用缓存输出目录
        # 若输入和输出都是指定的服务器路径，则不使用缓存目录
        output_params_obj.add_param("outputshp", output_shp, False)
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
        :return: 执行结果，返回格式二元组(is_success, data),若成功，则data为output_params；若失败，则data为errmsg字符串
        """
        logger.info("do task {}, input: {}, output: {}".format(task_id, input_params, output_params))
        score_thresh = input_params['scorethresh']
        input_image = input_params['inputimage']
        output_shp = output_params['outputshp']
        is_success, data = self.detector.predictImage(task_id, input_image, output_shp, score_thresh, self.processCb)
        if is_success:
            data = output_params
        return is_success, data

    # 每次预测完一张切片的回调函数，根据需求做相应处理
    def processCb(self, taskid, finishedCount, totalCount):
        #@print('Task {} FinishedCount: {} / {}'.format(taskid, finishedCount, totalCount))
        progress = round(float(finishedCount) / totalCount * 100)
        # 更新db中任务进度
        self.update_progress(taskid, progress)


if __name__ == "__main__":
    # 实例化开发者继承BaseService自定义的类
    ibd = IllegalBuildingDetectionService()
    # 调用__call__方法，传入子进程数，用于任务并行，子进程数最小为1
    ibd(_service_manager.config['service.illegal_building_detection.num_woker'])
    # 实例化框架预定义的停止任务service
    stop = StopService()
    # 实例化框架预定义的获取特定任务信息的service
    get_task = GetTaskService()
    # 实例化框架预定义的获取所有任务信息的service
    get_tasks = GetTasksService()
    # 注册各service到_service_manager中
    _service_manager.register_service(ibd)
    _service_manager.register_service(stop)
    _service_manager.register_service(get_task)
    _service_manager.register_service(get_tasks)
    # 启动微服务
    _service_manager.start()
    pass