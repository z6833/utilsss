import rasterio
# import sys
# sys.path.append('..')


from base.driver_base import DriverBase
from rasterio.io import MemoryFile


class TifDriver(DriverBase):
    def __init__(self):  # filepath=None):
        """
        tif文件路径
        :param filepath:
        """
        # self.file_path = filepath
        self.mem_file = None
        self.handle = None

    def load(self, raster_obj):
        """
        载入tif的数据方法，推荐使用fiona
        :param raster_obj: 栅格数据对象
        :return:
        """
        if raster_obj.data_uri is None:
            # 路径为空，必然包含data和profile数据
            self.mem_file = MemoryFile()
            self.handle = self.mem_file.open(**raster_obj.profile)
            self.handle.write(raster_obj.data)
        else:
            # 处理path的情况
            if raster_obj.data_uri.endswith(".ecw"):
                driver = "ECW"
            else:
                driver = None
            self.handle = rasterio.open(raster_obj.data_uri, driver = driver)

    def save(self, raster_obj, uri=None):
        """
         保存数据方法
         :param raster_obj:  栅格数据对象
         :param uri: 需要保存的路径
         """

        # print("raster_obj-----",raster_obj)
        data_handle = raster_obj.data_handle
        if data_handle is None:
            data = raster_obj.data
            profile = raster_obj.profile
        else:
            data = data_handle.read()
            profile = data_handle.profile

        # todo 处理大文件时候需要分块写
        with rasterio.open(uri, 'w', **profile) as dst:
            dst.write(data)

    def close(self):
        """释放当前资源"""
        if self.handle is not None:
            self.handle.close()
        if self.mem_file is not None:
            self.mem_file.close()

