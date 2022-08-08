# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/11/3 9:37
# @File    : tile_service.py
# @Desc    : 实现访问瓦片服务相关

import os
import math
import datetime
import traceback
import uuid
import asyncio
from osgeo import gdal
from aiohttp import ClientSession
from ..service.service_manager import _service_manager
from ..utils.log import logger


def get_tile_urls_by_extent(service_url, zoom, ul_x, ul_y, lr_x, lr_y):
    """
    获取给定地理范围内瓦片的url集合
    :param ul_x: 给定地理范围左上角x坐标
    :param ul_y: 给定地理范围左上角y坐标
    :param lr_r: 给定地理范围右下角x坐标
    :param lr_y: 给定地理范围右下角y坐标
    :return: 瓦片url集合
    """
    if ul_x > lr_x or ul_y < lr_y:
        return None
    tile_urls = list()
    tile_rows_cols = get_tile_row_col_by_extent(ul_x, ul_y, lr_x, lr_y, zoom)
    logger.info("tile_rows_cols: {}".format(tile_rows_cols))
    start_row, end_row, start_col, end_col = tile_rows_cols
    for row in range(start_row, end_row + 1):
        for col in range(start_col, end_col + 1):
            tile_url = "{}?style=default&tilematrixset=EPSG%3A3857&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fpng&TileMatrix={}&TileCol={}&TileRow={}".format(
                service_url, zoom, col, row)
            tile_urls.append((tile_url, row, col))
    return tile_urls, tile_rows_cols


def get_tile_row_col_by_extent(ul_x, ul_y, lr_x, lr_y, zoom):
    """
    根据给定地理范围和缩放级别获取瓦片起止行列号(墨卡托投影)
    :param ul_x: 给定地理范围左上角x坐标
    :param ul_y: 给定地理范围左上角y坐标
    :param lr_r: 给定地理范围右下角x坐标
    :param lr_y: 给定地理范围右下角y坐标
    :param zoom: 缩放级别
    :return:
    """
    n = math.pow(2, zoom)
    start_col = int(((ul_x + 180) / 360) * n)
    end_col = int(((lr_x + 180) / 360) * n)
    start_row = int((1 - (math.log(math.tan(math.radians(ul_y)) + (
            1 / math.cos(math.radians(ul_y)))) / math.pi)) / 2 * n)
    end_row = int((1 - (math.log(math.tan(math.radians(lr_y)) + (
            1 / math.cos(math.radians(lr_y)))) / math.pi)) / 2 * n)
    return start_row, end_row, start_col, end_col


def get_tile_extent_by_row_col(row, col, zoom):
    """
    根据给定瓦片行列号和缩放级别获取瓦片的地理范围(墨卡托投影)
    :param row: 行号
    :param col: 列号
    :param zoom: 缩放级别
    :return:
    """
    n = math.pow(2, zoom)
    min_x = col / n * 360.0 - 180.0
    max_x = (col + 1) / n * 360.0 - 180.0
    max_y = math.atan(math.sinh(math.pi * (1 - 2 * row / n))) * 180.0 / math.pi
    min_y = math.atan(math.sinh(math.pi * (1 - 2 * (row + 1) / n))) * 180.0 / math.pi
    return min_x, min_y, max_x, max_y


async def request_tile(out_raster, semaphore, url, row, col):
    async with semaphore:
        async with ClientSession() as session:
            async with session.get(url) as response:
                res = await response.read()
                if len(res) == 0:
                    logger.warning("tile fetch None, url: {}".format(url))
                    return None
                is_success, errmsg = write_bytes_to_image(out_raster, res, row, col)
                if not is_success:
                    logger.warning("tile parse failed, url: {}".format(url))
                    return None
                return res


async def request_tiles(out_raster, urls, tile_rows_cols):
    start_row, end_row, start_col, end_col = tile_rows_cols
    semaphore = asyncio.Semaphore(200)  # 限制并发量
    to_get = [request_tile(out_raster, semaphore, url[0], url[1] - start_row, url[2] - start_col) for url in
              urls]
    await asyncio.wait(to_get)


