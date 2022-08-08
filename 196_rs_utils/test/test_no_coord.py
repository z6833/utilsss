import os
import sys
print (sys.path)

import unittest

from utils.ShpGeoToPixel import shp_nocoord_rotate, JsonToImg


class TestNocoord(unittest.TestCase):
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
        self.shp_file_path = os.path.join(root_path,"data/cage_dataset_shp48/cage_bbox_shp48.shp")
        #待测试裁剪tif样本
        self.tif_file_path = os.path.join(root_path,"data/cage_dataset_shp48/cage_20201103_51_3band.tif")
        self.json_file_path = os.path.join(root_path,"test/shp_json_rotate.json")
        self.JsonToImg_save = os.path.join(root_path,"test/polylines_show.png")


    def test_no_coord(self):
        """
            普通裁剪和旋转裁剪，投影坐标转像素坐标
            将原来的shp里面的投影坐标转像素坐标
            保存为json文件
            矢量数据投影坐标转像素坐标后进行重叠验证
            存储为可视化图片
            :return:
        """

        # 投影坐标转像素坐标
        shp_nocoord_rotate(self.shp_file_path, self.tif_file_path, self.json_file_path)
        # 矢量数据投影坐标转像素坐标后的重叠验证
        JsonToImg(self.tif_file_path, self.json_file_path, self.JsonToImg_save)
