import datetime
from copy import deepcopy

import numpy as np
from affine import Affine
from shapely.geometry import Polygon, shape, mapping
from shapely.affinity import affine_transform
from shapely.validation import make_valid
from rasterio import features
import json
import os
import cv2 as cv
import traceback
from itertools import groupby

from shapes.shape import LayerData


class CocoDateSet:
    def __init__(self, label_dict):
        self.image_index = 0
        self.ann_index = 0
        self.label_dict = label_dict
        self.reverse_label_dict = dict()
        # 初始化coco字典
        self.coco_dict = {
            "info": {
                "description": "SOUTHGIS COCO-format dataset",
                "url": "",
                "version": "1.0",
                "contributor": "SOUTHGIS",
                "year": datetime.date.today().year,
                "date_created": str(datetime.datetime.today()),
            },
            "licenses": [{
                "id": 0,
                "name": "southgis",
                "url": "",
            }],
            "images": [],
            "annotations": [],
            "categories": []
        }
        # 单分类默认为target
        if self.label_dict is None:
            item = {
                "id": 1,
                "name": "target",
            }
            self.coco_dict["categories"].append(item)
        # 多分类根据输入列表确认
        else:
            for ky, val in self.label_dict.items():
                self.reverse_label_dict[val] = ky
                item = {
                    "id": ky,
                    "name": label_dict[ky],
                }

                self.coco_dict["categories"].append(item)

    def add_image(self, image_information):
        """
        # 往coco字典里面添加图片信息
        :param image_information: [image_path,height,width]
        :return:
        """
        self.image_index += 1
        img_dict = {
            "id": self.image_index,
            "file_name": image_information[0],
            "height": image_information[1],
            "width": image_information[2]
        }
        self.coco_dict["images"].append(img_dict)
        return self.image_index

    def add_ann(self, image_id, image_annotation):
        """
        # 添加bbox类别相关信息
        :param image_id:
        :param image_annotation:[label,polygon,area,bbox]
        :return:
        """
        self.ann_index += 1
        if self.label_dict is None:
            category_id = 1
        else:
            category_id = self.reverse_label_dict[image_annotation[0]]
        ann_dict = {
            "id": self.ann_index,
            "image_id": image_id,
            "category_id": category_id,
            "segmentation": image_annotation[1],
            "area": image_annotation[2],
            "bbox": image_annotation[3],
            "iscrowd": 0,
        }
        self.coco_dict["annotations"].append(ann_dict)

    def add_information(self, image_information, image_annotation):
        """
        添加每张照片的标注信息
        :param image_information:
        :param image_annotation:
        :return:
        """
        image_index = self.add_image(image_information)
        for annotation in image_annotation:
            self.add_ann(image_index, annotation)

    def save(self, file_name):
        with open(file_name, "w") as f:
            json.dump(self.coco_dict, f)


# def save_coco(self):
#     file_name = os.path.join(self.output_dir_json, "sample_lib.json")
#     self.coco_obj.save(file_name)
def img_save_coord(crop_rs, output_dir, save_name):
    crop_rs.save(os.path.join(output_dir, save_name))


def img_save_no_coord(crop_rs, output_dir, save_name):
    if crop_rs.data.shape[0] == 1 or crop_rs.data.shape[0] == 3:
        crop_rs_data = crop_rs.data
        crop_rs_data_CHW2HWC = crop_rs_data.transpose(1, 2, 0)
        crop_rs_data_RGB2BGR = cv.cvtColor(crop_rs_data_CHW2HWC, cv.COLOR_RGB2BGR)
        cv.imwrite(os.path.join(output_dir, save_name), crop_rs_data_RGB2BGR)
    else:
        # crop_rs_data = np.delete(crop_rs.data, -1, axis=0)
        raise ValueError("切片的波段数不是3！")


# 创建样本标记Labelme格式的json文件
def createLabelmeLabels(self, save_path, imageName, imageWidth, imageHeight, categories, polygons):
    labelmeJson = dict()
    polygonsArr = []
    labelmeJson["version"] = "4.2.10"
    labelmeJson["flags"] = {}
    labelmeJson["shapes"] = polygonsArr
    labelmeJson["imagePath"] = os.path.join(self.output_dir_img, imageName)
    # labelmeJson["imagePath"] = r"../imgs/{}".format(imageName)
    labelmeJson["imageData"] = None
    labelmeJson["imageHeight"] = imageHeight
    labelmeJson["imageWidth"] = imageWidth
    for i in range(0, len(polygons)):
        shape = dict()
        shape["label"] = categories[i]
        shape["points"] = polygons[i]
        shape["group_id"] = None
        shape["shape_type"] = "polygon"
        shape["flags"] = {}
        polygonsArr.append(shape)
    with open(save_path, "w") as f:
        json.dump(labelmeJson, f)