def create_tif(output_path, rows, cols, min_x, max_y, max_x, min_y, zoom):
    proj = 'GEOGCS["GCS_China_Geodetic_Coordinate_System_2000",DATUM["D_China_2000",SPHEROID["CGCS2000",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
    #resolution = (float(360) / 256) / math.pow(2, zoom)
    resolution_x = float(max_x - min_x) / cols
    resolution_y = float(max_y - min_y) / rows
    #@print('new tif resolution: {},  {}'.format(resolution_x, resolution_y))
    # self.crop_x = 50
    # self.crop_y = 50
    # self.step_x = 15
    # self.step_y = 15
    driver = gdal.GetDriverByName('GTiff')
    out_raster = driver.Create(output_path, cols, rows, 3, gdal.GDT_Byte)
    out_raster.SetGeoTransform((min_x, resolution_x, 0, max_y, 0, -1 * resolution_y))
    out_raster.SetProjection(proj)
    return out_raster


def write_bytes_to_image(out_raster, img_bytes, row, col):
    """
    将给定的瓦片写入到image的特定坐标位置
    :param img_bytes: 瓦片bytes
    :param row:
    :param col:
    """
    vfn = "/vsimem/tmp/{}".format(uuid.uuid4())
    try:
        gdal.FileFromMemBuffer(vfn, img_bytes)
        tile_ds = gdal.Open(vfn, gdal.GA_ReadOnly)
        if tile_ds is None:
            errmsg = "tile col: {}, row: {} read from bytes none".format(col, row)
            logger.warning(errmsg)
            return False, errmsg
        tile_array = tile_ds.ReadAsArray(0, 0, 256, 256)
        for i in range(0, 3):
            out_raster.GetRasterBand(i + 1).WriteArray(tile_array[i], col * 256, row * 256)
        return True, ""
    except Exception as e:
        errmsg = "read tile col: {}, row: {} error: {}".format(col, row, e)
        logger.warning(errmsg)
        logger.error(traceback.format_exc())
        return False, errmsg


def request_and_stitch_tiles(service_url, zoom, ul_x, ul_y, lr_x, lr_y, identifier):
    # urls, tile_rows_cols = ts.get_tile_urls_by_extent(113.365380, 23.087590, 113.365604, 23.087313)
    urls, tile_rows_cols = get_tile_urls_by_extent(service_url, zoom, ul_x, ul_y, lr_x, lr_y)
    # ts.get_tile_urls_by_extent(113.365604,23.087590,113.365604,23.087590)
    start_row, end_row, start_col, end_col = tile_rows_cols
    # 左上角瓦片的坐标范围
    ul_tile_extent = get_tile_extent_by_row_col(start_row, start_col, zoom)
    # 右下角瓦片的坐标范围
    lr_tile_extent = get_tile_extent_by_row_col(end_row, end_col, zoom)
    tasks = []
    width = 256 * (end_col - start_col + 1)
    height = 256 * (end_row - start_row + 1)
    logger.info('create tif, height: {}, width: {}'.format(height, width))
    input_filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S_') + "{}.tif".format(identifier)
    input_filepath = os.path.join(_service_manager.config['cache.root.dir'],
                                  _service_manager.config['cache.input_files.dir'], input_filename)
    out_raster = create_tif(input_filepath, height, width, ul_tile_extent[0], ul_tile_extent[3], lr_tile_extent[2], lr_tile_extent[1], zoom)
    # loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(request_tiles(out_raster, urls, tile_rows_cols))
    loop.close()
    # 关闭raster，否则只有缓存满了才会保存
    out_raster = None
    # for url in urls:
    #     task = asyncio.ensure_future(self.request_tile(url[0], url[1] - start_row, url[2] - start_col))
    #     tasks.append(task)
    # result = loop.run_until_complete(asyncio.wait(tasks))
    return input_filepath


if __name__ == "__main__":
    request_and_stitch_tiles('http://172.20.20.1/api/ispatial-service/service/wmts/373', 22, 113.365280, 23.087690,
                             113.365704, 23.087213)
    # #@print(result)
