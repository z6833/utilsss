# -*- coding: utf-8 -*-
"""
@File: test2..py
@time: 2022/4/6 15:21
@Desc: 实现xxx
E-mail = yifan.jiang@southgis.com
"""
# import sys
# import pathlib
# cwd_path = pathlib.Path(__file__).absolute()
# parent_path = cwd_path.parent.parent.as_posix()
# print(parent_path)
# sys.path.append(parent_path)

import os
from ..tools import main


if __name__ == '__main__':
    input_shp = r'/code/luojiaset_data/test_data/cage_dataset_shp48/cage_dataset_shp48/cage_bbox_shp48.shp'

    input_tif = r'/code/luojiaset_data/test_data/cage_20201103_48_3band.tif'
    # input_tif_change = r'/code/luojiaset_data/test_data/change_detection_data/8月巡查影像_8_1869_post.tif'
    input_tif_change = None

    output_dir = r"/code/luojiaset_data/test_data/out_data_0406_09/"
    input_shp_buffer = None

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
    listFeature = None
    task = 1
    consumer_number = 4

    main(consumer_number=consumer_number, task=task, input_shp=input_shp, input_tif=input_tif,
         input_shp_buffer=input_shp_buffer,
         input_tif_change=input_tif_change, output_dir=output_dir, type_crop=type_crop, angle=angle,
         out_shape=out_shape, move=move, label=label, resolution=resolution, step=step,
         save_no_coord=save_no_coord, buffer_field=buffer_field, list_buffer_name=list_buffer_name,
         listFeature=listFeature, feature=feature, callback=None, image_num=None, init_percent=None)
