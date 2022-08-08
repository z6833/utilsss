#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/3/31 10:12
# @File    : target_detection_sample_make.py
# @Desc    : 目标检测切片
import os
from tqdm import tqdm
from pathlib import Path
import sys; sys.path.append(Path.cwd().parent.as_posix())
from sample_makes.data_save import CocoDateSet, add_detection_item
from sample_makes.sample_make_bace import SampleMakeBase


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

    def make_sample(self, _type='norm', _index=0):
        num = 0
        total_num = len(self.data_coordinator)
        if self.label is None:
            label_dict = None
        else:
            label_dict = {(i + 1): lb for i, lb in enumerate(self.label)}
        coco_obj = CocoDateSet(label_dict)

        for item in self.data_coordinator:
            num += 1
            # print(num, '/', total_num)

            # 窗口选择
            crop_win = self.get_win(item=item)

            crop_result = self.judge_win(crop_win)
            if crop_result is None:
                continue

            crop_rs, crop_shp02 = crop_result
            save_name = "target_detection_{}_{}.tif".format(num, self.num2)

            image_information, image_annotation = add_detection_item(crop_rs=crop_rs, crop_shp=crop_shp02,
                                                                     output_dir_img=self.output_dir_img,
                                                                     save_name=save_name, out_shape=self.out_shape_rs,
                                                                     feature=self.feature)
            if image_annotation:
                self.img_save(crop_rs, self.output_dir_img, save_name)
                coco_obj.add_information(image_information, image_annotation)
            else:
                continue

            if (self.callback is not None) and num % 10 == 0:
                progress = (num / total_num) * 99 * (1 / self.image_num) + self.init_percent * 100
                self.callback(progress)

        coco_json = os.path.join(self.output_dir, f"{os.path.split(self.input_tif)[-1][:-4]}_{_type}_{_index}.json")
        coco_obj.save(coco_json)
        if self.callback is not None:
            self.callback(100 * (1 / self.image_num + self.init_percent))


def get_params():

    params = {
        'task': 1,
        'input_shp': None,
        'input_tif': None,
        'input_shp_buffer': None,
        'input_tif_change': None,
        'listFeature': None,
        'step': (300, 300),  # 滑窗裁剪步长，设置为outputShape大小时为无重叠裁剪,
        'angle': False,  # angle=False 为不旋转，为True时[10,90]度逆时针随机裁剪
        'type_crop': False,  # type_crop=False 为图斑裁剪，设置为True为滑窗裁剪
        'out_shape': (500, 500),  # outputShape 为输出数据的通道和像素尺寸
        'move': False,  # 随机偏移量，不需偏移请设置为False [-50, -100, -150, 50, 100, 150]随机偏移，可在上方修改
        'label': None,  # 生成json的用的label，单分类设置为None
        'output_dir': None,
        'save_no_coord': None,
        'resolution': None,  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
        'buffer_field': None,
        'list_buffer_name': None,
        'callback': None,
        'image_num': None,
        'init_percent': None,
        'feature': None,
    }
    return params


def build_maker(params):
    sample_maker = TargetDetectionSampleMake(task=params['task'],
                                             input_shp=params['input_shp'],
                                             input_tif=params['input_tif'],
                                             input_shp_buffer=params['input_shp_buffer'],
                                             input_tif_change=params['input_tif_change'],
                                             listFeature=params['listFeature'],
                                             step=params['step'],
                                             angle=params['angle'],
                                             type_crop=params['type_crop'],
                                             out_shape=params['out_shape'],
                                             move=params['move'],
                                             label=params['label'],
                                             output_dir=params['output_dir'],
                                             save_no_coord=params['save_no_coord'],
                                             resolution=params['resolution'],
                                             buffer_field=params['buffer_field'],
                                             list_buffer_name=params['list_buffer_name'],
                                             callback=params['callback'],
                                             image_num=params['image_num'],
                                             init_percent=params['init_percent'],
                                             feature=params['feature']
                                             )

    return sample_maker


