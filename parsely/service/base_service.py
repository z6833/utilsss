# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/21 11:24
# @File    : base_service.py
# @Desc    : 定义baseservice基础接口

import os
import sys
import datetime
import json
import time
import traceback
from flask_restful import reqparse, Resource

from parsely.utils.notify_url import NotifyUrl
from ..utils.log import logger
from ..service.argument import ReqArgumentType, ReqArgument, Params
from ..scheduler.task_scheduler import TaskScheduler
from ..database import db_utils as db
from ..utils.errno import ErrNo, PARAM_ERROR
from ..utils.result import Result
from ..service.service_manager import _service_manager


class BaseService(Resource):
    def __init__(self, *args, **kwargs):
        """
        为避免覆盖Resource的构造函数，不做任何处理
        :param args:
        :param kwargs:
        """
        self.last_time = time.time()
        super().__init__(*args, **kwargs)

    def __call__(self, num_worker):
        """
        实例化任务调度器，构建任务队列，子类若无需任务调度器，则不调用该方法
        :param num_worker:
        :return:
        """
        if int(num_worker) < 1:
            logger.error("num worker should be larger than zero, service shut down!")
            sys.exit(1)
        self.task_scheduler = TaskScheduler(self.setup_models, self.do_task_cb, self.task_fail_cb,
                                            num_worker=int(num_worker))

    def url(self):
        """
        设置Service的url，由子类重写该方法，该值会用于注册api接口，这样用户可以通过url访问该接口
        """
        raise NotImplemented

    def task_type(self):
        """
        设置Service的任务类型，由子类重写该方法，该值会记录在数据库任务表中任务类型字段中
        """
        return None

    def params(self):
        """
        设置Service需要验证的参数列表，利用flask-restful自带的验证方法验证http请求参数。返回ReqArgument的list。需要子类自行实现
        """
        return list()

    def setup_models(self):
        """
        微服务启动前模型初始化工作，会开启子进程执行该函数。子类自行实现，需要确保模型仅在此函数中加载，而没有在主进程中加载，否则存在CUDA张量进程间通信问题。该方法不用子类调用
        """
        pass

    def check_params(self, params):
        """
        对用户发送的请求进行参数校验，子类自行实现校验方法，并返回校验结果，验证通过后，input_params和output_params会写入数据库task记录中。该方法不用子类调用
        该方法返回值中的input_params和output_params将作为参数传入do_task方法中，用于模型的预测。故需要开发者在这两个参数中记录do_task需要用到的信息，
        如输入路径、概率阈值放入input_params中，输出路径、输出文件名放入output_params中
        :param params: 用户请求参数dict
        :return: 校验结果，返回格式二元组(is_success, data),若成功，则data为空字符串；若失败，则data为errmsg字符串
        """
        return False, ''
        pass

    def do_task(self, task_id, params):
        """
        模型预测的函数，接收从数据库task记录中获取的input_params和output_params，子类自行实现调用模型预测相关脚本，并返回执行结果。该方法不用子类调用
        该方法返回值中的output_params将被用于更新数据库对应task记录中outputparams字段的内容。
        开发者可根据需要，修改返回体中output_params中的内容，如记录预测结果bbox数量、分类类别等信息，这样调用download接口时，即可查看对应预测结果信息
        e.g. output_params['count'] = 9
        若无需修改，则保持output_params不变返回
        :param task_id: 任务id
        :param params: 接口参数,包含输入和输出使用的参数
        :return: 执行结果，返回格式二元组(is_success, data),若成功，则data为""；若失败，则data为errmsg字符串
        """
        return False, ''

    def update_progress(self, task_id, progress):
        """
        更新任务进度条的方法，开发者在任务进度条更新时调用，不用重写该方法
        :param task_id:
        :param progress:
        """
        # 进度需要是整数
        # 判断进度更新的时间,如果两次时间间隔()太近,则不进行状态更新
        MIN_INTERVAL = 0.5
        now_time = time.time()
        interval_time = now_time - self.last_time
        if interval_time < MIN_INTERVAL:
            return
        self.last_time = now_time
        with _service_manager.app.app_context():
            if not isinstance(progress, int):
                logger.warning("Task {} Progress is not integer".format(task_id))
                return
            if progress > 100 or progress < 0:
                logger.warning("Task {} Progress should between 0 and 100".format(task_id))
                return
            task = db.get_task(task_id)
            # 更新任务进度
            if task is not None and task.status == 3:
                task.progress = progress
                task.save_to_db()

    # 提交预测任务，任务创建后，会返回任务号给客户端，客户端利用该任务号查询任务进度及其它信息
    def post(self):
        # 参数解析，增加参数验证
        # 此处要求输入和输出参数都不为空
        try:
            params = Params()
            params.add_reqArguments(self.params())
            # 此处进行参数验证，具体逻辑由开发者自行实现
            valid, data = self.check_params(params)
            # 验证失败，返回错误信息给客户端
            if not valid:
                errmsg = data
                return Result(ErrNo.PARAM_ERROR, errmsg).as_dict()
            input_params_json, output_params_json = params.dumps()
            # 生成新的任务，任务信息存入db中
            with _service_manager.app.app_context():
                new_task = db.create_task(self.task_type(),
                                          input_params_json,
                                          output_params_json)
                taskid = new_task.id
                # 将该任务id写入task队列中，消费者取出后执行任务
                # 因此处无法获得service对象，故利用全局变量_service_manager间接访问对应任务类型的service
                _service_manager.add_task(self.task_type(), taskid)
                logger.info("New Task {} Submitted, Tasktype: {}".format(taskid, self.task_type()))
                return Result(ErrNo.SUCCESS, '', {'taskid': taskid}).as_dict()
        except PARAM_ERROR as e:
            errmsg = str(e)
            logger.error(errmsg)
            logger.error(traceback.format_exc())
            return Result(ErrNo.PARAM_ERROR, errmsg).as_dict()
        except Exception as e:
            errmsg = 'check_param failed: {}'.format(repr(e))
            logger.error(errmsg)
            logger.error(traceback.format_exc())
            return Result(ErrNo.PARAM_ERROR, errmsg).as_dict()

    def do_task_cb(self, task_id, pid):
        """
        从TaskScheduler中执行任务的回调函数，开发者不用调用和实现
        :param task_id: 任务号
        :param pid: 执行该任务的子进程id
        :return:
        """
        # 更新任务状态为进行中，并记录子进程id、任务开始时间到db
        with _service_manager.app.app_context():
            task = db.get_task(task_id)
            if task is None:
                return
            # 任务状态不是等待中，可能是提前终止了，直接返回
            if task.status != 0:
                return
            task.status = 3
            # 记录子进程id
            task.resource = json.dumps({"pid": pid})
            task.starttime = datetime.datetime.now()
            task.save_to_db()
            # 解析json字符串为dict
            params = Params.loads(task.inputparams, task.outputparams)
            # 真正执行任务
            is_success, data = self.do_task(task_id, params)
            # 更新任务状态
            task = db.get_task(task_id)
            if task is not None and task.status == 3:
                if is_success:
                    # kudu表写入数据目录表
                    if 'table_name' in params:
                        db.create_data_table(params['table_name'])
                    task.status = 1
                    task.progress = 100
                    task.content = "Task {} Completed!".format(task_id)
                    task.outputparams = params.dumps()[1]
                    # json.dumps(data, ensure_ascii=False)
                else:
                    task.status = 2
                    task.content = "Task {} Failed! ErrMsg: {}".format(task_id, data)
                task.finishtime = datetime.datetime.now()
                self.send_notify_url(params,task)
                task.save_to_db()

    def send_notify_url(self,params,task):
        url = params["notify_url"]
        if url:
            ret_dict = dict()
            ret_dict["id"] = task.id
            ret_dict["tasktype"] = task.tasktype
            ret_dict["status"] = task.status
            ret_dict["createtime"] = str(task.createtime)
            ret_dict["starttime"] = str(task.starttime)
            ret_dict["finishtime"] = str(task.finishtime)
            ret_dict["inputparams"] = params.input_params
            ret_dict["outputparams"] = params.output_params
            # data_json = json.dumps(ret_dict, ensure_ascii=False)
            NotifyUrl(url, ret_dict)

    def task_fail_cb(self, task_id, err_msg):
        """
        任务失败时的回调函数，为防止开发者未做异常处理。捕获到异常时调用，开发者不用调用和实现
        :param task_id: 任务id
        :param err_msg: 异常信息
        :return:
        """
        # 更新任务状态及记录异常信息
        with _service_manager.app.app_context():
            task = db.get_task(task_id)
            if task is not None and task.status == 3:
                params = Params.loads(task.inputparams, task.outputparams)
                task.status = 2
                task.content = "Task {} Failed! ErrMsg: {}".format(task_id, err_msg)
                task.finishtime = datetime.datetime.now()
                task.save_to_db()
                self.send_notify_url(params,task)

            pass

    def start(self):
        """
        启动该service下的子进程
        """
        self.task_scheduler.start_workers()

    def add_task(self, task_id):
        """
        将对应任务id写入task队列中
        :param task_id:
        :return:
        """

        self.task_scheduler.add_task(task_id)

    def stop_worker(self, pid):
        """
        杀掉指定的子进程，并开启新的worker
        :param pid: 子进程id
        """
        self.task_scheduler.restart_worker(pid)


