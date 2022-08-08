# -*- coding: utf-8 -*-
"""
@File: single_process_entrance.py.py
@time: 2022/3/30 15:21
@Desc: 实现xxx
E-mail = yifan.jiang@southgis.com
"""
import sys
import pathlib

# cwd_path = pathlib.Path(__file__).absolute()
# parent_path = cwd_path.parent.parent.as_posix()
# print(parent_path)
# sys.path.append(parent_path)

import os
from ..sample_makes import ChangeDetectionSampleMake
from ..sample_makes import SegmentationSampleMake
from ..sample_makes import TargetDetectionSampleMake


class SampleMake:
    def __init__(self, task=None, input_shp=None, input_tif=None, input_shp_buffer=None, input_tif_change=None,
                 output_dir=None, type_crop=None, angle=None, out_shape=None, move=None,
                 label=None, resolution=None, step=None, save_no_coord=None, buffer_field=None,
                 list_buffer_name=None, listFeature=None, feature=None,
                 callback=None, image_num=None, init_percent=None):
        """
                影像切片的基础类
                :param task: 任务类型（1.目标检测 2.语义分割 3.变化检测）
                :param input_shp: 输入的shp矢量路径
                :param input_tif: 输入的栅格影像路径
                :param input_shp_buffer: 输入过滤矢量路径
                :param input_tif_change: 输入变化检测后影像路径
                :param output_dir: 输出的文件夹路径
                :param type_crop: 样本裁剪类型(True:滑窗裁剪，False:图斑裁剪)
                :param angle: 旋转数据增强(True:是，False:否)
                :param out_shape: 输出图像像素尺寸，width和length，如（512，512）
                :param move: 抖动数据增强(True:是，False:否)
                :param label: 标签
                :param resolution: 分辨率
                :param step: 滑窗裁剪步长，length和width，如（512，512）
                :param save_no_coord: 无坐标系保存(True:是，False:否)
                :param buffer_field: 精准过滤字段（默认None)
                :param list_buffer_name: 精准过滤列表（默认None)
                :param listFeature: 多分类属性字典，1，2，3为对应类别的mask rgb值， 二分类设置为None
                :param feature: 多分类属性字段，二分类设置为None
                :param callback: 进度条
                :param image_num: 单个切片任务所所包含样本总数
                :param init_percent: 当前样本所占用进度值（如共5个样本，当前样本是第2个，则init_percent为20%）
        """
        self.task = task
        self.input_shp = input_shp
        self.input_tif = input_tif
        self.input_shp_buffer = input_shp_buffer
        self.input_tif_change = input_tif_change
        self.output_dir = output_dir
        self.type_crop = type_crop
        self.angle = angle
        self.out_shape = out_shape
        self.move = move
        self.label = label
        self.resolution = resolution
        self.step = step
        self.save_no_coord = save_no_coord
        self.buffer_field = buffer_field
        self.list_buffer_name = list_buffer_name
        self.listFeature = listFeature
        self.feature = feature
        self.callback = callback
        self.image_num = image_num
        self.init_percent = init_percent

    def sample_make(self):
        # 任务类型对应类关系
        type_map = {
            "1": TargetDetectionSampleMake,
            "2": SegmentationSampleMake,
            "3": ChangeDetectionSampleMake
        }
        obj = type_map[str(self.task)](
            task=self.task, input_shp=self.input_shp, input_tif=self.input_tif,
            input_shp_buffer=self.input_shp_buffer, input_tif_change=self.input_tif_change,
            output_dir=self.output_dir, type_crop=self.type_crop, angle=self.angle,
            out_shape=self.out_shape, move=self.move, label=self.label,
            resolution=self.resolution, step=self.step, save_no_coord=self.save_no_coord,
            buffer_field=self.buffer_field, list_buffer_name=self.list_buffer_name,
            listFeature=self.listFeature, feature=self.feature,
            callback=self.callback, image_num=self.image_num, init_percent=self.init_percent)
        obj()


if __name__ == '__main__':

    input_shp_path = r'/mnt/data/archive/建筑物提取数据/2021_building_rs/数据部/sd真值标签/tdfg_building.shp'

    input_tif_path = r'/mnt/data/archive/建筑物提取数据/2021_building_rs/数据部/sd-3-1-05/img_05.tif'
    # input_tif_change = r'/code/luojiaset_data/test_data/change_detection_data/8月巡查影像_8_1869_post.tif'
    input_tif_change = None

    output_dir = r"/code/luojiaset_data/test_data/out_data_0413/"
    input_shp_buffer_path = None

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    out_shape = (256, 256)  # outputShape 为输出数据的通道和像素尺寸
    step = (256, 256)  # 滑窗裁剪步长，设置为outputShape大小时为无重叠裁剪
    move = False  # 随机偏移量，不需偏移请设置为False [-50, -100, -150, 50, 100, 150]随机偏移，可在上方修改
    angle = False  # angle=False 为不旋转，为True时[10,90]度逆时针随机裁剪
    label = None  # 生成json的用的label，单分类设置为None
    # label = ['水田', '水浇地', '旱地']  # 多分类生成json的用的label，单分类设置为None
    resolution = None  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
    type_crop = True  # slideWin=False 为图斑裁剪，设置为True为滑窗裁剪
    save_no_coord = False
    buffer_field = None
    list_buffer_name = None
    # feature = 'DLMC'
    # 多分类属性字段
    feature = None
    task = 1

    sample_m = SampleMake(task=task, input_shp=input_shp_path, input_tif=input_tif_path, input_tif_change=input_tif_change,
                          input_shp_buffer=input_shp_buffer_path, step=step, angle=angle, type_crop=type_crop,
                          out_shape=out_shape, move=move, label=label, output_dir=output_dir,
                          save_no_coord=save_no_coord, resolution=resolution,
                          buffer_field=buffer_field, list_buffer_name=list_buffer_name,
                          feature=feature)
    sample_m.sample_make()