def transform_pixel_layer(layer_obj,raster_transform):
    inverse_transform = ~raster_transform
    affine_matrix = [inverse_transform.a, inverse_transform.b , inverse_transform.d, inverse_transform.e, inverse_transform.c, inverse_transform.f ]
    data_list = list()
    for item in layer_obj.data:
        tmp_item = deepcopy(item)
        item = shape(item["geometry"])
        if not item.is_valid:
            item = make_valid(item)
        item_pix = affine_transform(item, affine_matrix)
        tmp_item["geometry"]  = mapping(item_pix)
        data_list.append(tmp_item)
    return LayerData.build_data(data_list,deepcopy(layer_obj.profile))


def draw_tif(data,polygons,file_prefix):
    img = data.transpose(1, 2, 0)
    h,w,c = img.shape
    cv.imwrite(file_prefix+"pixel.tif",img)
    img_mask = np.zeros((h,w,), np.uint8)
    int_coords = lambda x: np.array(x).round().astype(np.int32)
    exteriors = [int_coords(poly.exterior.coords) for poly in polygons]
    interiors = [int_coords(pi.coords) for poly in polygons
                 for pi in poly.interiors]
    cv.fillPoly(img_mask, exteriors, 255)
    print("exteriors: ",exteriors)
    cv.fillPoly(img_mask, interiors, 0)
    cv.imwrite(file_prefix+"pixel_mask.tif",img_mask)


def get_polygons(shape_ds):
    polygons = list()
    for item in shape_ds:
        geom = shape(item["geometry"])
        valid_geom = make_valid(geom)
        #             print(valid_geom.geom_type)
        if valid_geom.geom_type == "Polygon":
            polygons.append(valid_geom)
        elif valid_geom.geom_type == "MultiPolygon":
            for plg in valid_geom.geoms:
                polygons.append(plg)
    return polygons


def add_detection_item(crop_rs, crop_shp, output_dir_img, save_name, out_shape, feature):
    transform = crop_rs.profile['transform']
    # inverse_transform = ~transform
    # affine_matrix = [inverse_transform.a, inverse_transform.b , inverse_transform.d, inverse_transform.e, inverse_transform.c, inverse_transform.f ]
    polygon_tif = Polygon([(0, 0), (out_shape[1], 0), (out_shape[1], out_shape[2]), (0, out_shape[2])])
    new_polygons = list()
    new_categories = list()
    pixel_shp = transform_pixel_layer(crop_shp, transform)

    # if num > 100:
    #     save_name = "target_detection_{}_{}".format(num, num2)
    #     polygons = get_polygons(pixel_shp.data)
    #     draw_tif(crop_rs.data,polygons,save_name)

        # crop_rs.save(save_name)
        # pixel_shp.save(save_name[:-3] + "shp")
        # exit(0)

    for item in pixel_shp.data:
        label = 'target'
        try:
            item = shape(item["geometry"])
            if polygon_tif.contains(item):
                new_polygons.append(item)
            else:
                # print(crop_shp.data[k])
                try:
                    intersection = polygon_tif.intersection(item)
                    # 当图斑在该切片的面积大于原图斑的0.7
                    if intersection.area / item.area > 0.7:
                        new_polygons.append(intersection)
                except Exception as e:
                    print("polygon id:{}有拓扑错误".format(item['id']),e)
        except Exception as e:
            print("polygon id:{}有拓扑错误".format(item['id']),e)

        if feature:
            label = item['properties'][feature]
        new_categories.append(label)

    image_information = [os.path.join(os.path.basename(output_dir_img), save_name), out_shape[2], out_shape[1]]
    image_annotation = list()

    for i, plg in enumerate(new_polygons):
        minx, miny, maxx, maxy = [i if i > 0 else 0 for i in np.around(np.array(plg.bounds), decimals=1)]
        label = new_categories[i]

        polygon = polygon_obj2rle(plg, out_shape)

        image_annotation.append(
            [label, polygon, np.around(plg.area, decimals=2), [minx, miny, maxx - minx, maxy - miny]])

    return image_information, image_annotation


