# -*- coding: utf-8 -*-
"""
@File: multi_main.py
@time: 2022/4/1 9:35
@Desc: 样本切片多进程处理的主程序
E-mail = yifan.jiang@southgis.com
"""
import argparse
import os
from .multi_process import main


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='sample make')
    parser.add_argument('--task', type=int, default=0, help='任务类型 1、目标检测 2、语义分割 3、变化检测')
    parser.add_argument('--input_tif', type=str, default=None, help='输入tif路径')
    parser.add_argument('--input_tif_change', type=str, default=None, help='输入tif后时像路径')
    parser.add_argument('--input_shp_buffer', type=str, default=None, help='缓冲区约束')
    parser.add_argument('--input_shp', type=str, default=None, help='输入shp路径')
    parser.add_argument('--output_dir', type=str, default=None, help='输出路径')
    parser.add_argument('--angle', type=str, default=None, help='旋转数据增强')
    parser.add_argument('--label', type=str, default=None, help='目标检测标签')
    parser.add_argument('--move', type=str, default=False, help='偏移数据增强')
    parser.add_argument('--type_crop', type=str, default=False, help='数据裁剪方式')
    parser.add_argument('--out_shape_x', type=int, default=600, help='输出像素尺寸-长')
    parser.add_argument('--out_shape_y', type=int, default=600, help='输出像素尺寸-宽')
    parser.add_argument('--step_x', type=int, default=None, help='滑窗裁剪步长-长')
    parser.add_argument('--step_y', type=int, default=None, help='滑窗裁剪步长-宽')
    parser.add_argument('--resolution', type=int, default=0, help='指定分辨率')
    parser.add_argument('--save_no_coord', type=str, default=False, help='无坐标系保存')
    parser.add_argument('--buffer_field', type=str, default=None, help='精准过滤字段名称')
    parser.add_argument('--list_buffer_name', type=str, default=None, help='精准过滤字段值列表')
    parser.add_argument('--listFeature', type=str, default=None, help='多分类属性字段值字典')
    parser.add_argument('--feature', type=str, default=None, help='多分类属性字段名称')
    parser.add_argument('--consumer_number', type=int, default=None, help='开启进程数量')
    args = parser.parse_args()
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    if args.resolution == 0:
        args.resolution = None

    if args.list_buffer_name == 'None':
        args.list_buffer_name = None
    else:
        args.list_buffer_name = [i for i in args.list_buffer_name.split(',')]

    if args.buffer_field == 'None':
        args.buffer_field = None

    if args.listFeature == 'None':
        args.listFeature = None
    else:
        args.listFeature = {i[0]: int(i[1]) for i in [j.split(':') for j in args.listFeature.split(',')]}

    if args.feature == 'None':
        args.feature = None

    if args.label == 'None':
        args.label = None
    else:
        args.label = [i for i in args.label.split(',')]

    step = (args.step_x, args.step_y)

    if args.angle == "False":
        args.angle = False
    elif args.angle == "True":
        args.angle = True

    if args.move == "False":
        args.move = False
    elif args.move == "True":
        args.move = True

    if args.type_crop == "False":
        args.type_crop = False
    elif args.type_crop == "True":
        args.type_crop = True

    if args.save_no_coord == "False":
        args.save_no_coord = False
    elif args.save_no_coord == "True":
        args.save_no_coord = True

    out_shape = (args.out_shape_x, args.out_shape_y)
    consumer_number = 4

    main(consumer_number=consumer_number, task=args.task, input_shp=args.input_shp, input_tif=args.input_tif,
         input_shp_buffer=args.input_shp_buffer,
         input_tif_change=args.input_tif_change, output_dir=args.output_dir, type_crop=args.type_crop, angle=args.angle,
         out_shape=out_shape, move=args.move, label=args.label, resolution=args.resolution, step=step,
         save_no_coord=args.save_no_coord, buffer_field=args.buffer_field, list_buffer_name=args.list_buffer_name,
         listFeature=args.listFeature, feature=args.feature, callback=None, image_num=None, init_percent=None)
