import os
import sys
import unittest
import cv2 as cv
from shapes.shape import LayerData
from utils.window import Rect, RotateRect
import rasterio
from rasters.raster import RasterData
import math

class TestShape(unittest.TestCase):
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
        self.raster_file_path = os.path.join(root_path,"/Users/zhangshirun/fsdownload/test_img/4193.0-413.0.tif")
        self.shape_file_path = os.path.join(root_path,"/Users/zhangshirun/fsdownload/test_img/oil_shp/oil_well_new_train.shp")


    def test_crop_shape00(self):
        """
        测试裁剪栅格数据
        """
        shp = LayerData.build_file(self.shape_file_path)

        rs = RasterData.build_file(self.raster_file_path)
        rs.load()
        shp.load(rs.crs_wkt)
        left, bottom, right, top = rs.region
        print("left, bottom, right, top",left, bottom, right, top)
        crop_win = Rect(left, bottom, right, top)
        # print(crop_win.left)
        # crop_win_n = RasterData(left, bottom, right, top)
        pix_x = rs.data_transform.a
        pix_y = rs.data_transform.e


        output_shape = (3, 400, 400)
        center = (left + right) / 2, (bottom + top) / 2,
        height = 200 * pix_x
        width = 200 * abs(pix_y)
        angle = 45
        crop_win = RotateRect(center, height, width, angle)
        print("crop_win.TopWin=",crop_win.TopWin)
        print("crop_win.Top=",crop_win.top)
        crop_rs = rs.crop(crop_win, out_shape=output_shape)
        # print(crop_rs.profile)
        crop_rs.save(os.path.join(self.test_dir, "test_crop_rotate_raster_small_30.tif"))