def build_dataset(input_shps, tif_path_list, output_dir, _type='val'):
    """
    制作测试集，裁剪方法用滑窗 ，type_crop=True；制作训练集，裁剪方法：图斑，type_crop=False
    :param input_shp: shp文件路径
    :param tif_path_list: list, tif文件路径
    :param output_dir: 结果保存路径
    :param _type: 制作训练集还是测试集
    :param aug: 数据增强；0表示不做增强；>0表示需要增强的次数；一半做move增强，一半做angle增强
    :return:
    """

    # 获取sample_maker的所有参数
    params = get_params()
    if _type == "train":
        params['type_crop'] = False
        aug = True
    # type_crop = True为滑窗裁剪
    elif _type == "val":
        params['type_crop'] = True
        aug = False
    elif _type == "val2":
        params['type_crop'] = False
        aug = False

    else:
        return

    for tif_path in tqdm(tif_path_list, total=len(tif_path_list), desc="Cropping: "):

        # if '20210202.tif' not in tif_path:
        #     continue

        if 'new_dongying' in tif_path:
            params['input_shp'] = input_shps[0]
        else:
            params['input_shp'] = input_shps[1]

        params['input_tif'] = tif_path

        # 原始路径
        tmp_output_dir = os.path.join(output_dir, _type, tif_path.split('/')[-1][:-4])
        params['output_dir'] = os.path.join(tmp_output_dir, 'raw_data')

        sample_maker = build_maker(params)
        sample_maker.make_sample()

        if aug:
            aug_output_dir = os.path.join(tmp_output_dir, 'aug_data')

            # 2018和2021的数据都扩充8倍，维持总量在15K左右
            nums = 8
            for i in tqdm(range(nums), total=nums, desc="Data Augumenting: "):

                params['angle'] = False
                params['move'] = True
                aug_type = 'move'
                params['output_dir'] = os.path.join(aug_output_dir, f'{i}_{aug_type}')
                sample_maker = build_maker(params)
                sample_maker.make_sample(_type=aug_type, _index=i)

                params['angle'] = True
                params['move'] = False
                aug_type = 'angle'
                params['output_dir'] = os.path.join(aug_output_dir, f'{i}_{aug_type}')
                sample_maker = build_maker(params)
                sample_maker.make_sample(_type=aug_type, _index=i)

    return


def main():

    """
    测试集：20210202.tif和2018中选取3张；裁剪方法：滑窗
    训练集：其他tif；裁剪方法：图斑
    type_crop=False 为图斑裁剪，设置为True为滑窗裁剪
    """

    # 输出结果保存路径
    base_output_dir = r"/data_01/results"

    tif_base_dir0 = r'/data_02/2018_dongying/new_dongying/dongying_images'
    tif_base_dir1 = r'/data_02/2022_oilwell_data/2019'
    tif_base_dir2 = r'/data_02/2022_oilwell_data/2021'
    tif_path_list0 = [os.path.join(tif_base_dir0, name) for name in os.listdir(tif_base_dir0) if name.endswith('.tif')]
    tif_path_list1 = [os.path.join(tif_base_dir1, name) for name in os.listdir(tif_base_dir1) if name.endswith('.tif')]
    tif_path_list2 = [os.path.join(tif_base_dir2, name) for name in os.listdir(tif_base_dir2) if name.endswith('.tif')]

    # 所有tif文件所在路径
    # tif_path_list_all = tif_path_list0 + tif_path_list1 + tif_path_list2
    tif_path_list_all = tif_path_list0 + tif_path_list2

    # 所有shp文件所在路径
    shp_path_0 = r'/data_02/2018_dongying/new_dongying/dongying_label/2018_oilwell.shp'
    shp_path_1 = r'/data_01/updated/shps/oilwell.shp'
    shp_path_list = [shp_path_0, shp_path_1]

    # 训练集路径
    val_tif_path_list = [
        os.path.join(tif_base_dir0, 'new-4193.0-413.tif'),
        os.path.join(tif_base_dir0, 'new-4196.0-415.tif'),
        os.path.join(tif_base_dir0, 'new-4197.0-417.tif'),
        # os.path.join(tif_base_dir1, '2019dy-39.tif'),
        os.path.join(tif_base_dir2, '20210202.tif'),
    ]

    train_tif_path_list = [fp for fp in tif_path_list_all if fp not in val_tif_path_list]

    # 构造训练集
    build_dataset(input_shps=shp_path_list, tif_path_list=train_tif_path_list,
                  output_dir=base_output_dir, _type='train')

    # 构造测试集
    # build_dataset(input_shps=shp_path_list, tif_path_list=val_tif_path_list,
    #               output_dir=base_output_dir, _type='val')

    # build_dataset(input_shps=shp_path_list, tif_path_list=val_tif_path_list,
    #               output_dir=base_output_dir, _type='val2')

    return


if __name__ == "__main__":
    main()





