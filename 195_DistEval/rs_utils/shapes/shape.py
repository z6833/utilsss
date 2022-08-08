# !/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import deepcopy
from affine import Affine
from fiona import MemoryFile
from base.data_base import DataBase
from base.driver_base import DriverError
from rasters.raster import RasterData
from shapes.driver import ShapeFileDriver
from utilss.transform import build_transformer, trans_points_coordinate
from utilss.window import Rect, RotateRect
from rasterio import features
from rasterio.crs import CRS
import numpy as np
import math
# from itertools import tee
# from presto.presto_client import PrestoClient


def covert_wkt(wkt_str):
    if wkt_str is None:
        return
    else:
        crs = CRS.from_wkt(wkt_str)
        return crs


def transform_item(items, transformer=None, src_crs_wkt=None, dst_crs_wkt=None):
    """
    转换items里面所有feature的坐标系
    :param transformer: 坐标映射对象
    :param items: 图层里的feature
    :param src_crs_wkt: 图层原来坐标系
    :param dst_crs_wkt: 图层目的坐标系
    :return: 返回一个转换坐标系的列表
    """
    if transformer is None:
        assert src_crs_wkt is not None
        assert dst_crs_wkt is not None
        transformer = build_transformer(src_crs_wkt, dst_crs_wkt)
    ret_list = list()

    for item in items:
        new_item = deepcopy(item)
        if new_item["geometry"] == None:
            continue

        coordinates = new_item["geometry"]["coordinates"]
        if new_item["geometry"]["type"] == "Polygon":
            trans_coords = [trans_points_coordinate(coors, transformer).tolist() for coors in coordinates]
            new_item["geometry"]["coordinates"] = trans_coords
        else:
            trans_coords_multipolygon = list()
            for coordinate in coordinates:
                trans_coords = [trans_points_coordinate(coors, transformer).tolist() for coors in coordinate]
                trans_coords_multipolygon.append(trans_coords)
            new_item["geometry"]["coordinates"] = trans_coords_multipolygon

        ret_list.append(new_item)
    return ret_list


class Data:
    def __init__(self, file_path, data, profile):
        pass


