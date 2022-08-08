# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/3/30 10:12
# @File    : sample_make.py
# @Desc    : 样本切片基类
import os
import random
from shapely.geometry import Polygon
# import sys
# import pathlib
from rasters.raster import RasterData
from shapes.shape import LayerData
from sample_makes.data_read import *
from sample_makes.data_save import img_save_coord, img_save_no_coord


# cwd_path = pathlib.Path(__file__).absolute()
# parent_path = cwd_path.parent.parent.as_posix()
# sys.path.append(parent_path)


class SampleMakeBase:
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
        self.output_dir_img = os.path.join(output_dir, 'images')
        self.num2 = random.randint(0, 9999)
        # 初始化文件输出路径
        self._init_dir()
        # 初始化加载影像
        self._init_load()
        # 初始化分辨率
        self._init_resolution()
        # 初始化迭代器
        self.data_coordinator = self.data_read()
        # 初始化影像保存方法
        self._init_img_save()

    def __call__(self, *args, **kwargs):
        self.make_sample()

    def make_sample(self):
        raise NotImplementedError

    def _init_dir(self):
        """
        初始化输出结果路径
        """
        # 切片文件输出路径初始化
        self.output_dir_img = os.path.join(self.output_dir, 'images')
        self.output_dir_mask = os.path.join(self.output_dir, 'labels')
        self.output_dir_img_after = os.path.join(self.output_dir, 'images_after')
        if not os.path.exists(self.output_dir_img):
            os.makedirs(self.output_dir_img)
        if self.task == 2:
            if not os.path.exists(self.output_dir_mask):
                os.makedirs(self.output_dir_mask)
        elif self.task == 3:
            if not os.path.exists(self.output_dir_mask):
                os.makedirs(self.output_dir_mask)
            if not os.path.exists(self.output_dir_img_after):
                os.makedirs(self.output_dir_img_after)
        # csv路径初始化
        csv_name_dict = {
            '1': "target_detection",
            '2': "segmentation_sample",
            '3': "change_detection"
        }
        self.csv_name = csv_name_dict[str(self.task)]
        self.csv_path = self.output_dir + '/{}.csv'.format(self.csv_name)

    def _init_load(self):
        """
        初始化并加载影像
        """
        # 样本加载
        self.rs = RasterData.build_file(self.input_tif)
        self.left, self.bottom, self.right, self.top = self.rs.region
        self.rs.load()
        self.out_shape_rs = (self.rs.count, self.out_shape[0], self.out_shape[1])
        # 矢量加载，并判断坐标系是否一致
        self.shp = LayerData.build_file(self.input_shp)
        self.shp.load(self.rs.crs_wkt)
        # self.shp_buffer = None
        self.shp_data = self.shp.data_handle
        # 过滤矢量加载
        if self.input_shp_buffer:
            self.shp_buffer = LayerData.build_file(self.input_shp_buffer)
            self.shp_buffer.load(self.rs.crs_wkt)
        else:
            self.shp_buffer = None

    def _init_resolution(self):
        """
        初始化分辨率
        """
        # 读取分辨率
        if self.resolution is None:
            self.pix_x = self.rs.data_transform.a
            self.pix_y = self.rs.data_transform.e
        else:
            self.pix_x = self.resolution[0]
            self.pix_y = self.resolution[1]

    def _init_img_save(self):
        """
        样本切片是否保存地理坐标信息
        :return:
        """
        if self.save_no_coord:
            self.img_save = img_save_no_coord
        else:
            self.img_save = img_save_coord

    def data_read(self):
        """
        读取数据
        返回一个裁剪坐标迭代器
        """
        # 滑窗地理范围步长
        if self.step is None:
            # 列步长
            row_step = self.out_shape[0] * abs(self.pix_y)
            # 行步长
            col_step = self.out_shape[1] * self.pix_x
        else:
            row_step = self.step[0] * abs(self.pix_y)
            col_step = self.step[1] * self.pix_x

        # 滑窗裁剪
        if self.type_crop is True:
            win_w = self.pix_x * self.out_shape[0]
            win_h = abs(self.pix_y) * self.out_shape[1]
            item_crop = cut_sliding_win(left=self.left,
                                        right=self.right,
                                        top=self.top,
                                        bottom=self.bottom,
                                        win_width=win_w,
                                        win_height=win_h,
                                        row_step=row_step,
                                        col_step=col_step,
                                        shp_buffer=self.shp_buffer,
                                        buffer_field=self.buffer_field,
                                        list_buffer_name=self.list_buffer_name
                                        )
        # 图斑裁剪
        else:
            item_crop = cut_spots(shp_data=self.shp_data,
                                  pix_x=self.pix_x,
                                  pix_y=self.pix_y,
                                  out_shape=(self.out_shape[0], self.out_shape[1])
                                  )
        return item_crop

    # 根据坐标得到滑窗的坐标范围
    def get_win(self, item):
        # 普通窗口裁剪
        crop_win = crop_win_rectangle(item[0], item[1], self.pix_x, self.pix_y, self.out_shape)
        # 裁剪窗口平移
        if self.move:
            crop_win = crop_win_dithering(crop_win.left, crop_win.top, self.pix_x, self.pix_y, out_shape=self.out_shape)
        # 裁剪窗口旋转
        if self.angle:
            crop_win = crop_win_revolve(crop_win.left, crop_win.top, self.pix_x, self.pix_y, self.angle,
                                        out_shape=self.out_shape)
        # 是否要进行过滤
        # todo @江一帆 此过滤放到数据读取时候过滤比较好，每次读取数据再去过滤，开销太大
        if self.shp_buffer is not None:
            # 精准过滤
            if self.list_buffer_name is not None:
                items = precision_buffer_restraint(self.shp_buffer, self.buffer_field, self.list_buffer_name)
                # 得到精准的过滤的polygon
                for item in items:
                    # 过滤范围包含窗口的范围
                    if filtrate_polygon(crop_win=crop_win, polygons=item):
                        return crop_win
                    # 过滤范围不包含窗口范围
                    else:
                        return False
            # 全遍历过滤
            else:
                if buffer_restraint(crop_win=crop_win, shp_buffer=self.shp_buffer):
                    return crop_win
                else:
                    return False
        else:
            return crop_win

    def judge_win(self, crop_win):
        # todo 函数命名有歧义，judge或者check应该返回bool值，此处表示对样本进行裁剪
        """
        判断将要切片的样本是否符合要求
        :param crop_win:
        :return:
        """
        if not crop_win:
            return None
        if crop_win.left < self.left or crop_win.right > self.right or \
                crop_win.top > self.top or crop_win.bottom < self.bottom:
            return None
        crop_shp = self.shp.crop(crop_win)
        # 跳过空白图像
        if not crop_shp.data:
            return None
        crop_rs = self.rs.crop(crop_win, out_shape=self.out_shape_rs)
        # 跳过全空影像
        if np.all(crop_rs.data == 0):
            return None
        # 图片像素占比大于一半进行保存
        if np.count_nonzero(crop_rs.data, axis=None) / np.size(crop_rs.data) < 0.5:
            return None
        return [crop_rs, crop_shp]

    def csv_save(self, csv_list):
        with open(self.csv_path, mode='a', newline='', encoding='utf-8') as csv_v:
            # 多分类csv头文件
            if self.listFeature:
                list_feature = ''
                for i, item in enumerate(self.listFeature):
                    list_feature = list_feature + ',' + item + ',' + str(self.listFeature[item])
                csv_v.write('#,version,1.0,data_creator,{}'.format(datetime.date.today()))
                csv_v.write('\n')
                csv_v.write('{}'.format(list_feature))
                csv_v.write('\n')
            for line in csv_list:
                csv_v.write(line)
                csv_v.write('\n')




