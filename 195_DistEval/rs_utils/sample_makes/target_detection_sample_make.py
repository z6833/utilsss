#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/3/31 10:12
# @File    : target_detection_sample_make.py
# @Desc    : 目标检测切片
import os
from sample_makes.data_save import CocoDateSet, add_detection_item
from sample_makes.sample_make_bace import SampleMakeBase
import numpy as np
# from utils.log import logger


class TargetDetectionSampleMake(SampleMakeBase):
    def __init__(self, task, input_shp, input_tif, input_shp_buffer, input_tif_change,
                 output_dir, type_crop, angle, out_shape, move,
                 label, resolution, step, save_no_coord, buffer_field,
                 list_buffer_name, listFeature, feature,
                 callback, image_num, init_percent):
        super(TargetDetectionSampleMake, self).__init__(task, input_shp, input_tif, input_shp_buffer, input_tif_change,
                                                        output_dir, type_crop, angle, out_shape, move,
                                                        label, resolution, step, save_no_coord, buffer_field,
                                                        list_buffer_name, listFeature, feature,
                                                        callback, image_num, init_percent)

    def make_sample(self):
        num = 0
        total_num = len(self.data_coordinator)
        if self.label is None:
            label_dict = None
        else:
            label_dict = {(i + 1): lb for i, lb in enumerate(self.label)}
        coco_obj = CocoDateSet(label_dict)
        for item in self.data_coordinator:
            num += 1
            print(num, '/', total_num)
            # 窗口选择
            crop_win = self.get_win(item=item)

            crop_result = self.judge_win(crop_win)
            if crop_result is None:
                continue
            crop_rs, crop_shp02 = crop_result
            save_name = "target_detection_{}_{}.tif".format(num, self.num2)
            # 调试代码，输出
            # if True:
            #     if num > 100:
            #
            #         crop_rs.save(save_name)
            #         crop_shp02.save(save_name[:-3] + "shp")
            #         print(os.path.abspath(save_name))
            #         if num > 114:
            #             exit(0)
            image_information, image_annotation = add_detection_item(crop_rs=crop_rs, crop_shp=crop_shp02,
                                                                     output_dir_img=self.output_dir_img,
                                                                     save_name=save_name, out_shape=self.out_shape_rs,
                                                                     feature=self.feature, num=num, num2=self.num2)
            if image_annotation:
                self.img_save(crop_rs, self.output_dir_img, save_name)
                coco_obj.add_information(image_information, image_annotation)
            else:
                continue

            if (self.callback is not None) and num % 10 == 0:
                progress = (num / total_num) * 99 * (1 / self.image_num) + self.init_percent * 100
                self.callback(progress)
        # logger.info("current images:{},is saving sample_lib.json".format(num))
        coco_json = os.path.join(self.output_dir, "sample_lib.json")
        coco_obj.save(coco_json)
        if self.callback is not None:
            self.callback(100 * (1 / self.image_num + self.init_percent))


# if __name__ == "__main__":
#
#     input_tif_path = r'D:\\dongying_data\\0.5oilwell\\img\\new-4193.0-413.tif'
#
#     input_shp_path = r'D:\\dongying_data\\0.5oilwell\\shpfile\\2018_oilwell.shp'
#
#     output_dir = r"D:\\dongying_data\\0.5oilwell\\new_data"
#     input_shp_buffer_path = None
#
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#
#     out_shape = (500, 500)  # outputShape 为输出数据的通道和像素尺寸
#     step = (500, 500)  # 滑窗裁剪步长，设置为outputShape大小时为无重叠裁剪
#     move = False  # 随机偏移量，不需偏移请设置为False [-50, -100, -150, 50, 100, 150]随机偏移，可在上方修改
#     angle = False  # angle=False 为不旋转，为True时[10,90]度逆时针随机裁剪
#     label = None  # 生成json的用的label，单分类设置为None
#     # label = ['水田', '水浇地', '旱地']  # 多分类生成json的用的label，单分类设置为None
#     resolution = None  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
#     type_crop = True  # slideWin=False 为图斑裁剪，设置为True为滑窗裁剪
#     save_no_coord = None
#     buffer_field = None
#     list_buffer_name = None
#     # feature = 'DLMC'
#     # 多分类属性字段
#     listfeature = None
#     feature = None
#
#     sample_m = TargetDetectionSampleMake(task=1, input_shp=input_shp_path, input_tif=input_tif_path,
#                                          input_shp_buffer=None, input_tif_change=None, output_dir=output_dir,
#                                          type_crop=type_crop, angle=angle, out_shape=out_shape,move=move,
#                                          label=label, resolution=resolution, step=step,
#                                          save_no_coord=save_no_coord, buffer_field=buffer_field,
#                                          list_buffer_name=list_buffer_name, listFeature=listfeature,
#                                          feature=feature, callback=None, image_num=None, init_percent=None)
#     sample_m.make_sample()
