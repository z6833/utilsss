# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/24 14:58
# @File    : service_manager.py
# @Desc    : 服务管理器，用于对不同service进行统一管理、注册

import sys
import os
from flask import Flask
from flask_restful import Api
import py_eureka_client.eureka_client as eureka_client
from ..utils.log import logger
from ..database import db_utils
from ..config import config_loader


class ServiceManager:
    # 已注册的service字典，key：任务类型，value：service对象
    service_map = dict()
    # 配置信息dict
    config = dict()

    def __init__(self):
        """
        构造app，初始化数据库
        """
        if len(sys.argv) != 2:
            logger.error("config_file_path should be passed as argument, service shut down!")
            sys.exit(1)
        config_path = sys.argv[1]
        # 读取本地配置文件，并记录配置信息
        self.read_config(config_path)
        # 获取主脚本所在目录
        main_dir, filename = os.path.split(os.path.abspath(sys.argv[0]))
        if not os.path.isabs(self.config['cache.root.dir']):
            self.config['cache.root.dir'] = os.path.join(main_dir, self.config['cache.root.dir'])
        # 创建缓存目录，存放输入和输出文件
        os.makedirs(os.path.join(self.config['cache.root.dir'], self.config['cache.input_files.dir']), exist_ok=True)
        os.makedirs(os.path.join(self.config['cache.root.dir'], self.config['cache.output_files.dir']), exist_ok=True)
        # 构造app，并设置缓存路径
        app = Flask(__name__, static_folder=self.config['cache.root.dir'])
        # 初始化数据库
        app = db_utils.registerDB(app, self.config)
        if not app:
            sys.exit(1)
        self.app = app
        self.api = Api(self.app)

    def read_config(self, config_path):
        """
        读取本地配置文件，并记录配置信息
        :param config_path: 本地配置文件路径
        """
        # 读取配置信息
        config_run_path = os.path.join(os.path.dirname(config_path), "run." + os.path.basename(config_path))
        local_config = config_loader.get_local_config(config_path)
        if local_config is None:
            logger.error("config file not found, server not start")
            sys.exit(1)
        # 如果是standalone模式，则不访问配置中心和注册中心
        is_standalone = local_config['is_standalone'] == "True"
        logger.info("Standalone Mode: {}".format(is_standalone))
        if is_standalone:
            self.config = local_config
        else:
            # 否则,就访问配置中心，获取相关配置
            update = config_loader.update_configs_with_remote(local_config, config_run_path)
            if update:
                config_run = config_loader.get_local_config(config_run_path)
                self.config = config_run
            else:
                self.config = local_config

    def register_service(self, service):
        """
        注册service，若service未重写tasktype方法，则仅注册api，不注册到service_map中
        :param service: service对象
        """
        self.api.add_resource(type(service), service.url())
        if service.task_type() is not None:
            self.service_map[service.task_type()] = service
        logger.info("Service {} registered".format(service.url()))

    def start_services(self):
        """
        开启服务，启动服务对应的子进程，初始化模型、监听任务队列
        :return:
        """
        for service in self.service_map.values():
            service.start()

    def add_task(self, service_type, task_id):
        """
        将任务id加入到对应类型service的任务队列中
        :param service_type: service类型
        :param task_id: 任务id
        """
        self.service_map[service_type].add_task(task_id)

    def stop_worker(self, service_type, pid):
        """
        杀掉指定的子进程，并开启新的worker
        :param service_type: service类型
        :param pid: 任务id
        :return:
        """
        self.service_map[service_type].stop_worker(pid)

    def start(self):
        """
        启动服务管理器
        """
        # 重置之前没有开始、或没有结束的任务，重新加入任务队列中
        self.reset_tasks()
        # 先销毁已有的engine，确保父进程没有数据库连接
        # 该操作解决多进程访问数据库Command out of sync、Lost Connection等问题
        self.app.db.get_engine(app=self.app).dispose()
        # 启动各service的子进程
        self.start_services()
        if not self.config['is_standalone'] == "True":
            # 注册到注册中心
            self.register_eureka()
        logger.info(
            "Web service runs, listening to container port: {}, request port: {}".format(self.config['container.port'],
                                                                                         self.config['server.port']))
        # 启动微服务，监听对应端口
        self.app.run(debug=False, host='0.0.0.0', port=self.config['container.port'])
        pass

    def reset_tasks(self):
        """
        将数据库中状态为等待中、进行中的任务，状态重置为等待中，并重置其它任务信息
        """
        with self.app.app_context():
            tasks = db_utils.reset_tasks()
            # 全部按顺序写入任务队列中
            if tasks is None or len(tasks) == 0:
                return
            for task in tasks:
                self.add_task(task.tasktype, task.id)
            logger.info("Restart Previous Unfinished {} Tasks".format(len(tasks)))

    def register_eureka(self):
        """
        将本微服务注册到eureka注册中心
        """
        # 注册中心url列表
        eureka_server_url_list = eval(self.config['eureka.url'])
        # 微服务注册到注册中心的app_name
        app_name = self.config['app_id']
        # 微服务所在主机ip
        server_host = self.config['server.host']
        # 微服务端口号
        server_port = int(self.config['server.port'])
        for index, eureka_server_url in enumerate(eureka_server_url_list):
            # http://172.20.20.1:8080/eureka
            # eureka_server_url = 'http://172.20.20.%s:8080/eureka' % str(eureka_server_url)
            # py_eureka_client版本号为0.10.0
            eureka_client.init(eureka_server=eureka_server_url,
                               app_name=app_name,
                               # 当前组件的主机名，可选参数，如果不填写会自动计算一个，
                               # 如果服务和 eureka 服务器部署在同一台机器，请必须填写，>否则会计算出 127.0.0.1
                               instance_host=server_host,
                               instance_port=server_port,
                               # instance_ip=server_host,
                               # instance_id="{}:{}".format(server_host, server_port),
                               # 调用其他服务时的高可用策略，可选，默认为随机
                               # ha_strategy=eureka_client.HA_STRATEGY_RANDOM
                               )
        logger.info("Registered to eureka")


_service_manager = ServiceManager()
