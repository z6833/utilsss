# -*- coding:utf-8 -*-
# @FileName  :constants.py
# @Time      :2022/5/24 17:14
# @Author    :zhaolun
from pathlib import Path
import os
from multiprocessing import cpu_count

# 项目根目录
root_dir = Path.cwd().parent.parent.as_posix()

# 裁剪结果保存目录
cropped_dir = os.path.join('/data_02', '不同任务训练测试数据', '数据分布网格切片数据', '陆良3')

# 服务器cores
cores = cpu_count()

# 随机种子
random_state = 1024
