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
        self.raster_file_path = os.path.join(root_path,"data/cage_dataset_shp48/cage_20201103_51_3band.tif")
        self.tif_file_path = os.path.join(root_path,"test/test_crop_rotate_raster_small_45.tif")
        self.tif_save_file_path = os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/data/output/cage_bbox_shp48.tif")
        # self.shape_file_path = os.path.join(root_path,"data/projected/cage_box_proj.shp")shape_file_path
        # /mnt/cephfs/deeplearning/data/2019_rs_monitor/370829嘉祥县/标注的数据/train_areas_0118/area_2_fixed_0_2_3_0118.shp
        self.shape_file_path = os.path.join(root_path,'/Users/zhangshirun/fsdownload/oil/01/111.shp')
        self.proj_raster_file_path = os.path.join(root_path,"data/projected/cage_tif_proj.tif")
        self.proj_shape_file_path = os.path.join(root_path,"data/projected/cage_box_proj.shp")


    def test_crop_shape00(self):
        """
        测试裁剪栅格数据
        """
        shp = LayerData.build_file(file_path=self.shape_file_path)

        left, bottom, right, top = shp.region
        output_shape = (3,1000,1000)
        crop_win = Rect(left, bottom, right, top)
        crop_rs = shp.crop(crop_win,out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir,"test_crop_shape_mask.tif"))
        # for i in crop_rs.data:
        #     print(i['geometry']['coordinates'][0])
        #     for j in i['geometry']['coordinates'][0]:
        #         if j[0]>left+100+500 or j[0]<left+100 or j[1]> bottom+250+500or j[1]<bottom+250:
        #             print("yessssssssssss!!!!!!!!")


    def test_crop_shape(self):
        """
        测试裁剪栅格数据
        """
        shp = LayerData.build_file(file_path=self.shape_file_path)
        left, bottom, right, top = shp.region
        print("shp.region",shp.region)
        output_shape = (1,1000,1000)
        crop_win = Rect(left+1000, bottom+2500, left+1000+output_shape[2], bottom+2500+output_shape[1])

        crop_rs = shp.crop(crop_win,out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir,"test_crop_shape_mask.tif"))

    def test_rotate_crop_shape(self):
        """
        测试裁剪旋转数据
        """
        shp = LayerData.build_file(file_path=self.shape_file_path)
        left, bottom, right, top = shp.region

        x = left + (right - left) / 2
        y = top + (bottom - top) / 2

        center = (x, y)
        height = 3000
        width = 3000
        output_shape = (1, 3000, 3000)
        angle = 45
        crop_win = RotateRect(center=center, height=height, width=width, angle=angle)
        crop_rs = shp.crop(crop_win, out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir, "test_rotate_crop_shape_mask5.tif"))

    def test_crop_shptotif(self):

        mask_path = r"/Users/zhangshirun/fsdownload/anqing_yixiu/aq_yx_gengdi.shp"
        shp = LayerData.build_file(file_path=mask_path)
        left, bottom, right, top = shp.region
        output_shape = (1, 10000, 10000)
        crop_win = Rect(left , bottom , right, top)
        crop_rs = shp.crop(crop_win, out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir, "test_rotate_crop_shape_mask5.tif"))
    def test_tip_to_crop_shape(self):
        """
        测试根据栅格裁剪对应矢量
        1、根据栅格裁剪对应矢量数据
        2、根据栅格旋转裁剪对应矢量数据
        """
        shp = LayerData.build_file(file_path=self.shape_file_path)
        print(shp.crs)
        # rs = RasterData.build_file(file_path=self.tif_file_path)
        # left, bottom, right, top = rs.region
        # x = left + (right - left) / 2
        # y = top + (bottom - top) / 2
        # center = (x, y)
        # height = 2000
        # width = 2000
        # output_shape = (1, 2000, 2000)
        # angle = 45
        # crop_win = RotateRect(center, height, width, angle)
        # rect_win = Rect(left, bottom, right, top)
        #
        # # 根据栅格裁剪对应矢量数据，保存为masktif
        # crop_rs = shp.crop(rect_win, out_shape=output_shape)
        # crop_rs.save(os.path.join(self.test_dir, "test_rotate_crop_shape_mask2.tif"))
        #
        # # 根据栅格旋转裁剪对应矢量数据，保存为masktif
        # crop_rs_rotate = shp.crop(crop_win, out_shape=output_shape)
        # crop_rs_rotate.save(os.path.join(self.test_dir, "test_rotate_crop_shape_mask3.tif"))

    # def test_get_all_models(self):
    #     """
    #     测试获取所有模型
    #     """
    #     # with self.app.app_context():
    #     self.assertEqual(res.errno, ErrNo.SUCCESS.get_code())