class StopService(BaseService):
    """
    通过任务号终止相应任务
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start(self):
        pass

    def url(self):
        return "/stop"

    def post(self):
        # 参数解析，增加参数验证
        parser = reqparse.RequestParser()
        parser.add_argument('taskid', type=int, required=True, help="taskid cannot be blank!")
        args = parser.parse_args()
        taskid = int(args['taskid'])
        with _service_manager.app.app_context():
            task = db.get_task(taskid)
            if task is None:
                return Result(ErrNo.TASK_ERROR, 'Task {} Not Found'.format(taskid)).as_dict()
            # 已成功或失败的任务无法终止
            if task.status == 1 or task.status == 2:
                return Result(ErrNo.TASK_ERROR, 'Task {} Already Stopped'.format(taskid)).as_dict()
            # 等待中的任务，直接修改status
            if task.status == 0:
                task.status = 2
                task.content = "Stopped Before Start"
                task.finishtime = datetime.datetime.now()
                task.save_to_db()
                logger.info("Task {} {}".format(taskid, task.content))
                return Result(ErrNo.SUCCESS, '').as_dict()
            resource = json.loads(task.resource)
            if resource is None:
                # 此处不应进入
                logger.warning("Task {} not start".format(taskid))
                return
            # 如果是正在执行，则通过ServiceManager通知对应service停止对应任务所在的子进程，并重启，以终止任务
            _service_manager.stop_worker(task.tasktype, int(resource['pid']))
            task.status = 2
            task.content = "Stopped During Running"
            task.finishtime = datetime.datetime.now()
            task.save_to_db()
            return Result(ErrNo.SUCCESS, '').as_dict()

    def get(self):
        pass


class GetTaskService(BaseService):
    """
    通过任务号获取预测任务的信息
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def url(self):
        return "/task/<taskid>"

    def start(self):
        pass

    def get(self, taskid):
        if not taskid.isdigit():
            return Result(ErrNo.PARAM_ERROR, 'taskid should be integer').as_dict()
        with _service_manager.app.app_context():
            task = db.get_task(taskid)
            if task is None:
                return Result(ErrNo.TASK_ERROR, 'Task {} Not Found'.format(taskid)).as_dict()
            return Result(ErrNo.SUCCESS, '', task.format_datetime().as_dict()).as_dict()

    def post(self):
        pass


