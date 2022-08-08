from .driver_base import DriverError


class DataBase:
    def __init__(self, data_uri=None, driver=None):

        self.driver = driver
        # data_handle表示数据处理句柄，
        # 矢量中使用fiona的MemoryFile实现，栅格中使用dataset实现
        # 在调用self.load函数内赋值
        self.data_handle = None

        self.data_uri = data_uri
        # 矢量的区域
        self.region_data = None
        # 目标坐标系
        self.crs_wkt = None
        # 载入数据的标志量
        self.load_flag = False

    def load(self):
        """
        使用driver进行数据读取
        :return:
        """
        if self.driver is None:
            raise DriverError("没有指定驱动")
        self.driver.load(self)

    def save(self, *args, **kwargs):
        """
        使用driver进行数据保存
        :param uri: 可选参数：数据保存资源名
        :return:
        """
        self.driver.save(self, *args, **kwargs)

    def crop(self, rect, out_shape=None):
        """
        数据切片
        :param rect: 表示切片区域的矩形（旋转矩形或者正矩形）
        :param out_shape: 切片输出的尺寸
        :return: 返回切片对象
        """
        raise NotImplementedError

    def clear(self):
        """申请资源释放"""
        raise NotImplementedError

    @property
    def region(self):
        """
        获取当前影像的区域范围，以四元组（left, bottom, right, top）表示
        """
        self.load()
        return self.region_data

    @region.setter
    def region(self, bounds):
        self.region_data = bounds
