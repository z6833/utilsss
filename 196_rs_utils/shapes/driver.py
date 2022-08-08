import fiona
import os
import configparser
# import sys
# sys.path.append('..')
from base.driver_base import DriverBase
from fiona.io import MemoryFile

# from presto.presto_client import PrestoClient
def get_local_config(local_config_path):

    if not os.path.exists(local_config_path):
        # logger.warning("Config File {} Not Found".format(local_config_path))
        return None
    # 创建管理对象
    conf_parser = configparser.ConfigParser()
    # 读ini文件
    conf_parser.read(local_config_path, encoding="utf-8")
    conf = {}
    for section in conf_parser.sections():
        conf[section] = {}
        for option in conf_parser.options(section):
            conf[section][option] = conf_parser.get(section, option)
    if 'configurations' not in conf:
        # logger.warning("session configurations should be top session")
        return None
    global g_confs
    g_confs = conf['configurations']
    return conf['configurations']

class ShapeFileDriver(DriverBase):
    def __init__(self):
        """
        处理shapefile格式文件
        """
        # self.file_path = filepath
        self.mem_file = None
        self.handle = None

    def load(self, shape_obj):
        """
        载入shapefile的数据方法，推荐使用fiona
        :param shape_obj: 数据对象，可以是矢量或者栅格数据
        :return:
        """
        if shape_obj.data_uri is None:
            # 路径为空，必然包含data和profile数据
            # self.mem_file = MemoryFile()
            # self.handle = self.mem_file.open(driver='GTiff', **raster_obj.profile)
            # self.handle.write(raster_obj.data)
            self.mem_file = MemoryFile()
            self.handle = self.mem_file.open(**shape_obj.profile)
            self.handle.writerecords(shape_obj.data)
            # 数据模型改为只读
            self.handle.mode = "r"
        else:
            # 处理path的情况
            self.handle = fiona.open(shape_obj.data_uri)


    def save(self, shape_obj, uri=None):
        """
         保存数据方法
         :param shape_obj:  矢量数据对象
         :param uri: 需要保存的路径
         """
        data_handle = shape_obj.data_handle
        with fiona.open(uri, 'w', **data_handle.profile) as dst:
            dst.writerecords(list(data_handle))

    def close(self):
        """释放当前资源"""
        if self.handle is not None:
            self.handle.close()
        if self.mem_file is not None:
            self.mem_file.close()


class PrestoDriver(DriverBase):
    def __init__(self, presto_client=None, layer=None, grid=None):
        """
        初始化Presto的驱动，参数可以在驱动实例化时候给，也可以从数据对象中读取
        :param presto_client:  presto的客户端
        :param layer:  数据库中要处理的层的名称
        """
        self.client = presto_client
        self.layer = layer

        self.table_name = None
        self.grid = grid
        self.output_shp_path=None
    def load(self, shape_obj, crs_wkt=None):
        """
        载入shapefile的数据方法，推荐使用fiona
        :param shape_obj: 矢量数据对象
        读取当前数据，需要根据坐标系和筛选条件载入，在crs为None时候设置crs，将数据写到data_handle中
        :param crs_wkt: 目标坐标系的wkt字符串
        """
        # todo conf接口
        # conf = get_local_config('config.ini')
        presto_cli = PrestoClient(self.client)
        grid_box = self.grid.bbox.split(',')
        if self.grid is not None:
            records = presto_cli.get_data_from_table_by_extents(self.table_name, grid_box[0], grid_box[1],
                                                            grid_box[2], grid_box[3])
        else:
            records = presto_cli.get_data_from_table(self.table_name)

        res = presto_cli.records_2_shp(records.data, output_shp_path=self.output_shp_path,input_srs_wkt=crs_wkt)
        return res.data['output_shp_path']

    def save(self, shape_obj, uri=None):
        """
         保存数据方法
         :param data_obj:  矢量数据对象
         :param uri: 需要保存的路径
         """
        data_handle = shape_obj.data_handle
        with fiona.open(uri, 'w', **data_handle.profile) as dst:
            dst.writerecords(list(data_handle))
    def close(self):
        """释放当前资源"""
        if self.client is not None:
            self.client.close()



class GdbDriver(DriverBase):
    def __init__(self, filepath=None, layer=None):
        """
        初始化gdb的驱动，参数可以在驱动实例化时候给，也可以从数据对象中读取
        这个优先级较低，先实现其他的
        :param filepath:  数据库文件路径
        :param layer:  数据库中要处理的层的名称
        """
        self.layer = layer
        self.file_path = filepath

    def load(self, shape_obj):
        """
        载入shapefile的数据方法，推荐使用fiona
        :param shape_obj: 数据对象，可以是矢量或者栅格数据
        :return:
        """
        pass

    def save(self, shape_obj, uri=None):
        """
         保存数据方法
         :param data_obj:  矢量数据对象
         :param uri: 需要保存的路径
         """

    def close(self):
        """释放当前资源"""
