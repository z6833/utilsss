import os
import sys
import unittest

from osgeo import gdal
from rasters.raster import RasterData
from utils.window import Rect, RotateRect
import rasterio

class TestEEEE(unittest.TestCase):
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
        self.ecw_file_path = os.path.join(root_path,"/data1/河南省商丘市天地图10_421_80.ecw")
        self.tif_file_path = os.path.join(root_path,"/data1/10_422_79.tif")
        self.out_ecw_file_path = os.path.join(root_path, "/data1/out")



    def test_crop_ecw(self):
        """
        测试裁剪栅格数据
        """

        ecw = RasterData.build_file(file_path=self.ecw_file_path)
        dataset = gdal.Open(self.ecw_file_path)
        if dataset == None:
            print("文件无法打开")
        im_width = dataset.RasterXSize  # 栅格矩阵的列数
        im_height = dataset.RasterYSize  # 栅格矩阵的行数
        print("栅格矩阵的列数", im_width)
        print("栅格矩阵的行数",im_height)
        im_bands = dataset.RasterCount  # 波段数
        print("波段数",im_bands)

        # rs = RasterData.build_file(file_path=self.raster_file_path)
        # print(rs.transform)

        with rasterio.open(self.ecw_file_path) as ds:
            print('该栅格数据的基本数据集信息（这些信息都是以数据集属性的形式表示的）：')
            print(f'数据格式：{ds.driver}')
            print(f'波段数目：{ds.count}')
            print(f'影像宽度：{ds.width}')
            print(f'影像高度：{ds.height}')
            print(f'地理范围：{ds.bounds}')
            print(f'反射变换参数（六参数模型）：\n {ds.transform.a}')
            print(f'投影定义：{ds.crs}')
        left, bottom, right, top = ecw.region
        print("left, bottom, right, top",left, bottom, right, top)
        output_shape = (3, 1000, 1000)
        print(1000*ds.transform.a)
        print((1000 + output_shape[1])*ds.transform.e)
        crop_win = Rect(left , bottom , left + 1000*ds.transform.a, bottom- 1000*ds.transform.e)
        crop_rs = ecw.crop(crop_win, out_shape=output_shape)
        if not os.path.exists(self.out_ecw_file_path):
            os.makedirs(self.out_ecw_file_path)
        crop_rs.save(os.path.join(self.out_ecw_file_path, "test_crop_raster.tif"))
        # im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
        # im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
        # im_proj = dataset.GetProjection()  # 获取投影信息
        # im_blueBand = im_data[0, 0:im_height, 0:im_width]  # 获取蓝波段
        # im_greenBand = im_data[1, 0:im_height, 0:im_width]  # 获取绿波段
        # im_redBand = im_data[2, 0:im_height, 0:im_width]  # 获取红波段
        # im_nirBand = im_data[3, 0:im_height, 0:im_width]  # 获取近红外波段





