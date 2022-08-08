# !/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import os
import uuid
from shutil import copyfile
# from osgeo import gdal
import pyproj
from pyproj import Transformer
import rasterio
from rasterio import Affine
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import calculate_default_transform, reproject
import tempfile

import numpy as np

# 指定缓存路径，用于存储临时的影像文件
# import sys
# # sys.path.append('..')
# import pathlib
# cwd_path = pathlib.Path(__file__).absolute()
# parent_path = cwd_path.parent.parent.as_posix()
# sys.path.append(parent_path)
from base.data_base import DataBase
# from base.driver_base import DriverError
from rasters.driver import TifDriver
from utilss.window import Rect, RotateRect


import time
# TMP_DIR = tempfile.mkdtemp()


def get_region(region, transformer):
    """
    计算region区域在坐标转换（transformer）后的区域
    :param region: 原始的区域，以四元组（left, bottom, right, top）表示
    :param transformer: 坐标转换对象， pyproj的对象Transformer，表示从原坐标系到目的坐标系
    :return: 返回转换后坐标系的区域，以四元组（left, bottom, right, top）表示
    """
    left, bottom, right, top, = region
    xx_yy_list = list()
    xx_yy_list.append(transformer.transform(left, bottom))
    xx_yy_list.append(transformer.transform(left, top))
    xx_yy_list.append(transformer.transform(right, bottom))
    xx_yy_list.append(transformer.transform(right, top))
    minX = 0
    minY = 0
    maxX = 0
    maxY = 0

    for i, (xx, yy) in enumerate(xx_yy_list):
        if i == 0:
            minX = xx
            minY = yy
            maxX = xx
            maxY = yy
        else:
            if minX > xx:
                minX = xx
            if maxX < xx:
                maxX = xx
            if minY > yy:
                minY = yy
            if maxY < yy:
                maxY = yy
    return minX, minY, maxX, maxY


