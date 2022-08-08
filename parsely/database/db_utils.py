# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/21 11:24
# @File    : db_utils.py
# @Desc    : 数据库操作相关方法

import os
import datetime
from sqlalchemy import or_
from ..database.db_model import Task, DataTable, db
from ..utils.log import logger


def get_task(task_id):
    """
    根据任务号获取任务记录
    :param task_id: 任务号
    :return: 任务记录
    """
    task = Task.query.filter_by(id=int(task_id)).first()
    return task


def get_all_tasks(page_num, page_size):
    """
    获取所有任务列表，按任务号升序
    :param page_num: 第几页
    :param page_size: 页大小
    :return: 任务列表
    """
    return Task.query.order_by(Task.id.desc()).paginate(page=page_num, per_page=page_size, error_out=False)


def get_tasks_by_status(status, page_num, page_size):
    """
    根据任务状态获取任务列表，按任务号升序
    :param status: 任务状态
    :param page_num: 第几页
    :param page_size: 页大小
    :return: 任务列表
    """
    return Task.query.filter_by(status=status).order_by(Task.id.desc()).paginate(page=page_num,
                                                                                 per_page=page_size,
                                                                                 error_out=False)


def create_task(task_type, input_params, output_params):
    """
    创建一条任务记录
    :param task_type:任务类型，即service_type
    :param input_params: 任务的输入参数，即客户端传过来的inputparams参数stringify后的字符串
    :param output_params: 任务的输出参数，即客户端传过来的outputparams参数stringify后的字符串
    :return: 新建的任务记录
    """
    new_task = Task(tasktype=task_type, inputparams=input_params, outputparams=output_params,
                    status=0, progress=0, createtime=datetime.datetime.now())
    new_task.save_to_db()
    return new_task


def reset_tasks():
    """
    等待和进行中的任务，状态重置为等待中
    """
    tasksQuery = Task.query.filter(or_(Task.status == 3, Task.status == 0))
    tasks = tasksQuery.order_by(Task.id.asc()).all()
    # 没有等待中的任务，直接返回
    if tasks is None or len(tasks) == 0:
        return None
    tasksQuery.update(
        {Task.status: 0, Task.progress: 0, Task.createtime: datetime.datetime.now()})
    db.session.commit()
    return tasks


def gen_databse_uri(conf):
    """
    构造数据库连接字符串
    :param conf: 配置信息
    :return: 数据库连接字符串
    """
    dialect = conf['database.dialect']
    if dialect == "mysql":
        driver = conf['database.driver']
        username = conf['database.username']
        password = conf['database.password']
        host = conf['database.host']
        port = conf['database.port']
        database = conf['database.dbname']
        sqlalchemy_database_uri = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(dialect,
                                                                               driver,
                                                                               username,
                                                                               password,
                                                                               host,
                                                                               port,
                                                                               database)
    elif dialect == "sqlite":
        # 创建存放数据库文件的文件夹
        SQLiteDir = os.path.join("/SQLiteData", "database")
        if not os.path.exists(SQLiteDir):
            os.makedirs(SQLiteDir)
        db_file = os.path.join(SQLiteDir, "tasks.db")

        sqlalchemy_database_uri = 'sqlite:///' + db_file + '?check_same_thread=False'
    else:
        raise ValueError("{}类型不支持。".formae(dialect))

    return sqlalchemy_database_uri


def update_task_table_name(config):
    """
    更新任务表的表明
    :param config:
    """
    Task.__table__.name = "{}.task".format(config['app_id'])


def create_data_table(table_name):
    """
    创建一条数据目录表的记录
    :param table_name: 表名
    :return: 新建的数据目录表记录
    """
    new_dt = DataTable(parent_fid=-1, name=table_name, creator_id='ai_gis', create_time=datetime.datetime.now(),
                       updator_id='ai_gis', update_time=datetime.datetime.now(), data_type='矢量数据表', state=1,
                       geo_type='面数据')
    new_dt.save_to_db()
    return new_dt


def registerDB(app, config):
    """
    注册数据库：实现数据库连接，创建数据表
    :param app: flask app
    :return: flask app
    """
    try:
        # 数据库文件路径
        app.config['SQLALCHEMY_DATABASE_URI'] = gen_databse_uri(config)

        # 更新任务表名
        update_task_table_name(config)
        db.init_app(app=app)
        app.db = db
        resetDB(app)
        return app
    except Exception as e:
        logger.error("Init DB Error: {}".format(repr(e)))
        return None


def resetDB(app):
    """
    初始化数据库
    :param app:
    """
    # db.drop_all(app=app)
    # 如果没有任务表，就会创建
    db.create_all(app=app)
