import os
import sys

import fiona
import numpy as np
print (sys.path)
import rasterio
import unittest
from rasterio.crs import CRS
from rasters.raster import RasterData
from utils.window import Rect, RotateRect
from shapes.shape import LayerData

class TestRaster(unittest.TestCase):
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
        # /mnt/cephfs/deeplearning/data/2019_rs_monitor/370829嘉祥县/前时相/370829AP0DOM01.img
        self.raster_file_path = os.path.join(root_path,"/data2/前时相/370829AP0DOM01.img")
        self.raster_file_path_test = os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils/data/test_tif/4195_62_12.tif")

        self.raster_file_CoordB_path = os.path.join(root_path,"data/projected/cage_tif_proj.tif")
        self.proj_raster_file_path = os.path.join(root_path,"data/projected/cage_tif_proj.tif")
        self.shape_file_path = os.path.join(root_path, "data/cage_dataset_shp48/cage_bbox_shp48.shp")


        # self.raster_build_file_path=os.path.join(root_path,"/Users/zhangshirun/fsdownload/070302增城区永宁街道.tif")
        self.raster_build_file_path=os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils/data/0705/070501_海珠区赤岗街道.tif")
        # self.shape_build_file_path = os.path.join(root_path, "/Users/zhangshirun/fsdownload/0703.shp")
        self.shape_build_file_path = os.path.join(root_path, "/Users/zhangshirun/Documents/04_code/rs_utils/data/0705/0705.shp")
        self.txt_save_path = os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils/building_data_txt")
        self.img_save_path = os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils/building_data_img")



    def test_aaa(self):
        """
        测试裁剪栅格数据
        """
        if not os.path.exists(self.txt_save_path):
            os.makedirs(self.txt_save_path)
        if not os.path.exists(self.img_save_path):
            os.makedirs(self.img_save_path)

        rs = RasterData.build_file(file_path=self.raster_build_file_path)
        shp = LayerData.build_file(file_path=self.shape_build_file_path)
        # print(rs.transform)
        left, bottom, right, top = rs.region
        output_shape = (3, 600, 600)
        print("left, bottom, right, top----", left, bottom, right, top)
        with rasterio.open(self.raster_build_file_path) as ds:
            pix_x = ds.transform.a
            pix_y = ds.transform.e
            tif_x = ds.transform.c
            tif_y = ds.transform.f
            pix_row = ds.width
            pix_col = ds.height

        shp_data = fiona.open(self.shape_build_file_path, 'r')

        print(self.raster_build_file_path)
        print(self.raster_build_file_path.split('/')[-1].split('.')[0])
        # 按照矢量图斑进行裁剪栅格数据
        for item in shp_data:

            array_item = np.array(item['geometry']['coordinates'][0])
            max_x, max_y = array_item.max(axis=0)
            min_x, min_y = array_item.min(axis=0)

            tif_left = min_x + (max_x-min_x)/2 - output_shape[1]*pix_x/2
            tif_right = min_x + (max_x-min_x)/2 + output_shape[1]*pix_x/2
            tif_top = min_y + (max_y-min_y)/2 - output_shape[2]*pix_y/2
            tif_bottom = min_y + (max_y-min_y)/2 + output_shape[2]*pix_y/2


            if tif_left<left or tif_right>right or tif_top > top or tif_bottom<bottom:
                continue
            # (self, left, bottom, right, top)
            print("tif_left, tif_bottom, tif_right, tif_top", tif_left, tif_bottom, tif_right, tif_top)
            crop_win = Rect(tif_left, tif_bottom, tif_right, tif_top)
            crop_rs = rs.crop(crop_win, out_shape=output_shape)
            print(crop_rs.profile['transform'])
            l = [crop_rs.profile['transform'].a, crop_rs.profile['transform'].b, crop_rs.profile['transform'].c, crop_rs.profile['transform'].d, crop_rs.profile['transform'].e,
                 crop_rs.profile['transform'].f, crop_rs.profile['transform'].g, crop_rs.profile['transform'].h, crop_rs.profile['transform'].i]
            transform_1 = (np.mat((np.asarray(l)).reshape(3, 3))).I

            data_coord = []
            for j in item['geometry']['coordinates'][0]:
                cc = np.mat([j[0], j[1], 1]).T
                out = (transform_1 * cc).A
                px = int(out[0][0])
                py = int(out[1][0])
                data_coord.append((px, py))


            save_name =self.raster_build_file_path.split('/')[-1].split('.')[0] + '_' + item['id'] +'.tif'
            # print(crop_rs.profile[''])
            print(crop_rs.profile)

            strr = save_name.split('.')[0] + ':'+'building'+':'+str(data_coord).replace('), (', ';').strip('[(').strip(')]')
            # strr = save_name.split('.')[0] + ':'+'building'+':'+str(item['geometry']['coordinates'][0]).replace('), (', ';').strip('[(').strip(')]')
            # strr = save_name + ':'+'building'+item['geometry']['coordinates'][0]
            print(strr)
            print(os.path.join(self.img_save_path, save_name))
            # crop_rs.save(os.path.join(self.img_save_path, save_name))
            txt_name = save_name.split('.')[0] +'.txt'
            txt_save = os.path.join(self.txt_save_path,txt_name)
            print(txt_save)
            with open(txt_save, 'w') as f:  # 设置文件对象
                f.write(strr)  # 将字符串写入文件中

        # 滑窗
        # print(pix_x*output_shape[1])
        # print(pix_y*output_shape[2])
        # for col in range(int(top), int(bottom), int(pix_y * output_shape[2])):  # 列
        #     if col+pix_y*output_shape[2] < bottom:
        #         col = int(bottom-pix_y * output_shape[2])
        #     for row in range(int(left), int(right), int(pix_x*output_shape[1])):  # 行
        #         if row + pix_x*output_shape[1] > right:
        #             row = int(right - pix_x*output_shape[1])
        #         crop_win = Rect(row, col+pix_y*output_shape[2], row+pix_y*output_shape[2], col)
        #         crop_rs = rs.crop(crop_win, out_shape=output_shape)
        # 矢量的矩形裁剪边界
        # crop_win = Rect(left + 1000, bottom + 1000, left + 1000 + output_shape[2], bottom + 1000 + output_shape[1])
        # crop_rs = rs.crop(crop_win, out_shape=output_shape)
        # crop_rs.save(os.path.join(self.test_dir, "test_crop_raster.tif"))

    def test_crop_raster(self):
        """
        测试裁剪栅格数据
        """
        rs = RasterData.build_file(file_path=self.raster_file_path)
        # print(rs.transform)
        left, bottom, right, top = rs.region
        print(rs.crss)
        print(rs.crs_wkt)
        # output_shape = (3,1000,1000)
        # crop_win = Rect(left+1000, bottom+1000, left+1000+output_shape[2], bottom+1000+output_shape[1])
        # crop_rs = rs.crop(crop_win,out_shape=output_shape)
        # crop_rs.save(os.path.join(self.test_dir,"test_crop_raster.tif"))

    def test_crop_raster11(self):
        """
        测试裁剪栅格数据
        """
        rs = RasterData.build_file(file_path=self.raster_file_path)
        # print(rs.transform)
        left, bottom, right, top = rs.region
        output_shape = (3,1000,1000)
        crop_win = Rect(left+1000, bottom+1000, left+1000+output_shape[2], bottom+1000+output_shape[1])
        crop_rs = rs.crop(crop_win,out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir,"test_crop_raster.tif"))

    def test_crop_rot30_raster(self):
        """
        测试裁剪栅格数据
        """
        rs = RasterData.build_file(file_path=self.raster_file_path)
        with rasterio.open(self.raster_file_path) as ds:
            print(f'反射变换参数（六参数模型）：\n {ds.transform}')
            pix_x = ds.transform.a
            pix_y = ds.transform.e

        left, bottom, right, top = rs.region
        output_shape = (3, 400, 400)
        center = (left + right) / 2, (bottom + top) / 2,
        height = 200 * pix_x
        width = 200 * abs(pix_y)
        angle = 0
        crop_win = RotateRect(center, height, width, angle)
        print("crop_win.TopWin=",crop_win.TopWin)
        crop_rs = rs.crop(crop_win, out_shape=output_shape)
        # print(crop_rs.profile)
        crop_rs.save(os.path.join(self.test_dir, "test_crop_rotate_raster_small_30.tif"))
        # rect_win = Rect(crop_win.left, crop_win.bottom, crop_win.right, crop_win.top)
        # crop_rs = rs.crop(rect_win, out_shape=output_shape)
        # crop_rs.save(os.path.join(self.test_dir, "test_crop_rotate_raster_big_30.tif"))

    def test_crop_rot45_raster(self):
        """
        测试裁剪栅格数据
        """
        rs = RasterData.build_file(file_path=self.raster_file_path)
        left, bottom, right, top = rs.region
        output_shape = (3, 2000, 2000)
        center = (left + right) / 2, (bottom + top) / 2,
        height = 2000
        width = 2000
        angle = 45
        crop_win = RotateRect(center, height, width, angle)
        crop_rs = rs.crop(crop_win, out_shape=output_shape)
        # print(crop_rs.profile)
        crop_rs.save(os.path.join(self.test_dir, "test_crop_rotate_raster_small_45.tif"))

        rect_win = Rect(crop_win.left, crop_win.bottom, crop_win.right, crop_win.top)
        crop_rs = rs.crop(rect_win, out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir, "test_crop_rotate_raster_big_45.tif"))

    def test_raster_coord_AToB(self):
        """
            测试坐标系转换
        """

        rs = RasterData.build_file(file_path=self.raster_file_CoordB_path)
        # rs.load(crs_wkt=CRS.from_epsg("32649"))
        rs.load(CRS.from_epsg("32649").to_wkt())
        left, bottom, right, top = rs.region
        output_shape = (3, 1000, 1500)

        crop_win = Rect(left + 1000, bottom + 1000, left + 1000 + output_shape[2], bottom + 1000 + output_shape[1])
        crop_rs = rs.crop(crop_win, out_shape=output_shape)
        crop_rs.save(os.path.join(self.test_dir, "test_crop_raster_CoordToB.tif"))
    # def test_get_all_models(self):
    #     """
    #     测试获取所有模型
    #     """
    #     # with self.app.app_context():
    #     self.assertEqual(res.errno, ErrNo.SUCCESS.get_code())