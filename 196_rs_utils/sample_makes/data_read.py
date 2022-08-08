import datetime

import numpy as np
from utilss.window import Rect, RotateRect
import random
from shapely.geometry import shape, Polygon


# 判断缓冲区是否包含窗口
def filtrate_polygon(crop_win, polygons):
    # 窗口Polygon
    polygon_win = Polygon([(crop_win.left, crop_win.top),
                           (crop_win.right, crop_win.top),
                           (crop_win.right, crop_win.bottom),
                           (crop_win.left, crop_win.bottom),
                           (crop_win.left, crop_win.top)])

    if polygons.contains(polygon_win):
        return True
    else:
        return False


def precision_buffer_restraint(shp_buffer, buffer_field, list_buffer_name):
    """
    根据缓冲区shp，返回一个可以精确过滤polygon的列表
    shp_buffer ： 缓冲区文件的shp
    buffer_field: 过滤属性字段名称
    list_buffer_name： 过滤字段值列表
    """
    out_polygons = []
    if buffer_field:
        list_buffer_ = list_buffer_name
        for item in shp_buffer.data_handle:
            if item['properties'][buffer_field] in list_buffer_:
                out_polygons.append(shape(item['geometry']))
        return out_polygons
    else:
        for item in shp_buffer.data_handle:
            out_polygons.append(shape(item['geometry']))
        return out_polygons


# 约束范围polygon得到范围
def polygon_to_region(polygon_in):
    # return polygon的范围
    polygon_ = Polygon(polygon_in)
    return polygon_.bounds


# 全遍历过滤图斑
def buffer_restraint(crop_win, shp_buffer, ):
    # 窗口Polygon
    polygon_win = Polygon([(crop_win.left, crop_win.top),
                           (crop_win.right, crop_win.top),
                           (crop_win.right, crop_win.bottom),
                           (crop_win.left, crop_win.bottom),
                           (crop_win.left, crop_win.top)])
    # 通过
    polygon_pass = False
    for item in shp_buffer.data_handle:
        # polygon_buffer = Polygon(item['geometry']['coordinates'][0])
        polygon_buffer = shape(item["geometry"])
        if polygon_buffer.contains(polygon_win):
            polygon_pass = True
    # 不包含在里面进行过滤
    if not polygon_pass:
        return False
    return True


# 旋转窗口
def crop_win_revolve(win_left, win_top, pix_x, pix_y, angle, out_shape):
    if angle is True:
        angle = random.choice([30, 45, 60, 75])
    # 旋转中心
    center = win_left + pix_x * out_shape[0] / 2, win_top + pix_y * out_shape[1] / 2,
    # 旋转窗口
    crop_win = RotateRect(center, out_shape[1] * abs(pix_y), out_shape[0] * pix_x, angle)
    return crop_win


# 抖动窗口
def crop_win_dithering(win_left, win_top, pix_x, pix_y, out_shape):
    # 偏移的像素量，会根据分辨率转换到对应的地理范围
    dithering_x = random.choice([-50, -100, -150, 50, 100, 150])
    dithering_y = random.choice([-50, -100, -150, 50, 100, 150])
    win_left += dithering_x * pix_x
    win_top += dithering_y * abs(pix_y)
    win_bottom = win_top + pix_y * out_shape[1]
    win_right = win_left + pix_x * out_shape[0]
    crop_win = Rect(win_left, win_bottom, win_right, win_top)
    return crop_win


# 普通矩形窗口
def crop_win_rectangle(win_left, win_bottom, pix_x, pix_y, out_shape):
    win_top = win_bottom + abs(pix_y) * out_shape[1]
    win_right = win_left + pix_x * out_shape[0]
    # 创建普通矩形窗口
    crop_win = Rect(win_left, win_bottom, win_right, win_top)
    return crop_win


# 滑窗数据读取
def cut_sliding_win(left, right, top, bottom, win_width, win_height, row_step, col_step, shp_buffer=None,
                    buffer_field=None, list_buffer_name=None):
    row_num = int(np.ceil((top - bottom - win_height) / row_step)) + 1
    col_num = int(np.ceil((right - left - win_width) / col_step)) + 1
    list_dot = list()
    # 是否进行缓冲区过滤
    if shp_buffer is None:
        for row in range(row_num):
            y = bottom + row * row_step
            if row == row_num - 1:
                y = top - win_height
            for col in range(col_num):
                x = left + col * col_step
                if col == col_num - 1:
                    x = right - win_width
                list_dot.append((x, y))
        return list_dot
    else:
        # 1、获得小区域的过滤图斑
        items = precision_buffer_restraint(shp_buffer, buffer_field, list_buffer_name)
        # 对所有的小区域进行遍历
        for item in items:
            # 滑动窗口的起始位置为小区域的位置
            lefts, bottoms, rights, tops = item.bounds
            # 行遍历次数
            row_num = int(np.ceil((tops - bottoms - win_height) / row_step)) + 2
            # 列遍历次数
            col_num = int(np.ceil((rights - lefts - win_width) / col_step)) + 2
            for row in range(row_num):
                y = bottoms + row * row_step
                if row == row_num - 1:
                    y = tops - win_height
                for col in range(col_num):
                    x = lefts + col * col_step
                    if col == col_num - 1:
                        x = rights - win_width
                    list_dot.append((x, y))
        return list_dot
    # return iter(list_dot)


# 图斑数据读取
def cut_spots(shp_data, pix_x, pix_y, out_shape):
    """
    得到图斑的bbox后出中心点坐标，然后往外面取一个out_shape范围的地理位置
    """
    list_dot = list()
    for item in shp_data:
        # print(item)
        x_list = list()
        y_list = list()
        if len(item['geometry']['coordinates']) > 1:
            for i in item['geometry']['coordinates']:
                # 处理带洞的Polygon
                if item['geometry']['type'] == 'Polygon':
                    item_new = i
                else:
                    item_new = i[0]
                array_item = np.array(item_new)
                max_x, max_y = array_item.max(axis=0)
                min_x, min_y = array_item.min(axis=0)
                x_list.append(max_x)
                x_list.append(min_x)
                y_list.append(max_y)
                y_list.append(min_y)
            # 根据输出像素尺寸得到地理范围
            left = min(x_list) + (max(x_list) - min(x_list)) / 2 - out_shape[1] * pix_x / 2
            # top = min(y_list) + (max(y_list) - min(y_list)) / 2 - out_shape[0] * pix_y / 2
            bottom = min(y_list) + (max(y_list) - min(y_list)) / 2 - out_shape[0] * abs(pix_y) / 2
        else:
            array_item = np.array(item['geometry']['coordinates'][0])
            max_x, max_y = array_item.max(axis=0)
            min_x, min_y = array_item.min(axis=0)
            # 根据输出像素尺寸得到地理范围
            left = min_x + (max_x - min_x) / 2 - out_shape[1] * pix_x / 2
            # top = min_y + (max_y - min_y) / 2 - out_shape[0] * pix_y / 2
            bottom = min_y + (max_y - min_y) / 2 - out_shape[0] * abs(pix_y) / 2

        list_dot.append((left, bottom))
    return list_dot
