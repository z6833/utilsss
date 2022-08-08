# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/25 10:23
# @File    : db_model.py
# @Desc    : 定义通用的任务信息表结构

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    """
    预测任务的Model，各应用继承该类并重写表名
    """
    # 任务号
    id = db.Column(db.Integer, primary_key=True)
    # 所用资源信息，{ip: XXX.XXX.XXX.XXX, pid: XXXX}，json经stringify后存入
    resource = db.Column(db.String(200))
    # 任务类型，与服务注册时的app_name保持一致
    tasktype = db.Column(db.String(200))
    # 任务的输入参数kvps，key自定义，json经stringify后存入
    inputparams = db.Column(db.String(1000))
    # 任务的输出参数kvps，key自定义，格式同上
    outputparams = db.Column(db.String(1000))
    # 任务信息，存储任务错误或成果信息
    content = db.Column(db.String(500))
    # 任务执行进展，值域：[0, 100]
    progress = db.Column(db.Integer)
    # 任务状态：0 等待中，1 执行成功，2 执行失败，3 执行中，4 待入队
    status = db.Column(db.Integer)
    # 任务创建时间
    createtime = db.Column(db.DateTime)
    # 任务开始时间
    starttime = db.Column(db.DateTime)
    # 任务结束时间
    finishtime = db.Column(db.DateTime)

    # 因datetime格式不支持json序列化，故格式化datetime字段，以返回给客户端

    def format_datetime(self):
        if self.createtime is not None:
            self.createtime = self.createtime.strftime('%Y-%m-%d %H:%M:%S')
        if self.starttime is not None:
            self.starttime = self.starttime.strftime('%Y-%m-%d %H:%M:%S')
        if self.finishtime is not None:
            self.finishtime = self.finishtime.strftime('%Y-%m-%d %H:%M:%S')
        return self

    # 属性转dict，用于构造json返回给客户端
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    # 保存到数据库
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()


class DataTable(db.Model):
    """
    数据库基本信息表
    """
    __tablename__ = "m_table"
    id = db.Column(db.Integer, primary_key=True)
    parent_fid = db.Column(db.Integer)
    name = db.Column(db.String(255))
    tags = db.Column(db.String(255))
    creator_id = db.Column(db.String(255))
    updator_id = db.Column(db.String(255))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    description = db.Column(db.String(4000))
    data_type = db.Column(db.String(255))
    storage_type = db.Column(db.String(255))
    state = db.Column(db.Integer)
    geo_type = db.Column(db.String(255))

    # 保存到数据库
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
