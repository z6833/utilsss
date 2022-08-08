from pyproj import CRS
from pyproj import Transformer
import numpy as np


def build_transformer(src_crs_wkt: str, dst_crs_wkt: str) -> Transformer:
    """
    创建坐标系转换对象transformer，用于针对源坐标系到目的坐标系的坐标转换
    :param src_crs_wkt: 源坐标系的wkt表示方法
    :param dst_crs_wkt: 目的坐标系的wkt表示方法
    :return: 返回坐标转换对象
    """
    src_crs = CRS.from_wkt(src_crs_wkt)
    dst_crs = CRS.from_wkt(dst_crs_wkt)
    return Transformer.from_crs(src_crs, dst_crs, always_xy=True)


def trans_points_coordinate(point_arr: np.ndarray, transformer: Transformer) -> np.ndarray:
    """
    对一个点集合进行坐标转换，支持批量坐标转换
    :param point_arr: 为（N,2）的array数组，同时对N个点进行坐标转换
    :param transformer: 坐标转换对象
    :return: 经过坐标转换后的点集合，为（N,2）,顺序与出去点集保持一致
    """
    # print("----"*8)
    #
    # print("point_arr------",point_arr)
    # print("len---",len(point_arr))
    point_arr = np.array(point_arr)
    # print("point_arr------",point_arr)
    # print(point_arr)
    xx = point_arr[:, 0]
    yy = point_arr[:, 1]

    # print("xxxx---",xx)
    # print("yyyy---",yy)


    new_xx, new_yy = transformer.transform(xx, yy)
    return np.stack([new_xx, new_yy]).T