class LayerData(DataBase):
    """
    图层数据类，表示一个图层
    """

    def __init__(self, file_path=None, data=None, profile=None, driver=None, layer_name=None):
        if driver is None:
            raise DriverError("没有指定驱动")
        self.profile = profile
        self.data = data
        # 属性筛选的过滤规则
        self.space_bbox = None
        self.attr_func = None
        self.mem_file = None
        self.layer_name = layer_name
        super(LayerData, self).__init__(data_uri=file_path, driver=driver)

    def set_filter(self, attr_filter_func=None, space_filter=None):
        """
        按照属性过滤,指定过滤规则(包含属性过滤规则和空间过滤规则)，在self.load中实际进行过滤.
        目前规则为一个字符串指定，也可以采取其他定义规则方式（待设计）
        :param attr_filter_func: 属性过滤函数
        :param space_filter: 空间过滤器，为一个bbox
        :return:
        """
        if self.space_bbox != space_filter:
            self.load_flag = False
            self.space_bbox = space_filter
        if self.attr_func != attr_filter_func:
            self.load_flag = False
            self.attr_func = attr_filter_func

    @property
    def crs(self):
        """
        当前矢量的坐标系的wkt表示
        todo 可尝试放到DataBase基类中，需验证基类的特性继承机制
        :return:
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

    def load(self, crs_wkt=None):
        """
        读取当前数据，需要根据坐标系和筛选条件载入，在crs为None时候设置crs，将数据写到data_handle中
        :param crs_wkt: 目标坐标系的wkt字符串
        """
        if crs_wkt:
            self.crs = crs_wkt
        if self.load_flag is True:
            return
        super().load()
        rect_bbox = None
        transformer = None
        load_handle = self.driver.handle
        raw_crs_wkt = load_handle.crs_wkt
        if self.space_bbox is not None:
            left, bottom, top, right = self.space_bbox
            rect_bbox = Rect(left, bottom, right, top)
        # print("raw_crs_wkt",raw_crs_wkt)
        # print(covert_wkt(raw_crs_wkt))
        # print(self.crs_wkt)
        if (covert_wkt(raw_crs_wkt) is not None) and (covert_wkt(self.crs_wkt) is not None) and covert_wkt(
                raw_crs_wkt) != self.crs_wkt:
            # 处理坐标转换
            dst_cts_wkt = self.crs_wkt
            if self.space_bbox is not None:
                invert_transform = build_transformer(dst_cts_wkt, raw_crs_wkt)
                rect_bbox = rect_bbox.trans_points(invert_transform)
            transformer = build_transformer(raw_crs_wkt, dst_cts_wkt)
        else:
            # 没有空间过滤器且坐标系不需要修改
            self.crs_wkt = raw_crs_wkt
        self._load_transform_filter_data(rect_bbox, transformer, self.attr_func)
        self.region = self.data_handle.bounds
        self.load_flag = True
        # self.data_shp = self.handle

    def _load_transform_filter_data_presto(self, rect_bbox, transformer, attr_filter):
        load_handle = self.driver.handle
        profile = deepcopy(load_handle.profile)
        profile["encoding"] = "utf-8"
        # 空间过滤
        if rect_bbox is not None:

            data_iter = load_handle.get_data_from_table_by_extents(bbox=rect_bbox.bounds())
        else:
            data_iter = load_handle.get_data_from_table_by_extents(bbox=rect_bbox.bounds())

    def _load_transform_filter_data(self, rect_bbox, transformer, attr_filter):
        """
        加载数据，处理坐标变换，空间过滤，属性过滤等操作，根据指定参数进行处理。
        :param rect_bbox: 空间过滤参数，None表示不进行空间过滤
        :param transformer: 坐标变换参数，None表示不进行坐标变换
        :param attr_filter: 属性过滤参数，None表示不进行属性过滤
        """
        load_handle = self.driver.handle
        profile = deepcopy(load_handle.profile)
        profile["encoding"] = "utf-8"
        # profile["encoding"] = "GBK"
        # 空间过滤
        if rect_bbox is not None:
            data_iter = load_handle.filter(bbox=rect_bbox.bounds())
        else:
            data_iter = load_handle.filter()
        # 属性过滤
        if attr_filter is not None:
            data_items = list()
            for item in data_iter:
                if attr_filter(item) is True:
                    data_items.append(item)
        else:
            data_items = list(data_iter)
        if transformer is not None:
            data_items = transform_item(data_items, transformer=transformer)
            profile["crs_wkt"] = self.crs_wkt
            if "crs" in profile:
                del profile["crs"]
        # 写文件句柄，使用虚拟文件技术
        self.mem_file = MemoryFile()
        self.data_handle = self.mem_file.open(**profile)

        # print("____________",type(data_items))
        self.data_handle.writerecords(data_items)
        # 数据模型改为只读
        self.data_handle.mode = "r"

    def shape2raster(self):
        """
        将矢量转化为栅格，此接口预留，目前切片没用
        :return:
        """
        raise NotImplementedError

    def save(self, uri):
        """
        保存文件，根据driver来指定保存数据类型，根据uri表示资源的文件类型（本地文件，hdfs等）
        :param uri: 保存的资源名
        :return:
        """
        # super().save(uri)
        self.load()
        super().save(uri=uri)

    def get_angle_coord(self, X, Y, c_x, c_y, angle):
        # 计算旋转之后的投影坐标的位置，返回旋转之后的投影坐标
        # X, Y 为旋转之前
        # c_x ,c_y旋转中心点

        # 计算中心投影坐标
        x_a = (X - c_x) * math.cos(math.radians(-angle)) - (Y - c_y) * math.sin(math.radians(-angle)) + c_x
        y_a = (X - c_x) * math.sin(math.radians(-angle)) + (Y - c_y) * math.cos(math.radians(-angle)) + c_y

        return x_a, y_a

    def crop(self, rect_obj, out_shape=None, listFeature=None, feature=None):
        """
        对图层进行裁剪，当out_shape为None时，剪裁结果为空间区域中的矢量；
        当out_shape不为None，剪裁结果为区域中的栅格
        当listFeature不为None时，进行多分类的mask生成
        :param rect_obj:表示裁剪的矩形切片区域对象（可以是正矩形或者旋转矩形对象）
        :param out_shape:输出栅格的尺寸(channel,height,width)，None表示与原来栅格尺寸一致
        :return:当out_shape为None，返回矢量图层对象，当out_shape不为None，返回栅格数据对象

        """
        self.load()
        if isinstance(rect_obj, RotateRect):
            if out_shape:

                # 保存为栅格
                data_iter = self.data_handle.filter(bbox=rect_obj.bounds())

                c, y_res, x_res = out_shape
                # 获取角点坐标（外接矩阵尺寸）
                nW = int(
                    (y_res * math.sin(math.radians(rect_obj.angle)) + (x_res * math.cos(math.radians(rect_obj.angle)))))
                nH = int(
                    (y_res * math.cos(math.radians(rect_obj.angle)) + (x_res * math.sin(math.radians(rect_obj.angle)))))

                y_pixel_size = (rect_obj.top - rect_obj.bottom) / nH
                x_pixel_size = (rect_obj.right - rect_obj.left) / nW

                transform = Affine(x_pixel_size, 0.0, rect_obj.left, 0.0, - y_pixel_size, rect_obj.top)
                if listFeature:
                    # cur_items,second_it = tee(data_iter)
                    # dictFeature = dict()
                    # listFeature = []
                    # for item1 in second_it:
                    #     if item1['properties']['DLMC'] in dictFeature:
                    #         dictFeature[item1['properties']['DLMC']] += 1
                    #     else:
                    #         dictFeature[item1['properties']['DLMC']] = 1
                    # for i in dictFeature:
                    #     listFeature.append(i)
                    image = features.rasterize(
                        ((item["geometry"],
                          listFeature[item['properties'][feature]] if item['properties'][feature] in listFeature else 0)
                         for item in data_iter),
                        transform=transform, out_shape=(y_res, x_res))
                else:
                    image = features.rasterize(((item["geometry"], 1) for item in data_iter), transform=transform,
                                               out_shape=(nH, nW))

                profile = dict()
                profile["transform"] = transform
                # profile["driver"] = 'GTiff'
                # profile['resampling'] = Resampling.cubic
                profile['crs'] = CRS.from_wkt(self.crs_wkt)
                profile['height'] = nH
                profile['width'] = nW
                profile['count'] = 1
                profile['dtype'] = 'uint8'
                shp_data = RasterData.build_data(np.array([image]), profile)
                # 将外接矩形进行旋转裁剪
                crop_win = RotateRect(rect_obj.center, rect_obj.height, rect_obj.width, rect_obj.angle)
                out_shape_new = (1, out_shape[1], out_shape[2])
                crop_rs = shp_data.crop(crop_win, out_shape=out_shape_new)

                return crop_rs

            else:
                # 返回剪切的矢量对象（与当前有交集的都可以）
                # 旋转矩形需要根据现有情况进行旋转
                data_iter = self.data_handle.filter(bbox=rect_obj.bounds())
                return LayerData.build_data(list(data_iter), self.data_handle.profile)

        else:
            if out_shape:
                # 返回切分的栅格对象
                c, y_res, x_res = out_shape
                y_pixel_size = (rect_obj.top - rect_obj.bottom) / y_res
                x_pixel_size = (rect_obj.right - rect_obj.left) / x_res

                transform = Affine(x_pixel_size, 0.0, rect_obj.left, 0.0, - y_pixel_size, rect_obj.top)

                data_iter = self.data_handle.filter(bbox=rect_obj.bounds())
                if listFeature:
                    # cur_items,second_it = tee(cur_items)
                    # dictFeature = dict()
                    # listFeature = []
                    # for item1 in second_it:
                    #     if item1['properties']['DLMC'] in dictFeature:
                    #         dictFeature[item1['properties']['DLMC']] += 1
                    #     else:
                    #         dictFeature[item1['properties']['DLMC']] = 1
                    # for i in dictFeature:
                    #     listFeature.append(i)
                    # image = features.rasterize(
                    #         ((item["geometry"], listFeature.index(item['properties']['DLMC']) + 1) for item in cur_items ), transform=transform,out_shape=(y_res, x_res))
                    image = features.rasterize(
                        ((item["geometry"],
                          listFeature[item['properties'][feature]] if item['properties'][feature] in listFeature else 0)
                         for item in data_iter),
                        transform=transform, out_shape=(y_res, x_res))

                    # for item in data_iter:
                    #     print(listFeature[item['properties'][feature]])
                    print(listFeature)
                else:
                    # print("transform",transform)
                    # print("data_iter",data_iter)
                    # for item in data_iter:
                    #     print(item)
                    #     print('1111')

                    image = features.rasterize(
                        ((item["geometry"], 1) for item in data_iter), transform=transform, out_shape=(y_res, x_res))

                profile = dict()
                profile["transform"] = transform
                profile["driver"] = 'GTiff'
                # profile['resampling'] = Resampling.cubic
                profile['crs'] = CRS.from_wkt(self.crs_wkt)
                profile['height'] = y_res
                profile['width'] = x_res
                profile['count'] = 1
                profile['dtype'] = 'uint8'
                return RasterData.build_data(np.array([image]), profile)
            else:

                # 返回剪切的矢量对象（与当前有交集的都可以）
                # 旋转矩形需要根据现有情况进行旋转

                data_iter = self.data_handle.filter(bbox=rect_obj.bounds())
                return LayerData.build_data(list(data_iter), self.data_handle.profile)

    @classmethod
    def build_file(cls, file_path, driver=None, layer_name=None):
        """
        以文件的方式创建栅格数据对象
        :param layer_name: 层的名称
        :param driver: 指定的驱动对象
        :param file_path: 文件路径
        :return: 栅格数据对象
        """
        # 暂时仅支持shapefile驱动
        driver = ShapeFileDriver()
        ret_obj = cls(file_path=file_path, driver=driver, layer_name=layer_name)
        return ret_obj

    @classmethod
    def build_data(cls, data, profile, driver=None, layer_name=None):
        """
        以数据和元数据描述的方式创建栅格数据对象
        :param layer_name: 层的名称
        :param driver: 指定的驱动对象
        :param data: data格式为c,h,w
        :param profile: 元数据描述字典
        :return:
        """
        # 暂时仅支持shapefile驱动
        driver = ShapeFileDriver()
        ret_obj = cls(data=data, profile=profile, driver=driver, layer_name=layer_name)
        return ret_obj

    def clear(self):
        """
        资源情况，删除临时存储文件
        """
        if self.data_handle is not None:
            self.data_handle.close()
        if self.mem_file is not None:
            self.mem_file.close()
        self.space_bbox = None
        self.attr_func = None
        self.mem_file = None
        self.driver.close()
