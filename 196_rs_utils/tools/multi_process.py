# -*- coding: utf-8 -*-
"""
@File: multi_process.py
@time: 2022/3/29 16:59
@Desc: 实现样本切片的多进程处理
E-mail = yifan.jiang@southgis.com
"""
import os
import numpy as np
import datetime
import traceback
from multiprocessing import Process
from multiprocessing import Queue
from ..rasters.raster import RasterData
from ..sample_makes import SampleMakeBase
from ..sample_makes.data_save import CocoDateSet, add_detection_item


class Producer(Process):
    def __init__(self, process_number, queue, task, input_shp, input_tif, input_shp_buffer, input_tif_change,
                 output_dir, type_crop, angle, out_shape, move, label, resolution, step, save_no_coord, buffer_field,
                 list_buffer_name, listFeature, feature, callback, image_num, init_percent):
        super(Producer, self).__init__()
        sample_make = SampleMakeBase(task, input_shp, input_tif, input_shp_buffer, input_tif_change, output_dir,
                                     type_crop, angle, out_shape, move, label, resolution, step, save_no_coord,
                                     buffer_field, list_buffer_name, listFeature, feature, callback, image_num,
                                     init_percent)
        self.data_coordinator = sample_make.data_coordinator
        self.queue = queue
        self.number = process_number
        self.callback = callback

    def run(self) -> None:
        for item in self.data_coordinator:
            if self.callback is not None:
                self.callback(len(self.data_coordinator))
            self.queue.put(item)
        # 根据进程数量添加完成信号
        for j in range(self.number):
            self.queue.put(None)


class Consumer(Process):
    def __init__(self, queue, queue_out, task, input_shp, input_tif, input_shp_buffer, input_tif_change, output_dir,
                 type_crop, angle, out_shape, move, label, resolution, step, save_no_coord, buffer_field,
                 list_buffer_name, listFeature, feature, callback, image_num, init_percent):
        super(Consumer, self).__init__()
        sample_make = SampleMakeBase(task, input_shp, input_tif, input_shp_buffer, input_tif_change, output_dir,
                                     type_crop, angle, out_shape, move, label, resolution, step, save_no_coord,
                                     buffer_field, list_buffer_name, listFeature, feature, callback, image_num,
                                     init_percent)
        self.queue = queue
        self.queue_out = queue_out
        self.task = sample_make.task
        self.output_dir_mask = sample_make.output_dir_mask
        self.get_win = sample_make.get_win
        self.judge_win = sample_make.judge_win
        self.shp = sample_make.shp
        self.out_shape_rs = sample_make.out_shape_rs
        self.listFeature = sample_make.listFeature
        self.feature = sample_make.feature
        self.num2 = sample_make.num2
        self.img_save = sample_make.img_save
        self.output_dir_img = sample_make.output_dir_img
        self.output_dir = sample_make.output_dir
        self.output_dir_img_after = sample_make.output_dir_img_after
        self.input_tif_change = sample_make.input_tif_change
        self.rs = sample_make.rs
        self.data_coordinator = sample_make.data_coordinator

    def run(self) -> None:
        try:
            if self.task == 1:
                self.target_detection()
            elif self.task == 2:
                self.segmentation()
            else:
                self.change_detection()
        except Exception as e:
            print("Consumer:", str(e))
            traceback.print_exc()

    def segmentation(self):
        num = 0

        while True:
            item = self.queue.get()
            if item is not None:
                num += 1
                # print(num, '/', len(self.data_coordinator))
                # 窗口选择
                crop_win = self.get_win(item=item)
                crop_result = self.judge_win(crop_win)
                if crop_result is None:
                    continue
                crop_rs, crop_shp = crop_result
                crop_shp02 = self.shp.crop(crop_win, out_shape=self.out_shape_rs,
                                           listFeature=self.listFeature,
                                           feature=self.feature)
                # 保存切片的image与mask
                save_name = "segmentation_{}_{}.tif".format(num, self.num2)
                save_name_mask = "segmentation_{}_{}_mask.tif".format(num, self.num2)
                self.img_save(crop_rs, self.output_dir_img, save_name)
                self.img_save(crop_shp02, self.output_dir_mask, save_name_mask)

                csv_result = 'images/{},labels/{}'.format(save_name, save_name_mask)
                self.queue_out.put(csv_result)

            #     if (self.callback is not None) and num % 10 == 0:
            #         progress = (num / total_num) * 99 * (1 / self.image_num) + self.init_percent * 100
            #         self.callback(progress)
            # if self.callback is not None:
            #     self.callback(100 * (1 / self.image_num + self.init_percent))
            else:
                self.queue_out.put(None)
                break

    def target_detection(self):
        num = 0
        while True:
            item = self.queue.get()
            if item is not None:
                num += 1
                # print(num, '/', len(self.data_coordinator))
                crop_win = self.get_win(item=item)
                crop_result = self.judge_win(crop_win)
                if crop_result is None:
                    continue
                crop_rs, crop_shp02 = crop_result
                save_name = "target_detection_{}_{}.tif".format(num, self.num2)
                image_information, image_annotation = add_detection_item(crop_rs=crop_rs, crop_shp=crop_shp02,
                                                                         output_dir_img=self.output_dir_img,
                                                                         save_name=save_name,
                                                                         out_shape=self.out_shape_rs,
                                                                         feature=self.feature)
                self.img_save(crop_rs, self.output_dir_img, save_name)
                self.queue_out.put([image_information, image_annotation])
            else:
                self.queue_out.put(None)
                break

    def change_detection(self):
        # if not os.path.exists(self.output_dir_mask):
        #     os.makedirs(self.output_dir_mask)
        # if not os.path.exists(self.output_dir_img_after):
        #     os.makedirs(self.output_dir_img_after)
        rs2 = RasterData.build_file(self.input_tif_change)
        rs2.load(self.rs.crs_wkt)
        num = 0
        # total_num = len(self.data_coordinator)
        while True:
            item = self.queue.get()
            if item is not None:
                num += 1
                # print(num, '/', len(self.data_coordinator))
                # 窗口选择
                crop_win = self.get_win(item=item)
                crop_result = self.judge_win(crop_win)
                if crop_result is None:
                    continue
                crop_rs, crop_shp = crop_result
                crop_after_rs = rs2.crop(crop_win, out_shape=self.out_shape_rs)
                # 后时像全空时，跳过
                if np.all(crop_after_rs == 0):
                    continue
                crop_shp02 = self.shp.crop(crop_win, out_shape=self.out_shape_rs,
                                           listFeature=self.listFeature, feature=self.feature)
                # 保存切片的image与mask
                save_name = "change_detection_{}_{}.tif".format(num, self.num2)
                save_after_name = "change_detection_{}_{}_after.tif".format(num, self.num2)
                save_name_mask = "change_detection_{}_{}_mask.tif".format(num, self.num2)
                self.img_save(crop_rs, self.output_dir_img, save_name)
                self.img_save(crop_after_rs, self.output_dir_img_after, save_after_name)
                self.img_save(crop_shp02, self.output_dir_mask, save_name_mask)

                csv_result = 'images/{},images_after/{},labels/{}'.format(save_name, save_after_name, save_name_mask)
                self.queue_out.put(csv_result)
            #     if (self.callback is not None) and num % 10 == 0:
            #         progress = (num / total_num) * 99 * (1 / self.image_num) + self.init_percent * 100
            #         self.callback(progress)
            # if self.callback is not None:
            #     self.callback(100 * (1 / self.image_num + self.init_percent))
            else:
                self.queue_out.put(None)
                break


