# !/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from fiona.crs import  to_string,from_epsg
import unittest

from utilss.ShpGeoToPixel import shp_nocoord_rotate, JsonToImg
import unittest
from rasterio.crs import CRS
from rasters.raster import RasterData
from utilss.window import Rect, RotateRect
from shapes.shape import LayerData
from cropper.cropper import Cropper



class TestCropper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        在执行具体的测试方法前，先被调用
        """

    @classmethod
    def tearDownClass(cls):
        """
        测试结束操作，删除测试数据库
        """
        # return

    def setUp(self) -> None:

        self.test_dir = os.path.dirname(__file__)
        root_path = os.path.dirname(self.test_dir)
        self.tif_A_file_path = os.path.join(root_path, "/Users/zhangshirun/fsdownload/oil/4193.0-413.0.tif")
        self.tif_B_file_path = os.path.join(root_path, "data/projected/cage_tif_proj.tif")
        self.shp_A_file_path = os.path.join(root_path,"/Users/zhangshirun/fsdownload/oil/dongying_shp/oil_well_train.shp")
        self.shp_B_file_path = os.path.join(root_path,"data/projected/cage_box_proj.shp")


    def test_cropper(self):
        """
            批量裁剪测试（对应裁剪及坐标系转换）
            :return:
        """
        rs_A = RasterData.build_file(file_path=self.tif_A_file_path)
        # rs_B = RasterData.build_file(file_path=self.tif_B_file_path)
        shp_A = LayerData.build_file(file_path=self.shp_A_file_path)
        # shp_B = LayerData.build_file(file_path=self.shp_B_file_path)

        rs_A.load(CRS.from_epsg("32649").to_wkt())
        # rs_B.load(CRS.from_epsg("32649").to_wkt())
        shp_A.load(CRS.from_epsg("32649").to_wkt())
        # shp_B.load(CRS.from_epsg("32649").to_wkt())
        print(rs_A.count)
        crs_wkt = CRS.from_epsg("32649").to_wkt()
        cropper = Cropper(crs_wkt)
        cropper.set_crs(crs_wkt)
        left, bottom, right, top = rs_A.region
        output_shape = (3, 1000, 1000)
        crop_win = Rect(left, bottom, right, top)
        cropper.add_crop_data(rs_A)
        # cropper.add_crop_data(rs_B)
        cropper.add_crop_data(shp_A)
        # cropper.add_crop_data(shp_B)

        # 矩形批量裁剪
        ret_list = cropper.crop(crop_win, output_shape)
        for index, obj in enumerate(ret_list):
            obj.save("cropper-test-{}.tif".format(index))


    def test_rotate_cropper(self):
        """
            批量裁剪测试（对应裁剪及坐标系转换）
            :return:
        """
        rs_A = RasterData.build_file(file_path=self.tif_A_file_path)
        rs_B = RasterData.build_file(file_path=self.tif_B_file_path)
        shp_A = LayerData.build_file(file_path=self.shp_A_file_path)
        shp_B = LayerData.build_file(file_path=self.shp_B_file_path)

        rs_A.load(CRS.from_epsg("32649").to_wkt())
        rs_B.load(CRS.from_epsg("32649").to_wkt())
        shp_A.load(CRS.from_epsg("32649").to_wkt())
        shp_B.load(CRS.from_epsg("32649").to_wkt())

        crs_wkt = CRS.from_epsg("32649").to_wkt()
        cropper = Cropper(crs_wkt)
        cropper.set_crs(crs_wkt)
        left, bottom, right, top = rs_A.region
        x = left + (right - left) / 2
        y = top + (bottom - top) / 2
        center = (x, y)
        height = 3000
        width = 3000
        angle = 45
        output_shape = (3, 1000, 1000)
        crop_rotate_win = RotateRect(center, height, width, angle)
        cropper.add_crop_data(rs_A)
        cropper.add_crop_data(rs_B)
        cropper.add_crop_data(shp_A)
        cropper.add_crop_data(shp_B)

        # 旋转矩形批量裁剪
        ret_list = cropper.crop(crop_rotate_win, output_shape)
        for index, obj in enumerate(ret_list):
            obj.save("cropper-rotate-test-{}.tif".format(index))






