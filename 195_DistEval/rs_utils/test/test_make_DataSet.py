import os
import sys

import fiona
import numpy as np
print (sys.path)
import rasterio
import unittest
from rasterio.crs import CRS
import math
from rasters.raster import RasterData
from utils.window import Rect, RotateRect
from shapes.shape import LayerData

class TestmakeDataSet(unittest.TestCase):
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
        self.raster_file_CoordB_path = os.path.join(root_path,"data/projected/cage_tif_proj.tif")
        self.proj_raster_file_path = os.path.join(root_path,"data/projected/cage_tif_proj.tif")
        self.shape_file_path = os.path.join(root_path, "data/cage_dataset_shp48/cage_bbox_shp48.shp")

        # self.raster_build_file_path=os.path.join(root_path,"/Users/zhangshirun/fsdownload/070302增城区永宁街道.tif")
        self.raster_build_file_path=os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils/data/0615/061502_花都区秀全街道.tif")
        self.raster_build_file_path_oil=os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils_master/rs_utils/data/oil/4197.0-417.0.tif")
        # self.shape_build_file_path = os.path.join(root_path, "/Users/zhangshirun/fsdownload/0703.shp")
        self.shape_build_file_path = os.path.join(root_path, "/Users/zhangshirun/Documents/04_code/rs_utils/data/0615/0617.shp")
        self.shape_build_file_path_oil = os.path.join(root_path, "/Users/zhangshirun/Documents/04_code/rs_utils_master/rs_utils/data/oil/oil_well_train.shp")
        self.txt_save_path = os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils_master/building_data_txt01")
        self.img_save_path = os.path.join(root_path,"/Users/zhangshirun/Documents/04_code/rs_utils_master/building_data_img01")



    def test_spot(self):
        """
        数据集图斑裁剪
        遍历所有的Polygon获得投影坐标
        对应tif坐标范围，里面所以对Polygon进行保存为txt
        目前是对坐标范围全在tif里面的才进行保存
        """
        if not os.path.exists(self.txt_save_path):
            os.makedirs(self.txt_save_path)
        if not os.path.exists(self.img_save_path):
            os.makedirs(self.img_save_path)

        rs = RasterData.build_file(file_path=self.raster_build_file_path_oil)
        rs.load(CRS.from_epsg("4326").to_wkt())
        shp = LayerData.build_file(file_path=self.shape_build_file_path_oil)
        left, bottom, right, top = rs.region
        output_shape = (3, 600, 600)
        with rasterio.open(self.raster_build_file_path_oil) as ds:
            pix_x = ds.transform.a
            pix_y = ds.transform.e

        shp_data = fiona.open(self.shape_build_file_path_oil, 'r')
        num = 0
        # print(self.raster_build_file_path)
        # print(self.raster_build_file_path.split('/')[-1].split('.')[0])
        # 按照矢量图斑进行裁剪栅格数据
        for item in shp_data:
            num += 1  # 输出ID编号
            array_item = np.array(item['geometry']['coordinates'][0])
            max_x, max_y = array_item.max(axis=0)
            min_x, min_y = array_item.min(axis=0)
            tif_left = min_x + (max_x-min_x)/2 - output_shape[1]*pix_x/2
            tif_right = min_x + (max_x-min_x)/2 + output_shape[1]*pix_x/2
            tif_top = min_y + (max_y-min_y)/2 - output_shape[2]*pix_y/2
            tif_bottom = min_y + (max_y-min_y)/2 + output_shape[2]*pix_y/2
            # 如果裁剪框没有交集跳过
            # if tif_left<left and tif_right>right and tif_top>top and tif_bottom<bottom:
            #     continue
            if tif_left<left or tif_right>right or tif_top>top or tif_bottom<bottom:
                continue
            # (self, left, bottom, right, top)
            crop_win = Rect(tif_left, tif_bottom, tif_right, tif_top)
            crop_rs = rs.crop(crop_win, out_shape=output_shape)
            crop_shp = shp.crop(crop_win)
            save_name = self.raster_build_file_path_oil.split('/')[-1].split('.')[0] + '_' + str(num) + '.tif'
            crop_rs.save(os.path.join(self.img_save_path, save_name))
            # 投影坐标转像素坐标,保存为txt
            txt_name = save_name.split('.')[0] + '.txt'
            txt_save = os.path.join(self.txt_save_path, txt_name)
            l = [crop_rs.profile['transform'].a, crop_rs.profile['transform'].b, crop_rs.profile['transform'].c,
                 crop_rs.profile['transform'].d, crop_rs.profile['transform'].e,
                 crop_rs.profile['transform'].f, crop_rs.profile['transform'].g, crop_rs.profile['transform'].h,
                 crop_rs.profile['transform'].i]
            transform_1 = (np.mat((np.asarray(l)).reshape(3, 3))).I
            data_coord = []
            # 遍历一张tif中的所有Polygon
            for K in range(len(crop_shp.data)):
                for item in crop_shp.data[K]['geometry']['coordinates'][0]:
                    cc = np.mat([item[0], item[1], 1]).T
                    out = (transform_1 * cc).A
                    px = int(out[0][0])
                    py = int(out[1][0])
                    data_coord.append((px, py))
                # 保存shp中的矢量信息为txt
                strr = save_name.split('.')[0] + ':' + 'building' + ':' + str(data_coord).replace('), (', ';').strip(
                    '[(').strip(')]')
                # print(txt_save)
                with open(txt_save, 'a+') as f:  # 设置文件对象
                    f.write(str(strr) + '\n')  # 将字符串写入文件中
                data_coord = []

    def test_slide_win(self):
        """
        测试裁剪栅格数据
        1、滑窗遍历整个tif，得到地理范围
        2、判断地理范围内是否存在矢量信息
        3、保存具有矢量信息的tif

        针对矢量和栅格数据集进行批量裁剪
        setUp
        """
        if not os.path.exists(self.txt_save_path):
            os.makedirs(self.txt_save_path)
        if not os.path.exists(self.img_save_path):
            os.makedirs(self.img_save_path)
        rs = RasterData.build_file(file_path=self.raster_build_file_path)

        shp = LayerData.build_file(file_path=self.shape_build_file_path)
        left, bottom, right, top = rs.region
        output_shape = (4, 600, 600)
        with rasterio.open(self.raster_build_file_path) as ds:
            pix_x = ds.transform.a
            pix_y = ds.transform.e
        num = 0
        # 滑窗
        # 往下遍历有多少个格子
        cooo = math.ceil((bottom-top)/(pix_y * output_shape[2]))
        # 往右遍历有多少个格子
        rooo = math.ceil((right-left)/(pix_x*output_shape[1]))
        win_top = top

        for col in range(cooo):  # 列遍历
            # 当滑窗溢出时，平移到边界
            win_left = left
            if col == cooo-1:
                win_top = bottom - pix_y * output_shape[2]
            for row in range(rooo):  # 行遍历
                # 当滑窗溢出时，平移到边界
                if row == rooo -1:
                    win_left = right - pix_x*output_shape[1]
                # def __init__(self, left, bottom, right, top)
                crop_win = Rect(win_left, win_top+pix_y*output_shape[2], win_left+pix_x*output_shape[1], win_top)
                crop_shp = shp.crop(crop_win)
                # 滑窗往右平移一格
                win_left += pix_x*output_shape[1]
                # 2、判断地理范围内是否存在矢量信息
                num += 1
                if crop_shp.data == []:
                    continue
                # 保存tif
                save_name = self.raster_build_file_path.split('/')[-1].split('.')[0] + '_' + str(num) + '.tif'
                crop_rs = rs.crop(crop_win, out_shape=output_shape)
                crop_rs.save(os.path.join(self.img_save_path, save_name))

                # 投影坐标转像素坐标,保存为txt
                txt_name = save_name.split('.')[0] + '.txt'
                txt_save = os.path.join(self.txt_save_path, txt_name)
                l = [crop_rs.profile['transform'].a, crop_rs.profile['transform'].b, crop_rs.profile['transform'].c,
                     crop_rs.profile['transform'].d, crop_rs.profile['transform'].e,
                     crop_rs.profile['transform'].f, crop_rs.profile['transform'].g, crop_rs.profile['transform'].h,
                     crop_rs.profile['transform'].i]
                transform_1 = (np.mat((np.asarray(l)).reshape(3, 3))).I
                data_coord = []
                # 遍历一张tif中的所有Polygon，并转换为像素坐标
                for K in range(len(crop_shp.data)):
                    for item in crop_shp.data[K]['geometry']['coordinates'][0]:
                        cc = np.mat([item[0], item[1], 1]).T
                        out = (transform_1 * cc).A
                        px = int(out[0][0])
                        py = int(out[1][0])
                        data_coord.append((px, py))
                    # 保存shp中的矢量信息为txt
                    strr = save_name.split('.')[0] + ':' + 'building' + ':' + str(data_coord).replace('), (', ';').strip('[(').strip(')]')
                    with open(txt_save, 'a+') as f:  # 设置文件对象
                        f.write(str(strr)+'\n')  # 将字符串写入文件中
                    data_coord = []
            # 滑窗往下平移一格
            win_top += pix_y * output_shape[2]

    def test_spot_Rotate(self):
        """
        数据集图斑裁剪
        遍历所有的Polygon获得投影坐标
        对应tif坐标范围，里面所以对Polygon进行保存为txt
        目前是对坐标范围全在tif里面的才进行保存
        """
        print(self.raster_build_file_path_oil)
        angle = 45
        if not os.path.exists(self.txt_save_path):
            os.makedirs(self.txt_save_path)
        if not os.path.exists(self.img_save_path):
            os.makedirs(self.img_save_path)

        rs = RasterData.build_file(file_path=self.raster_build_file_path_oil)
        rs.load(CRS.from_epsg("4326").to_wkt())
        #4527
        shp = LayerData.build_file(file_path=self.shape_build_file_path_oil)
        left, bottom, right, top = rs.region
        output_shape = (3, 600, 600)
        with rasterio.open(self.raster_build_file_path_oil) as ds:
            pix_x = ds.transform.a
            pix_y = ds.transform.e
            print("ds.transform",ds.transform)

        shp_data = fiona.open(self.shape_build_file_path_oil, 'r')
        num = 0
        # print(self.raster_build_file_path)
        # print(self.raster_build_file_path.split('/')[-1].split('.')[0])
        # 按照矢量图斑进行裁剪栅格数据
        for item in shp_data:
            num += 1  # 输出ID编号
            # print("item['geometry']['coordinates'][0]",item['geometry']['coordinates'][0])
            array_item = np.array(item['geometry']['coordinates'][0])
            max_x, max_y = array_item.max(axis=0)
            min_x, min_y = array_item.min(axis=0)

            # 外接矩形边长
            nW = int((output_shape[2] * math.sin(math.radians(angle)) + (output_shape[1] * math.cos(math.radians(angle)))))
            nH = int((output_shape[2] * math.cos(math.radians(angle)) + (output_shape[1] * math.sin(math.radians(angle)))))

            tif_left = min_x + (max_x-min_x)/2 - nW*pix_x/2
            tif_right = min_x + (max_x-min_x)/2 + nW*pix_x/2
            tif_top = min_y + (max_y-min_y)/2 - nH*pix_y/2
            tif_bottom = min_y + (max_y-min_y)/2 + nH*pix_y/2

            center = (tif_left + tif_right) / 2, (tif_bottom + tif_top) / 2,

            # crop_rs = rs.crop(crop_win, out_shape=output_shape)


            # 如果裁剪框没有交集跳过
            # if tif_left<left and tif_right>right and tif_top>top and tif_bottom<bottom:
            #     continue
            if tif_left<left or tif_right>right or tif_top>top or tif_bottom<bottom:
                continue
            # (self, left, bottom, right, top)
            # crop_win = Rect(tif_left, tif_bottom, tif_right, tif_top)
            crop_win = RotateRect(center, output_shape[2] * abs(pix_y), output_shape[1] * pix_x, angle)
            crop_rs = rs.crop(crop_win, out_shape=output_shape)
            crop_shp = shp.crop(crop_win)
            save_name = self.raster_build_file_path_oil.split('/')[-1].split('.')[0] + '_' + str(num) + '.tif'
            crop_rs.save(os.path.join(self.img_save_path, save_name))
            # 投影坐标转像素坐标,保存为txt
            txt_name = save_name.split('.')[0] + '.txt'
            txt_save = os.path.join(self.txt_save_path, txt_name)
            l = [crop_rs.profile['transform'].a, crop_rs.profile['transform'].b, crop_rs.profile['transform'].c,
                 crop_rs.profile['transform'].d, crop_rs.profile['transform'].e,
                 crop_rs.profile['transform'].f, crop_rs.profile['transform'].g, crop_rs.profile['transform'].h,
                 crop_rs.profile['transform'].i]
            transform_1 = (np.mat((np.asarray(l)).reshape(3, 3))).I
            data_coord = []
            # 遍历一张tif中的所有Polygon
            for K in range(len(crop_shp.data)):
                for item in crop_shp.data[K]['geometry']['coordinates'][0]:
                    cc = np.mat([item[0], item[1], 1]).T
                    out = (transform_1 * cc).A
                    px = int(out[0][0])
                    py = int(out[1][0])
                    data_coord.append((px, py))
                # 保存shp中的矢量信息为txt
                strr = save_name.split('.')[0] + ':' + 'building' + ':' + str(data_coord).replace('), (', ';').strip(
                    '[(').strip(')]')
                # print(txt_save)
                with open(txt_save, 'a+') as f:  # 设置文件对象
                    f.write(str(strr) + '\n')  # 将字符串写入文件中
                data_coord = []



    def test_zuobaioxi(self):
        with rasterio.open(self.raster_build_file_path_oil) as ds:
            print("ds.crs", ds.crs.to_wkt())
            print("ds.crs", ds.crs)
            print(type(ds.crs))
        # rs = RasterData.build_file(file_path=self.raster_build_file_path_oil)
        # rs.load(crs_wkt=CRS.from_epsg("32649"))
        # rs.load(CRS.from_epsg("4326").to_wkt())
        # rs.load(CRS.from_epsg("4326").to_wkt())
        # rs.save(os.path.join(self.test_dir, "test_rotate_crop_shape_mask2.tif"))
        # shp_data = fiona.open(self.shape_build_file_path_oil, 'r')
        # print("shp_data.crs",shp_data.crs['init'])
        # print(type(shp_data.crs['init']))

    def test_zuobaioxi2(self):
        shp_data = fiona.open(self.shape_build_file_path_oil, 'r')
        print("shp_data.crs", shp_data.crs['init'].split(':')[1])
        print("shp_data.crs", shp_data.crs)
        print(type(str(shp_data.crs['init'].split(':'))))
        print(type(str(shp_data.crs)))



