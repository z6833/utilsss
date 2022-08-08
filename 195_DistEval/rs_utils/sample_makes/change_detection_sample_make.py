# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/3/31 10:12
# @File    : sample_make.py
# @Desc    : 变化检测切片
import os
# from ..sample_makes.data_save import DataSave
from rasters.raster import RasterData
from sample_makes.sample_make_bace import SampleMakeBase
import numpy as np
import datetime


class ChangeDetectionSampleMake(SampleMakeBase):
    def __init__(self, task, input_shp, input_tif, input_shp_buffer,input_tif_change,
                 output_dir, type_crop, angle, out_shape, move,
                 label, resolution, step, save_no_coord, buffer_field,
                 list_buffer_name, listFeature, feature,
                 callback, image_num, init_percent):
        super(ChangeDetectionSampleMake, self).__init__(task, input_shp, input_tif, input_shp_buffer,input_tif_change,
                 output_dir, type_crop, angle, out_shape, move,
                 label, resolution, step, save_no_coord, buffer_field,
                 list_buffer_name, listFeature, feature,
                 callback, image_num, init_percent)

    def make_sample(self):
        rs2 = RasterData.build_file(self.input_tif_change)
        rs2.load(self.rs.crs_wkt)
        num = 0

        csv_list = list()
        total_num = len(self.data_coordinator)
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
            crop_after_rs = rs2.crop(crop_win, out_shape=self.out_shape_rs)
            # 后时像全空时，跳过
            if np.all(crop_after_rs == 0):
                continue
            # 保存切片的image与mask
            save_name = "change_detection_{}_{}.tif".format(num, self.num2)
            save_after_name = "change_detection_{}_{}_after.tif".format(num, self.num2)
            save_name_mask = "change_detection_{}_{}_mask.tif".format(num, self.num2)
            self.img_save(crop_rs, self.output_dir_img, save_name)
            self.img_save(crop_after_rs, self.output_dir_img_after, save_after_name)
            self.img_save(crop_shp02, self.output_dir_mask, save_name_mask)


            csv_list.append('images/{},images_after/{},labels/{}'.format(save_name, save_after_name, save_name_mask))

            if (self.callback is not None) and num % 10 == 0:
                progress = (num / total_num) * 99 * (1 / self.image_num) + self.init_percent * 100
                self.callback(progress)
        # 保存csv文件
        self.csv_save(csv_list)

        if self.callback is not None:
            self.callback(100 * (1 / self.image_num + self.init_percent))


# if __name__ == "__main__":
#     """
#        变化检测样本制作
#     """
#     # 变化检测矢量路径
#     input_shp_path = r'/Users/zhangshirun/fsdownload/change_detction_data/0304/202003_130105新华区.shp'
#
#     # 变化检测前时像路径
#     input_tif_path = r'/Users/zhangshirun/fsdownload/样本制作样例/变化检测/前时像/201909_xinhua.img'
#
#     # 变化检测后时像路径
#     input_tif_after_path = r'/Users/zhangshirun/fsdownload/样本制作样例/变化检测/后时像/202003_xinhua.img'
#
#     # 输出文件夹
#     output_dir_img = r"/Users/zhangshirun/fsdownload/样本制作样例/变化检测/hhhh"
#
#     # 过滤矢量路径
#     input_shp_buffer_path = None
#
#     # 裁剪图像像素尺寸
#     out_shape = (512, 512)  # outputShape 为输出数据的通道和像素尺寸
#
#     # 滑窗步长
#     step = (512, 512)  # 滑窗裁剪步长，设置为outputShape大小时为无重叠裁剪
#     move = False  # 随机偏移量，不需偏移请设置为False
#     angle = False  # angle=False 为不旋转
#     resolution = None  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
#     type_crop = True  # slideWin=False 为图斑裁剪，设置为True为滑窗裁剪
#     import cProfile
#
#     listFeature = {'水田': 1, '水浇地': 2, '旱地': 3}
#     feature = 'DLMC'
#
#     # 直接把分析结果打印到控制台
#
#     crop_a = ChangeDetectionSampleMake(input_shp_path=input_shp_path, input_tif_path=input_tif_path,
#                                        input_tif_after_path=input_tif_after_path, out_shape=out_shape,
#                                        step=step, type_crop=type_crop, move=move, angle=angle,
#                                        output_dir=output_dir_img,
#                                        resolution=resolution,
#                                        input_shp_buffer_path=input_shp_buffer_path)
#
#     # cProfile.run("crop_a.make_sample()")
#     cProfile.run("crop_a.make_sample()", sort="cumulative")