class RasterData(DataBase):
    """
    栅格数据类，两种方式表述数据，一种是以文件路径表示，一种是以数据和profile表示
    """

    def __init__(self, file_path=None, profile=None, data=None, driver=None):
        """
        初始化函数，用于build_data或者build_file调用来构建对象
        :param file_path: 影像文件路径，以文件来构建栅格数据对象
        :param profile: 栅格元数据描述
        :param data: 栅格的数据，numpy.array格式
        """
        self.profile = profile
        self._data = data
        self.file_path  = file_path
        super(RasterData, self).__init__(data_uri=file_path, driver=driver)

    def load(self, crs_wkt=None):
        if crs_wkt:
            self.crs = crs_wkt
        if self.load_flag is True:
            return
        super().load()
        load_handle = self.driver.handle
        raw_crs_wkt = load_handle.crs.to_wkt()
        # print("load_handle.crs---",load_handle.crs)
        # print("load_handle---",load_handle)
        if self.crs_wkt is not None and raw_crs_wkt is not None and raw_crs_wkt != self.crs_wkt:
            crs = CRS.from_wkt(self.crs_wkt)
            self.data_handle = WarpedVRT(load_handle, crs=crs, resampling=Resampling.cubic_spline)
            # 计算变换坐标系后影像的边界
            # @ 注意：此段代码不能直接替换为(self.region = self.data_handle.bounds)，虚拟文件不会改变bound边界值

            #######
            transformer = Transformer.from_crs(
                pyproj.CRS.from_wkt(load_handle.crs.to_wkt()), pyproj.CRS.from_wkt(self.crs_wkt), always_xy=True)
            self.region = get_region(load_handle.bounds, transformer)
            self.data_transform = transformer
            self.count = self.data_handle.count
        else:
            self.data_handle = load_handle
            self.region = self.data_handle.bounds
            self.crs_wkt = raw_crs_wkt
            self.data_transform = self.data_handle.transform
            self.count = self.data_handle.count
            self.crss = self.data_handle.crs
        # 更新profile
        self.profile = self.data_handle.profile

    @property
    def crs(self):
        """
        当前影像的坐标系（wkt描述）字符串
        """
        if self.crs_wkt is None:
            self.load()
        return self.crs_wkt

    @crs.setter
    def crs(self, new_crs_wkt):
        """
        设置当前矢量坐标系，如果坐标系更新，读取标识符设置为False，下次需要重新读取
        :param new_crs_wkt:
        :return:
        """
        if self.crs_wkt != new_crs_wkt:
            self.load_flag = False
            self.crs_wkt = new_crs_wkt

    @property
    def data(self):
        """
        影像的数据，numpy.array形式的数据
        """

        if self._data is None:
            self.load()

        # if self._data is None and self.profile is not None:
        #     data = rasterio.open(self.file_path)
        #     return data.read()
        return self._data

    @property
    def cur_handle(self):
        """
        获取当前的影像处理句柄
        :return:
        """
        return self.data_handle

    def mask(self, mask_arr):
        """
        对当前影像进行掩膜操作，会修改当前影像数据
        :param mask_arr: 和影像shape一样的掩膜
        """
        mask = (mask_arr > 0).astype(np.uint8)
        self._data = self.data * mask

    @classmethod
    def build_file(cls, file_path, driver=None):
        """
        以文件的方式创建栅格数据对象
        :param file_path: 文件路径
        :return: 栅格数据对象
        """
        # 暂时仅支持tif驱动
        driver = TifDriver()
        ret_obj = cls(file_path=file_path, driver=driver)
        return ret_obj

    @classmethod
    def build_data(cls, data, profile, driver=None):
        """
        以数据和元数据描述的方式创建栅格数据对象
        :param data: data格式为c,h,w
        :param profile: 元数据描述字典
        :return:
        """
        # 暂时仅支持tif驱动
        driver = TifDriver()
        ret_obj = cls(profile=profile, data=data, driver=driver)
        return ret_obj

    def raster2shape(self):
        """
        将栅格转化为矢量，适用于mask类型的数据
        :return:
        """
        raise NotImplementedError

    def save(self, filename):
        """
        将数据导出保存到一个文件中
        :return:
        """
        super().save(uri=filename)

    def crop(self, rect_obj: Rect, out_shape=None):
        """
        对当前载入的数据进行影像裁剪，当前仅支持矩形边框裁剪
        todo 增加对旋转矩形裁剪的支持
        :param rect_obj: 表示裁剪的矩形切片区域对象（可以是正矩形或者旋转矩形对象）
        :param out_shape: 输出栅格的尺寸(channel,height,width)，None表示与原来栅格尺寸一致
        :return: 返回RasterData类型的对象
        """
        self.load()

        if isinstance(rect_obj, RotateRect):
            # 旋转切割
            window = self.cur_handle.window(rect_obj.left, rect_obj.bottom, rect_obj.right, rect_obj.top)
            data = self.cur_handle.read(window=window)
            cut_transform = self.cur_handle.window_transform(window)
            # print("data.shape", data.shape)
            if out_shape:
                c, height, width = out_shape
            else:
                height = int(rect_obj.height / (-cut_transform.e))
                width = int(rect_obj.width / cut_transform.a)

            scaling = Affine.scale(
                rect_obj.width / width / cut_transform.a,  # window.width / width,
                rect_obj.height / height / (-cut_transform.e)  # window.height / height
            )
            # 以做下点为基准进行变换，构建放射矩阵
            left_offset = rect_obj.leftbottom[0] - rect_obj.left
            angle = rect_obj.angle
            translating = Affine.translation(left_offset / cut_transform.a, 0)
            rotating = Affine.rotation(angle)
            # 右边的变换矩阵先行进行变换，参见 https://www.louyaning.cn/article/oschina-%E7%BC%96%E8%BE%91?id=1575
            dst_transform = cut_transform * translating * rotating * scaling
            dst_data = np.zeros((c, height, width), np.uint8)
            dst_proj = reproject(
                data,
                dst_data,
                src_transform=cut_transform,
                src_crs=self.cur_handle.crs,
                dst_transform=dst_transform,
                dst_crs=self.cur_handle.crs,
                resampling=Resampling.nearest)

            profile = self.cur_handle.profile
            profile['width'] = width
            profile['height'] = height
            profile['driver'] = 'GTiff'
            profile['transform'] = dst_transform
            ret_raster = RasterData.build_data(data=dst_data, profile=profile)
            return ret_raster
        else:
            window = self.cur_handle.window(rect_obj.left, rect_obj.bottom, rect_obj.right, rect_obj.top)
            # print("window----",window)
            # print("window----",window)
            # print("window----",window.left)
            data = self.cur_handle.read(window=window, out_shape=out_shape)
            profile = self.cur_handle.profile
            c, height, width = data.shape
            # if out_shape:
            #     c, height, width = out_shape
            # else:
            #     height = window.height
            #     width = window.width
            profile['width'] = width
            profile['height'] = height
            profile['driver'] = 'GTiff'
            dst_transform = self.cur_handle.window_transform(window)
            # print(f'dst_transform{dst_transform}')
            scaling = Affine.scale(window.width / width,
                                   window.height / height
                                   )
            dst_transform *= scaling
            profile['transform'] = dst_transform
            ret_raster = RasterData.build_data(data=data, profile=profile)
            return ret_raster

    def clear(self):
        """
        资源释放，释放文件句柄，删除临时文件
        """
        self.profile = None
        self._data = None
        self.data_handle.close()
        self.driver.close()



