# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/21 11:55
# @File    : task_scheduler.py
# @Desc    : 定义任务调度及worker并行相关逻辑

import time
import multiprocessing
from ..scheduler.worker import Worker
from ..utils.log import logger


class TaskScheduler:
    """
    任务调度器，在baseservice中进行实例化，作为其成员变量
    """

    def __init__(self, init_worker_func, do_task_func, fail_func, num_worker=4):
        """
        初始化任务调度器
        :param init_worker_func:
        :param finish_func:
        :param num_worker:
        """
        # worker开启时执行自定义初始化函数，如加载模型
        self.init_worker_func = init_worker_func
        # worker从任务队列中拿到任务时，执行相应的函数，如执行检测
        self.do_task_func = do_task_func
        # 任务失败的回调函数，捕获到异常时调用
        self.fail_func = fail_func
        # 可同时执行的任务数（子进程数），每个子进程一次执行一个任务
        self.num_worker = num_worker
        # 子进程字典，key为pid，value为worker对象
        self.workers = dict()
        # 支持进程间通信的的任务队列，各子进程从中取任务执行
        self.task_queue = multiprocessing.Queue()

    def start_workers(self):
        """
        启动指定数量的子进程，每个子进程执行给定的初始化工作后，监听任务队列
        """
        for w in range(self.num_worker):
            # 分开启动worker，间隔一定时间
            time.sleep(1)
            self.start_worker()

    def start_worker(self):
        """
        开启一个新的子进程
        """
        worker = Worker(self.task_queue, self.init_worker_func, self.do_task_func, self.fail_func)
        worker.start()
        self.workers.setdefault(worker.pid, worker)
        logger.info("new worker {} starts, worker count: {}".format(worker.pid, len(self.workers)))
        return worker

    def stop_worker(self, pid):
        """
        杀掉指定的子进程
        :param pid: 子进程id
        """
        worker = self.workers.get(pid)
        if worker is None:
            logger.warning("Worker {} not found".format(pid))
            return
        if worker.is_alive():
            worker.terminate()
            worker.join()
        self.workers.pop(pid)
        logger.info("worker {} is killed, worker count: {}".format(pid, len(self.workers)))

    def restart_worker(self, pid):
        """
        杀掉指定的子进程，并开启一个新的子进程
        :param pid: 子进程id
        """
        self.stop_worker(pid)
        self.start_worker()

    def monitor_works(self):
        """
        监控工作进程状态，如果工作进程为非活动状态，则结束进程，新启动一个work
        :return:
        """
        die_pid_list = list()
        for pid in self.workers:
            work = self.workers[pid]
            if work.is_alive() is False:
                die_pid_list.append(pid)
        for die_pid in die_pid_list:
            self.restart_worker(die_pid)

    def add_task(self, task_id):
        """
        向任务队列写入新任务的id
        :param task_id:
        """
        self.monitor_works()
        self.task_queue.put(task_id)