def polygon_obj2rle(polygon, out_shape):
    """
    polygon的coords转化为list格式
    """
    transform = Affine(1, 0, 0, 0, -1, out_shape[2])
    polygon = mapping(polygon)
    if polygon['type'] == 'GeometryCollection':
        data = polygon['geometries']
    else:
        data = [polygon]
    result = dict()
    mask = features.rasterize(((item, 1) for item in data), transform=transform, out_shape=(out_shape[2], out_shape[1]))
    # print("mask", mask)
    # print("mask.number", np.sum(mask == 1))
    # result["count"] = rle_encode(mask)
    # result["size"] = [out_shape[2], out_shape[1]]
    result = mask_to_rle(mask)
    return result


# def rle_encode(binary_mask):
#     '''
#     binary_mask: numpy array, 1 - mask, 0 - background
#     Returns run length as string formated
#     '''
#     pixels = binary_mask.flatten(order='F')
#     pixels = np.concatenate([[0], pixels, [0]])
#     runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
#     runs[1::2] -= runs[::2]
#     return runs.tolist()

def mask_to_rle(binary_mask):
    rle = {'counts': [], 'size': list(binary_mask.shape)}
    counts = rle.get('counts')
    for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order='F'))):
        if i == 0 and value == 1:
            counts.append(0)
        counts.append(len(list(elements)))
    return rle


