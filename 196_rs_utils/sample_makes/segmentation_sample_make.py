#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/3/31 10:12
# @File    : target_detection_sample_make.py
# @Desc    : 语义分割切片
import os
# from ..sample_makes.data_save import DataSave
from .sample_make_bace import SampleMakeBase
import numpy as np
import datetime


class SegmentationSampleMake(SampleMakeBase):
    def __init__(self, task, input_shp, input_tif, input_shp_buffer,input_tif_change,
                 output_dir, type_crop, angle, out_shape, move,
                 label, resolution, step, save_no_coord, buffer_field,
                 list_buffer_name, listFeature, feature,
                 callback, image_num, init_percent):
        super(SegmentationSampleMake, self).__init__(task, input_shp, input_tif, input_shp_buffer, input_tif_change,
                                                     output_dir, type_crop, angle, out_shape, move,
                                                     label, resolution, step, save_no_coord, buffer_field,
                                                     list_buffer_name, listFeature, feature,
                                                     callback, image_num, init_percent)

    def make_sample(self):
        num = 0
        total_num = len(self.data_coordinator)
        csv_list = list()
        for item in self.data_coordinator:
            num += 1
            # print(num, '/', len(self.data_coordinator))
            # 窗口选择
            crop_win = self.get_win(item=item)

            crop_result = self.judge_win(crop_win)
            if crop_result is None:
                continue
            crop_rs, crop_shp = crop_result
            crop_shp02 = self.shp.crop(crop_win, out_shape=self.out_shape_rs, listFeature=self.listFeature,
                                       feature=self.feature)

            # 保存切片的image与mask
            save_name = "segmentation_{}_{}.tif".format(num, self.num2)
            save_name_mask = "segmentation_{}_{}_mask.tif".format(num, self.num2)
            self.img_save(crop_rs, self.output_dir_img, save_name)
            self.img_save(crop_shp02, self.output_dir_mask, save_name_mask)

            csv_list.append('images/{},labels/{}'.format(save_name, save_name_mask))

            if (self.callback is not None) and num % 10 == 0:
                progress = (num / total_num) * 99 * (1 / self.image_num) + self.init_percent * 100
                self.callback(progress)

        self.csv_save(csv_list)

        if self.callback is not None:
            self.callback(100 * (1 / self.image_num + self.init_percent))


# if __name__ == "__main__":
#
#     input_shp_path = r'/Users/zhangshirun/fsdownload/耕地图斑/gengdi.shp'
#     input_tif_path = r'/Users/zhangshirun/fsdownload/高要语义分割三调数据/441283GF2DOM01.IMG'
#
#     csv_path = r"/Users/zhangshirun/fsdownload/duofenlei_out_new_all_311"
#
#     input_shp_buffer_path = None
#
#     if not os.path.exists(csv_path):
#         os.makedirs(csv_path)
#     # outputShape 为输出数据的通道和像素尺寸
#     out_shape = (512, 512)
#     # 滑窗裁剪步长，设置为outputShape大小时为无重叠裁剪
#     step = (512, 512)
#
#     angle = False  # angle=False 为不旋转
#     move = False  # 随机偏移量，不需偏移请设置为False
#     resolution = None  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
#     type_crop = True  # False 为图斑裁剪，设置为True为滑窗裁剪
#     save_no_coord = False
#     # 精准过滤列表
#     list_buffer_name = None
#     # list_buffer_name = ['5303811112010000000','12312']
#     # 精准过滤的字段
#     buffer_field = None
#     # buffer_field = 'ZLDWDM'
#     # 多分类属性字典，1，2，3为对应类别的mask rgb值， 二分类设置为None
#     listFeature = None
#     # listFeature = {'水田':1, '水浇地':2, '旱地':3}
#     # 多分类属性字段，二分类设置为None
#     feature = None
#     # feature = 'DLMC'
#
#     crop_a = SegmentationSampleMake(input_shp_path=input_shp_path, input_tif_path=input_tif_path, out_shape=out_shape,
#                                     step=step, type_crop=type_crop, move=move, angle=angle,
#                                     output_dir=csv_path,
#                                     input_shp_buffer_path=input_shp_buffer_path, save_no_coord=save_no_coord,
#                                     buffer_field=buffer_field, list_buffer_name=list_buffer_name,
#                                     listFeature=listFeature, feature=feature)
#     crop_a.make_sample()
