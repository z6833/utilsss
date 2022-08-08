# !/usr/bin/env python
# -*- coding: utf-8 -*-
from ..rasters.raster import RasterData
from ..shapes.shape import LayerData
from ..utils.window import Rect, RotateRect


class Cropper:
    """
    切片类，管理一组影像和栅格的切片，同时对对象中的所有栅格和影像进行切片，
    按照顺序返回切片的结果对象。
    """
    def __init__(self, crs_wkt):
        """
        初始化需要设置在哪个坐标系下进行切片
        :param crs_wkt: 待切片的坐标系
        """

        self.crop_list = list()
        self.crs_wkt = None
        self.crop_area = None

    def add_crop_data(self, data):
        """
        增加待切片的数据，可以是LayerData或者RasterData对象
        todo 这里可以设计一个两者共同的基类，从而可以增加类型判断
        :param data: LayerData或者RasterData对象(DataBase)
        :return:
        """

        self.crop_list.append(data)

    def set_crop_area(self, layer_obj=None):
        """
        设定需要切片的区域，掩膜与切出来的栅格进行数值交集操作，
        并且对当前所有数据进行载入，此为切分调用必须进行的步骤
        todo 增加表示量对此函数调用进行控制，必须进行此函数调用后才能进行切片操作
        :param layer_obj: 掩膜的矢量，图层中所有矢量包含的区域为掩膜
        """
        self.crop_area = layer_obj

    def set_crs(self, dst_wkt):
        self.crs_wkt = dst_wkt
        for data_obj in self.crop_list:
            data_obj.load_file(crs_wkt=dst_wkt)

    def crop(self, rect_obj, out_shape, mask_flag=True, crs_flag=True):
        """
        对对象中的左右数据进行切片，
        :param rect_obj:表示裁剪的矩形切片区域对象（可以是正矩形或者旋转矩形对象）
        :param rect_obj: 表示裁剪的矩形切片区域对象（可以是正矩形或者旋转矩形对象）
        :param mask_flag: True表示切片为语义分割样本（mask），False为目标检测样本（矢量坐标）
        :param crs_flag: 设定是否保存切片的坐标系，True为保存地理坐标系，False表示仅保存当前像素坐标
        :return:输出为内部所有数据指定位置（每个数据相同）的切片结果对象
        """
        if self.crs_wkt is None:
            raise RuntimeError("没有指定裁剪的坐标系")
        ret_datas = list()
        # 返回当前所有数据对应的切片对象
        if self.crop_area is not None:
            mask_area = self.crop_area.crop(rect_obj.left, rect_obj.bottom, rect_obj.right, rect_obj.top, out_shape=out_shape)


        for data_obj in self.crop_list:
            # 处理矢量
            if isinstance(data_obj, LayerData):

                out_shape2 = (1, out_shape[1], out_shape[2])
                crop_layer = data_obj.crop(rect_obj, out_shape=out_shape2)
                ret_datas.append(crop_layer)

            # 处理栅格
            else:
                crop_raster = data_obj.crop(rect_obj, out_shape=out_shape)
                # 当前只考虑了语义分割用的mask裁剪，对于目标检测的mask没做处理
                ret_datas.append(crop_raster)


        return ret_datas


if __name__ == "__main__":
    pass