class CocoDataSave:
    def __init__(self, label_list=None, output_dir_json=None, output_dir_img=None):
        self.output_dir_json = output_dir_json
        # self.output_dir_mask = output_dir_mask
        self.output_dir_img = output_dir_img
        if label_list is None:
            self.label_dict = None
        else:
            self.label_dict = {(i + 1): lb for i, lb in enumerate(label_list)}

        self.coco_obj = CocoDateSet(self.label_dict)

    def save_coco(self):
        file_name = os.path.join(self.output_dir_json, "sample_lib.json")
        self.coco_obj.save(file_name)

    # # mask图像保存
    # def mask_save(self, crop_shp, save_name):
    #
    #     if np.all(crop_shp.data == 0):
    #         return False
    #     else:
    #         crop_shp.save(os.path.join(self.output_dir_mask, save_name))
    #         return True
    #
    # # mask 无地理信息图像保存
    # def mask_png_save(self, crop_shp, save_name):
    #     crop_rs_data = crop_shp.data
    #     crop_rs_data_CHW2HWC = crop_rs_data.transpose(1, 2, 0)
    #     crop_rs_data_RGB2BGR = cv.cvtColor(crop_rs_data_CHW2HWC, cv.COLOR_RGB2BGR)
    #
    #     if np.all(crop_rs_data_RGB2BGR == 0):
    #         return False
    #     else:
    #         cv.imwrite(os.path.join(self.output_dir_mask, save_name), crop_rs_data_RGB2BGR)
    #         return True
    #
    # # 图像保存
    # def img_save(self, crop_rs, save_name):
    #     crop_rs.save(os.path.join(self.output_dir_img, save_name))
    #
    # def img_png_save(self, crop_rs, save_name):
    #     if crop_rs.data.shape[0] == 4:
    #         crop_rs_data = np.delete(crop_rs.data, -1, axis=0)
    #     else:
    #         crop_rs_data = crop_rs.data
    #     crop_rs_data_CHW2HWC = crop_rs_data.transpose(1, 2, 0)
    #     crop_rs_data_RGB2BGR = cv.cvtColor(crop_rs_data_CHW2HWC, cv.COLOR_RGB2BGR)
    #     # os.path.join(self.output_dir_mask, save_name)
    #     cv.imwrite(os.path.join(self.output_dir_img, save_name), crop_rs_data_RGB2BGR)

    # 创建样本标记Labelme格式的json文件
    def createLabelmeLabels(self, save_path, imageName, imageWidth, imageHeight, categories, polygons):
        labelmeJson = dict()
        polygonsArr = []
        labelmeJson["version"] = "4.2.10"
        labelmeJson["flags"] = {}
        labelmeJson["shapes"] = polygonsArr
        labelmeJson["imagePath"] = os.path.join(self.output_dir_img, imageName)
        # labelmeJson["imagePath"] = r"../imgs/{}".format(imageName)
        labelmeJson["imageData"] = None
        labelmeJson["imageHeight"] = imageHeight
        labelmeJson["imageWidth"] = imageWidth
        for i in range(0, len(polygons)):
            shape = dict()
            shape["label"] = categories[i]
            shape["points"] = polygons[i]
            shape["group_id"] = None
            shape["shape_type"] = "polygon"
            shape["flags"] = {}
            polygonsArr.append(shape)
        with open(save_path, "w") as f:
            json.dump(labelmeJson, f)

    # 投影坐标转像素坐标
    # def add_detection_item(self, crop_rs, crop_shp, save_name, out_shape, feature):
    #     """
    #     feature ：
    #     """
    #     array_crop_rs = [crop_rs.profile['transform'].a, crop_rs.profile['transform'].b, crop_rs.profile['transform'].c,
    #                      crop_rs.profile['transform'].d, crop_rs.profile['transform'].e, crop_rs.profile['transform'].f,
    #                      crop_rs.profile['transform'].g, crop_rs.profile['transform'].h, crop_rs.profile['transform'].i]
    #     transform_crop_rs = (np.mat((np.asarray(array_crop_rs)).reshape(3, 3))).I
    #     # 是否保存tif标志量
    #     have = False
    #     polygon_tif = Polygon([(0, 0), (out_shape[1], 0), (out_shape[1], out_shape[2]), (0, out_shape[2])])
    #     new_polygons = list()
    #     new_categories = list()
    #     # 遍历一张图上K个polygon
    #     for K in range(len(crop_shp.data)):
    #         # Todo Shapely支持
    #         # Type的写法需要定义标准的shapefile关键字段
    #         label = 'target'
    #         # 处理multi_polygons
    #         if len(crop_shp.data[K]['geometry']['coordinates']) > 1:
    #             # 将Polygon的组合成员分别进行坐标转换
    #
    #             for i in crop_shp.data[K]['geometry']['coordinates']:
    #                 # 处理没有类型的数据
    #
    #                 if crop_shp.data[K]['geometry']['type'] == ' ':
    #                     item = [i]
    #                 else:
    #                     item = i
    #                 # 处理带洞的Polygon
    #                 if crop_shp.data[K]['geometry']['type'] == 'Polygon':
    #                     item_array = np.array(item)
    #                 else:
    #                     item_array = np.array(item[0])
    #                 # 将原始Polygon的规格从n*2 增加到n*3 与transform 3*3矩阵相乘 进行矩阵变换
    #                 array_one = np.ones(len(item_array)).T
    #                 array_polygon = np.insert(item_array, len(item_array[0]), values=array_one, axis=1)
    #                 array_polygon_pix = (array_polygon * transform_crop_rs.T).A
    #                 array_polygon_pix = np.delete(array_polygon_pix, 2, axis=1)
    #                 # 将不合格的Polygon给过滤
    #                 if len(array_polygon_pix) < 4:
    #                     continue
    #                 array_polygon_pix_new = Polygon(array_polygon_pix.astype(np.int))
    #
    #                 if not polygon_tif.contains(array_polygon_pix_new):
    #                     # 图片内是否有完整Polygon的标志量
    #                     have = False
    #                     break
    #                 # 图片内是否有完整Polygon的标志量
    #                 have = True
    #                 # multi_polygons.append(list(array_polygon_pix_new.exterior.coords))
    #                 # 如果是多分类的话，将label替换
    #                 if feature:
    #                     label = crop_shp.data[K]['properties'][feature]
    #                 new_categories.append(label)
    #                 # new_polygons.append(multi_polygons)
    #                 new_polygons.append(list(array_polygon_pix_new.exterior.coords))
    #         # polygon的坐标转换
    #         else:
    #             item_array = np.array(crop_shp.data[K]['geometry']['coordinates'])
    #             array_one = np.ones(len(item_array[0])).T
    #             array_polygon = np.insert(item_array[0], len(item_array[0][0]), values=array_one, axis=1)
    #             array_polygon_pix = (array_polygon * transform_crop_rs.T).A
    #
    #             array_polygon_pix = np.delete(array_polygon_pix, 2, axis=1)
    #             if len(array_polygon_pix) < 4:
    #                 continue
    #             array_polygon_pix_new = Polygon(array_polygon_pix.astype(np.int))
    #             polygon_tif = Polygon([(0, 0), (out_shape[1], 0), (out_shape[1], out_shape[2]), (0, out_shape[2])])
    #             if polygon_tif.contains(array_polygon_pix_new):
    #                 have = True
    #                 new_polygons.append(list(array_polygon_pix_new.exterior.coords))
    #
    #                 if feature:
    #                     label = crop_shp.data[K]['properties'][feature]
    #                 new_categories.append(label)
    #     if have is True:
    #         image_id = self.coco_obj.add_image(os.path.join(os.path.basename(self.output_dir_img), save_name),
    #                                            out_shape[2], out_shape[1])
    #         for i, plg in enumerate(new_polygons):
    #             plg_obj = Polygon(plg)
    #             minx, miny, maxx, maxy = plg_obj.bounds
    #             label = new_categories[i]
    #             self.coco_obj.add_ann(image_id, label, plg, plg_obj.area, [minx, miny, maxx - minx, maxy - miny], )
    #     return have