class Consumer2(Process):
    def __init__(self, consumer_number, queue, task, output_dir, listFeature=None, label=None):
        super(Consumer2, self).__init__()
        self.output_dir = output_dir
        self.queue = queue
        self.number = consumer_number
        self.task = task
        self.listFeature = listFeature
        self.label = label
        csv_name_dict = {
            '1': "target_detection",
            '2': "segmentation_sample",
            '3': "change_detection"
        }
        self.csv_name = csv_name_dict[str(self.task)]
        self.csv_path = self.output_dir + '/{}.csv'.format(self.csv_name)

    def run(self) -> None:
        try:
            if self.task == 1:
                self.write_coco()
            else:
                self.write()
        except Exception as e:
            print("Consumer2:", str(e))
            traceback.print_exc()

    def write(self):
        with open(self.csv_path, mode='a', newline='', encoding='utf-8') as csv_v:
            if self.listFeature:
                list_feature = ''
                for i, item in enumerate(self.listFeature):
                    list_feature = list_feature + ',' + item + ',' + str(self.listFeature[item])
                csv_v.write('#,version,1.0,data_creator,{}'.format(datetime.date.today()))
                csv_v.write('\n')
                csv_v.write('{}'.format(list_feature))
                csv_v.write('\n')
            index = 0
            while True:
                item = self.queue.get()
                if item is not None:
                    csv_v.write(item)
                    csv_v.write('\n')
                else:
                    index += 1
                    if index == self.number:
                        break

    def write_coco(self):
        if self.label is None:
            label_dict = None
        else:
            label_dict = {(i + 1): lb for i, lb in enumerate(self.label)}
        coco_obj = CocoDateSet(label_dict)
        index = 0
        while True:
            item = self.queue.get()
            if item is not None:
                coco_obj.add_information(item[0], item[1])
            else:
                index += 1
                if index == self.number:
                    break
        coco_json = os.path.join(self.output_dir, "sample_lib.json")
        coco_obj.save(coco_json)


def main(consumer_number, task, input_shp, input_tif, input_shp_buffer, input_tif_change, output_dir, type_crop, angle,
         out_shape, move, label, resolution, step, save_no_coord, buffer_field, list_buffer_name,
         listFeature, feature, callback, image_num, init_percent):
    """
    多进程程序入口
    :param consumer_number:
    :param task:
    :param input_shp:
    :param input_tif:
    :param input_shp_buffer:
    :param input_tif_change:
    :param output_dir:
    :param type_crop:
    :param angle:
    :param out_shape:
    :param move:
    :param label:
    :param resolution:
    :param step:
    :param save_no_coord:
    :param buffer_field:
    :param list_buffer_name:
    :param listFeature:
    :param feature:
    :param callback:
    :param image_num:
    :param init_percent:
    :return:
    """
    queue = Queue(10)
    queue_out = Queue(10)
    producer = Producer(consumer_number, queue, task, input_shp, input_tif, input_shp_buffer, input_tif_change,
                        output_dir, type_crop, angle, out_shape, move, label, resolution, step, save_no_coord,
                        buffer_field, list_buffer_name, listFeature, feature, callback, image_num, init_percent)
    jobs = list()
    for i in range(consumer_number):
        consumer = Consumer(queue, queue_out, task, input_shp, input_tif, input_shp_buffer, input_tif_change,
                            output_dir, type_crop, angle, out_shape, move, label, resolution, step, save_no_coord,
                            buffer_field, list_buffer_name, listFeature, feature, callback, image_num, init_percent)
        jobs.append(consumer)
    consumer2 = Consumer2(consumer_number, queue_out, task, output_dir, listFeature, label)

    print("task is start")
    producer.start()
    for job in jobs:
        job.start()
    consumer2.start()

    producer.join()
    for job in jobs:
        job.join()
    consumer2.join()
    print("task is over!")
