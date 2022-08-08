from pyproj import CRS
from pyproj import Transformer
import numpy as np
from rasterio.windows import Window
import math
from .transform import trans_points_coordinate


def calc_rect_points(center, height, width, angle) -> np.array:
    """
    计算旋转矩形的顶点坐标
    :param center:  中心点
    :param height: 矩形高度
    :param width: 矩形宽度
    :param angle: 旋转角度
    :return:返回顶点坐标（numpy.array）格式。shape为（4，2）
    """
    x, y = center
    h = height
    w = width
    angle = angle

    x_1 = x - w / 2
    y_1 = y + h / 2

    x_2 = x + w / 2
    y_2 = y + h / 2

    x_3 = x + w / 2
    y_3 = y - h / 2

    x_4 = x - w / 2
    y_4 = y - h / 2

    x_a = (x_1 - x) * math.cos(math.radians(angle)) - (y_1 - y) * math.sin(math.radians(angle)) + x
    y_a = (x_1 - x) * math.sin(math.radians(angle)) + (y_1 - y) * math.cos(math.radians(angle)) + y

    x_b = (x_2 - x) * math.cos(math.radians(angle)) - (y_2 - y) * math.sin(math.radians(angle)) + x
    y_b = (x_2 - x) * math.sin(math.radians(angle)) + (y_2 - y) * math.cos(math.radians(angle)) + y

    x_c = (x_3 - x) * math.cos(math.radians(angle)) - (y_3 - y) * math.sin(math.radians(angle)) + x
    y_c = (x_3 - x) * math.sin(math.radians(angle)) + (y_3 - y) * math.cos(math.radians(angle)) + y

    x_d = (x_4 - x) * math.cos(math.radians(angle)) - (y_4 - y) * math.sin(math.radians(angle)) + x
    y_d = (x_4 - x) * math.sin(math.radians(angle)) + (y_4 - y) * math.cos(math.radians(angle)) + y

    out = np.array([[x_a, y_a], [x_b, y_b], [x_c, y_c], [x_d, y_d]])

    return out


class Polygon:
    def __init__(self, point_arr):
        self.points = np.array(point_arr)

    @property
    def left(self):
        return self.points[:, 0].min()

    @property
    def right(self):
        return self.points[:, 0].max()

    @property
    def bottom(self):
        return self.points[:, 1].min()

    @property
    def top(self):
        return self.points[:, 1].max()

    def trans_points(self, transformer: Transformer):
        point_arr = trans_points_coordinate(self.points, transformer)
        return Polygon(point_arr)

    def bounds(self):
        return self.left, self.bottom, self.right, self.top


class Rect(Polygon):
    def __init__(self, left, bottom, right, top):
        point_arr = np.array([(left, top), (right, top), (right, bottom), (left, bottom)])
        super(Rect, self).__init__(point_arr)

    def __repr__(self):
        return " left, bottom, right, top:{} {} {} {}".format( self.left, self.bottom, self.right, self.top)


class RotateRect(Polygon):
    def __init__(self, center, height, width, angle):
        if angle < 0 or angle > 90:
            raise ValueError("Valid range of angle is [0,90] degree.")
        self.center = center
        self.height = height
        self.width = width
        self.angle = angle
        point_arr = calc_rect_points(center, height, width, angle)
        super(RotateRect, self).__init__(point_arr)
        self.LeftWin = point_arr[:, 0].min()
        self.RightWin = point_arr[:, 0].max()
        self.BottomWin = point_arr[:, 1].min()
        self.TopWin = point_arr[:, 1].max()

    @property
    def leftbottom(self):
        """
        旋转前左下角点旋转后的坐标，用于旋转裁剪
        :return:
        """
        # center_point = self.points.mean(axis=0)
        # for pt in self.points:
        #     diff = pt - center_point
        #     if diff[0] <= 0 and diff[1] <= 0:
        return self.points[3]
