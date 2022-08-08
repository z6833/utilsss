# -*- coding:utf-8 -*-
# @FileName  :configs.py
# @Time      :2022/5/24 17:09
# @Author    :zhaolun
from utils.constants import cropped_dir

# todo 数据裁剪集成进来


class SampleMakeConfig:
    task = 1,
    input_shp = None,
    input_tif = None,
    input_shp_buffer = None,
    input_tif_change = None,
    listFeature = None,
    step = (2000, 2000),
    angle = False,
    type_crop = True,
    out_shape = (2000, 2000),  # outputShape 为输出数据的通道和像素尺寸
    move = False,  # 随机偏移量，不需偏移请设置为False [-50, -100, -150, 50, 100, 150]随机偏移，可在上方修改
    label = None,  # 生成json的用的label，单分类设置为None
    output_dir = cropped_dir,
    save_no_coord = None,
    resolution = None,  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
    buffer_field = None,
    list_buffer_name = None,
    callback = None,
    image_num = None,
    init_percent = None,
    feature = None
