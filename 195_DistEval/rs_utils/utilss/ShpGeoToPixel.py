import fiona
import rasterio
import numpy as np
import json
import cv2 as cv


def shp_nocoord_rotate(shp_path, tif_path,json_save_path):
    """
    普通裁剪和旋转裁剪，投影坐标转像素坐标
    将原来的shp里面的投影坐标转像素坐标
    保存为json文件
    :return:
    """
    data_iter = fiona.open(shp_path)
    raster = rasterio.open(tif_path)
    data_list = []
    data_coord = []

    # 计算transform的逆矩阵transform_1
    l = [raster.transform.a, raster.transform.b, raster.transform.c, raster.transform.d, raster.transform.e,
         raster.transform.f, raster.transform.g, raster.transform.h, raster.transform.i]
    transform_1 = (np.mat((np.asarray(l)).reshape(3, 3))).I

    for item in data_iter:
        # 将矢量图像中的投影坐标对应原tif的transform转换为像素坐标
        for i in item["geometry"]["coordinates"][0]:
            cc = np.mat([i[0], i[1], 1]).T
            out= (transform_1*cc).A
            px = int(out[0][0])
            py = int(out[1][0])
            data_coord.append((px, py))

        item["geometry"]["coordinates"][0] = data_coord
        data_list.append(item)
        data_coord = []
    json_save = json.dumps(data_list)
    f2 = open(json_save_path, 'w')
    f2.write(json_save)
    f2.close()

def JsonToImg(tif_path, json_path, JsonToImg_save_path):
    """
        矢量数据投影坐标转像素坐标后的重叠验证
        存储为图片
        :return:
    """
    # 待验证的tif图像
    img = cv.imread(tif_path)
    # img = cv.imread('/Users/zhangshirun/Documents/04_code/rs_utils-ss_refactor 2/test/test_crop_rotate_raster_small_45.tif')
    # 导入矢量坐标转换后的json文件，并将坐标写到待验证的图像中
    with open(json_path, 'r') as load_f:
        load_dict = json.load(load_f)
        for item in load_dict:
            pts = np.array(item['geometry']['coordinates'][0], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv.polylines(img, pts=[pts], isClosed=True, color=(0, 0, 255), thickness=4)
    cv.imwrite(JsonToImg_save_path,img)


if __name__ == "__main__":

    shp_path = '/data/cage_dataset_shp48/cage_bbox_shp48.shp'
    tif_path = 'test/test_crop_rotate_raster_big_30.tif'
    json_path = 'test/shp_json_rotate.json'
    JsonToImg_save = 'test/polylines_show.png'

    # 投影坐标转像素坐标
    shp_nocoord_rotate(shp_path, tif_path, json_path)
    # 矢量数据投影坐标转像素坐标后的重叠验证
    JsonToImg(tif_path, json_path, JsonToImg_save)