class GetTasksService(BaseService):
    """
    获取满足查询条件的任务信息，最新在最前
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def url(self):
        return "/tasks"

    def start(self):
        pass

    def get(self):
        # 参数解析，增加参数验证
        parser = reqparse.RequestParser()
        # 页码编号，从1开始
        parser.add_argument('pagenum', type=int, required=True, location="args", help="pagenum cannot be blank!")
        # 每页项目数，默认10个
        parser.add_argument('pagesize', type=int, required=False, location="args", default=10,
                            help="pagesize should be integer!")
        # 任务状态，默认-1，返回所有任务
        parser.add_argument('status', type=int, required=False, location="args", default=-1,
                            help="status should be integer!")
        args = parser.parse_args()
        pagenum = int(args['pagenum'])
        pagesize = int(args['pagesize'])
        status = int(args['status'])
        if pagenum <= 0:
            return Result(ErrNo.PARAM_ERROR, 'pagenum should be positive number').as_dict()
        if pagesize <= 0:
            return Result(ErrNo.PARAM_ERROR, 'pagesize should be positive number').as_dict()
        with _service_manager.app.app_context():
            if status == -1:
                pageInfo = db.get_all_tasks(pagenum, pagesize)
            else:
                pageInfo = db.get_tasks_by_status(status, pagenum, pagesize)
            tasks = pageInfo.items
            if tasks is None or len(tasks) == 0:
                return Result(ErrNo.TASK_ERROR, 'Tasks Not Found').as_dict()

            tasksArr = []
            for task in tasks:
                tasksArr.append(task.format_datetime().as_dict())
            curpage = pageInfo.page
            pages = pageInfo.pages
            total = pageInfo.total
            pagesize = pageInfo.per_page
            data = {'list': tasksArr, 'curpage': curpage, 'pages': pages, 'pagesize': pagesize, 'total': total}
            return Result(ErrNo.SUCCESS, '', data).as_dict()

    def post(self):
        pass


class DownloadService(BaseService):
    """
    下载对应任务的预测结果
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def url(self):
        return "/download/<taskid>"

    def start(self):
        pass

    def get(self, taskid):
        if not taskid.isdigit():
            return Result(ErrNo.PARAM_ERROR, 'taskid should be integer').as_dict()
        with _service_manager.app.app_context():
            task = db.get_task(taskid)
            if task is None:
                return Result(ErrNo.TASK_ERROR, 'Task {} Not Found'.format(taskid)).as_dict()
            output_params = json.loads(task.outputparams)
            if 'file_list' in output_params:
                file_keys = output_params['file_list']
                for file_key in file_keys:
                    # 此处的file_path不是文件在容器中的路径，因flask的static_folder在url中根目录是cache.root.dir的basename，需要重新拼接
                    file_url = os.path.join(os.path.basename(_service_manager.config['cache.root.dir']),
                                            _service_manager.config['cache.output_files.dir'],
                                            os.path.basename(output_params[file_key]))
                    output_params[file_key] = file_url
                output_params.pop('file_list')
            return Result(ErrNo.SUCCESS, '', output_params).as_dict()

    def post(self):
        pass
