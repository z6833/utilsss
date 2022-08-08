# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/21 11:55
# @File    : worker.py
# @Desc    : 实现子进程的逻辑，主要是回调，包含初始化工作、队列中取任务并执行

import traceback
import multiprocessing
from ..utils.log import logger


class Worker(multiprocessing.Process):
    """
    每个子进程执行给定的初始化操作后，监听任务队列
    """

    def __init__(self, task_queue, init_func, do_task_func, fail_func):
        super(Worker, self).__init__()
        # 任务队列，多个worker共同监听该任务队列，谁拿到谁消费
        self.task_queue = task_queue
        # 模型初始函数，由开发者自行定义
        self.init_func = init_func
        # 执行任务函数，由开发者自行定义后，在base_service类中进一步封装
        self.do_task_func = do_task_func
        # 任务失败函数，当捕获到do_task_func函数的异常后，会执行该函数
        self.fail_func = fail_func
        pass

    def run(self):
        """
        子进程启动时执行的代码，包含模型初始化及任务队列监听，获取任务id后，执行该任务
        """
        # 初始化工作，如加载模型
        self.init_func()
        while True:
            task_id = self.task_queue.get()
            logger.info('Process {} get task {}'.format(self.pid, task_id))
            try:
                # 执行任务
                self.do_task_func(task_id, self.pid)
                logger.info('Process {} complete task {}'.format(self.pid, task_id))
            except Exception as e:
                # 捕获do_task_func中的异常
                logger.error('Process {} task {} failed, error: {}'.format(self.pid, task_id, repr(e)))
                logger.error(traceback.format_exc())
                self.fail_func(task_id, repr(e))
        pass
