# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import traceback
from osgeo import gdal, ogr
from .prestodb import dbapi
from ..utils.log import logger
from ..service.service_manager import _service_manager


class PrestoClient(object):
    def __init__(self):
        host = _service_manager.config['presto.host']
        port = _service_manager.config['presto.port']
        user = _service_manager.config['presto.user']
        catalog = _service_manager.config['presto.catalog']
        schema = _service_manager.config['presto.schema']
        self.conn = dbapi.Connection(host=host, port=port, user=user, schema=schema, catalog=catalog)

    def show_tables(self):
        """
        获取所有表名
        """
        cur = self.conn.cursor()
        cur.execute('show tables')
        res = cur.fetchall()
        if res is None:
            logger.warning("no table")
            return
        for item in res:
            logger.info(item)

    def create_table(self, table_name):
        """
        创建数据库表，目前支持存储目标检测bbox结果
        :param table_name: 表名
        :return: 创建结果
        """
        if table_name is None or table_name == "":
            logger.error("table name is empty")
            return False
        cur = self.conn.cursor()
        # 创建表
        # TODO: 后期支持写入坐标系
        # create_sql = "CREATE TABLE {} (the_geom Geometry with(geometry_type = 'Polygon'),class char(50) WITH ( nullable = true ),score double WITH ( nullable = true ))  with(table_indices = 'id,xz2')".format(table_name)
        create_sql = "CREATE TABLE {} (the_geom Geometry with(geometry_type = 'Polygon'),class char(50) WITH ( nullable = true ),score double WITH ( nullable = true ), status int WITH (nullable = true))  with(table_indices = 'id,xz2')".format(
            table_name)
        try:
            cur.execute(create_sql)
            cur.fetchone()
            logger.info("table {} created successfully!".format(table_name))
            return True, ""
        except Exception as e:
            errmsg = "create table {} failed, err: {}".format(table_name, e)
            logger.error(errmsg)
            logger.error(traceback.format_exc())
            return False, errmsg

    def insert_features(self, table_name, features):
        """
        将features批量写入到db中
        :param table_name: 表名
        :param features: 要素list，其中每个元素为一个元组，格式为(wkt, class_name, score, status)
        :return: 插入结果
        """
        if table_name is None or table_name == "":
            logger.error("table name is empty")
            return False
        if features is None or len(features) == 0:
            logger.error("input features is empty")
            return False
        cur = self.conn.cursor()
        values = ""
        # 构造批量上传的sql
        for feature in features:
            wkt, class_name, score, status = feature
            # value = "(st_geometryfromtext('{}'), '{}', {})".format(wkt, class_name, score)
            value = "(st_geometryfromtext('{}'), '{}', {}, {})".format(wkt, class_name, score, status)
            values += value + ","
        values = values[:-1]
        insert_sql = "Insert into {} values {}".format(table_name, values)
        try:
            cur.execute(insert_sql)
            cur.fetchone()
            logger.info("insert into {} successfully!".format(table_name))
            return True, ""
        except Exception as e:
            errmsg = "insert into {} failed, err: {}".format(table_name, e)
            logger.error(errmsg)
            logger.error(traceback.format_exc())
            return False, errmsg

    def clear_table(self, table_name):
        """
        删除指定表中所有记录
        :param table_name: 表名
        :return: 插入结果
        """
        if table_name is None or table_name == "":
            logger.error("table name is empty")
            return False
        cur = self.conn.cursor()
        # 清空表
        sql = "Delete from {}".format(table_name)
        try:
            cur.execute(sql)
            cur.fetchone()
            logger.info("table {} cleared successfully!".format(table_name))
            return True, ""
        except Exception as e:
            errmsg = "clear table {} failed, err: {}".format(table_name, e)
            logger.error(errmsg)
            logger.error(traceback.format_exc())
            return False, errmsg

    def get_data_from_table(self, table_name):
        """
        获取指定表中的数据
        :param table_name: 表名
        :return: 返回数据list
        """
        if table_name is None or table_name == "":
            logger.error("table name is empty")
            return False
        cur = self.conn.cursor()
        cur.execute("select * from {}".format(table_name))
        res = cur.fetchall()
        if res is None:
            logger.warning("no record in table {}".format(table_name))
            return
        return res

    def read_shp(self, shp_path):
        """
        读取shp
        """
        # 为了支持中文路径，请添加下面这句代码
        gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")
        # 为了使属性表字段支持中文，请添加下面这句
        gdal.SetConfigOption("SHAPE_ENCODING", "")
        # 注册所有的驱动
        ogr.RegisterAll()
        # 数据格式的驱动
        driver = ogr.GetDriverByName('ESRI Shapefile')
        shp = driver.Open(shp_path)
        if shp is None:
            return False, "Cannot Open " + shp_path
        return True, shp

    def write_shp_to_db(self, table_name, shp_path):
        """
        将shp内容写入到db
        :param table_name:
        :param shp_path:
        :return:
        """
        is_success, shp = self.read_shp(shp_path)
        if not is_success:
            return
        is_success, errmsg = self.create_table(table_name)
        if not is_success:
            return
        feature_layer = shp.GetLayerByIndex(0)
        polygons = []
        # 对每个要素进行遍历，裁剪一定范围的周边区域
        for n in range(0, feature_layer.GetFeatureCount()):
            feature = feature_layer.GetFeature(n)
            class_name = feature.GetField('class')
            score = feature.GetField('score')
            status = feature.GetField('status')
            geometry = feature.GetGeometryRef()
            if geometry is None:
                continue
            wkt = geometry.ExportToWkt()
            polygons.append((wkt, class_name, score, status))
        self.insert_features(table_name, polygons)
