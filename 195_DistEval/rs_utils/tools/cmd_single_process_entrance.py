# import sys
# import pathlib
# cwd_path = pathlib.Path(__file__).absolute()
# parent_path = cwd_path.parent.as_posix()
# sys.path.append(parent_path)
import argparse
import os
from ..sample_makes import ChangeDetectionSampleMake
from ..sample_makes import SegmentationSampleMake
from ..sample_makes import TargetDetectionSampleMake


class SampleMake:
    def __init__(self, task=None, input_shp=None, input_tif=None, input_shp_buffer=None, input_tif_change=None,
                 output_dir=None, type_crop=None, angle=None, out_shape=None, move=None,
                 label=None, resolution=None, step=None, save_no_coord=None, buffer_field=None,
                 list_buffer_name=None, listFeature=None, feature=None,
                 callback=None, image_num=None, init_percent=None):
        """
                影像切片的基础类
                :param task: 任务类型（1.目标检测 2.语义分割 3.变化检测）
                :param input_shp: 输入的shp矢量路径
                :param input_tif: 输入的栅格影像路径
                :param input_shp_buffer: 输入过滤矢量路径
                :param input_tif_change: 输入变化检测后影像路径
                :param output_dir: 输出的文件夹路径
                :param type_crop: 样本裁剪类型(True:滑窗裁剪，False:图斑裁剪)
                :param angle: 旋转数据增强(True:是，False:否)
                :param out_shape: 输出图像像素尺寸，width和length，如（512，512）
                :param move: 抖动数据增强(True:是，False:否)
                :param label: 标签
                :param resolution: 分辨率
                :param step: 滑窗裁剪步长，length和width，如（512，512）
                :param save_no_coord: 无坐标系保存(True:是，False:否)
                :param buffer_field: 精准过滤字段（默认None)
                :param list_buffer_name: 精准过滤列表（默认None)
                :param listFeature: 多分类属性字典，1，2，3为对应类别的mask rgb值， 二分类设置为None
                :param feature: 多分类属性字段，二分类设置为None
                :param callback: 进度条
                :param image_num: 单个切片任务所所包含样本总数
                :param init_percent: 当前样本所占用进度值（如共5个样本，当前样本是第2个，则init_percent为20%）
        """
        self.task = task
        self.input_shp = input_shp
        self.input_tif = input_tif
        self.input_shp_buffer = input_shp_buffer
        self.input_tif_change = input_tif_change
        self.output_dir = output_dir
        self.type_crop = type_crop
        self.angle = angle
        self.out_shape = out_shape
        self.move = move
        self.label = label
        self.resolution = resolution
        self.step = step
        self.save_no_coord = save_no_coord
        self.buffer_field = buffer_field
        self.list_buffer_name = list_buffer_name
        self.listFeature = listFeature
        self.feature = feature
        self.callback = callback
        self.image_num = image_num
        self.init_percent = init_percent

    def sample_make(self):
        # 任务类型对应类关系
        type_map = {
            "1": TargetDetectionSampleMake,
            "2": SegmentationSampleMake,
            "3": ChangeDetectionSampleMake
        }
        obj = type_map[str(self.task)](
            task=self.task, input_shp=self.input_shp, input_tif=self.input_tif,
            input_shp_buffer=self.input_shp_buffer, input_tif_change=self.input_tif_change,
            output_dir=self.output_dir, type_crop=self.type_crop, angle=self.angle,
            out_shape=self.out_shape, move=self.move, label=self.label,
            resolution=self.resolution, step=self.step, save_no_coord=self.save_no_coord,
            buffer_field=self.buffer_field, list_buffer_name=self.list_buffer_name,
            listFeature=self.listFeature, feature=self.feature,
            callback=self.callback, image_num=self.image_num, init_percent=self.init_percent)
        obj()


if __name__ == "__main__":
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

    sample_m = SampleMake(input_tif=args.input_tif, input_tif_change=args.input_tif_change,
                          input_shp_buffer=args.input_shp_buffer,
                          input_shp=args.input_shp, output_dir=args.output_dir, angle=args.angle, label=args.label,
                          move=args.move,
                          type_crop=args.type_crop, task=args.task, out_shape=out_shape, step=step,
                          resolution=args.resolution,
                          save_no_coord=args.save_no_coord, buffer_field=args.buffer_field,
                          list_buffer_name=args.list_buffer_name, listFeature=args.listFeature, feature=args.feature)
    sample_m.sample_make()
