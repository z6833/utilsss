# rs-utils

遥感影像通用操作库，所有遥感影像切片、样本生成、后处理相关操作都封装在此，各项目可利用该库进行遥感影像相关数据处理。

## Modules:
* ##base: 
    ###data_base.py:数据初始化：
    ###driver_base.py:驱动初始化：
* ##sample_make: 数据集制作 
    ### sample_making_bace.py:
      数组制作的基类
    ### sample_making_bace.py:
      样本制作脚本，支持目标检测、实例分割、变化检测
      任务类型 1、目标检测 2、实例分割 3、变化检测
      parser.add_argument('--task', type=int, default=1, help='任务类型')
      parser.add_argument('--input_tif', type=str, default=None, help='输入tif路径')
      parser.add_argument('--input_tif_change', type=str, default=None, help='输入tif后时像路径')
      parser.add_argument('--input_shp_buffer', type=str, default=None, help='缓冲区约束')
      parser.add_argument('--input_shp', type=str, default=None, help='输入shp路径')
      parser.add_argument('--output_dir', type=str, default=None, help='输出路径')
      parser.add_argument('--angle', type=bool, default=False, help='旋转数据增强')
      parser.add_argument('--move', type=bool, default=False, help='偏移数据增强')
      parser.add_argument('--type_crop', type=bool, default=False, help='数据裁剪方式')
      parser.add_argument('--out_shape', type=int, default=(600,600), help='输出像素尺寸',nargs='+')
      parser.add_argument('--step', type=int, default=None, help='滑窗裁剪步长',nargs='+')
      parser.add_argument('--resolution', type=int, default=None, help='指定分辨率')
      parser.add_argument('--label', type=str, default=None, help='目标检测生成label')
      eg:
      python  sample_make.py  --input_tif '/data_11/rs-house/illegally_built_coco/illegally_built/train/test/batch_1/0525/052501_haizhu_guanzhou.tif'   
      --input_shp '/data_11/rs-house/illegally_built_coco/illegally_built/train/test/batch_1/0525/海珠.shp'  
      --output_dir "/zsr_08/change_test_zz" --task 1 --step 300 300   --type_crop True  --out_shape 800 800

    ### change_detection_sample_making.py
      变化检测样本制作
      输入：前后时像tif和shp
      输出：前后时像裁剪后的tif和对应的mask标签以及对应的csv
      参数设置：
      out_shape = (600, 600)  # outputShape 为输出数据的通道和像素尺寸
      step = (600, 600)  # 滑窗裁剪步长，设置为outputShape大小时为无重叠裁剪
      move = False  # 随机偏移量，不需偏移请设置为False
      angle = False  # angle=False 为不旋转
      resolution = None  # (1, -1)分辨率设置为None时不改变分辨率 后一位为负号
      type_crop = True  # slideWin=False 为图斑裁剪，设置为True为滑窗裁剪

    ### segmentation_sample_making.py
      实例分割样本制作
      输入：tif和shp
      输出：裁剪后的tif，对应的mask标签，对应的csv
    ### target_detection_sample_making.py
      目标检测样本制作
      输入：tif和shp
      输出：裁剪后的tif，对应的json标签，需统一转为coco的训练标签Make_dataset/labelme_to_coco.py
* ##rasters: 栅格处理
    ### driver.py：
    ### raster.py:进行栅格数据裁剪操作：
* ##shapes: 矢量处理
    ### driver.py：
    ### shapes.py:进行矢量数据裁剪操作：

* test: 功能测试
    ### test_cropper.py：批量裁剪测试（对应裁剪及坐标系转换）
    ### test_make_DataSet.py：
      1、test_spot(self):数据图斑裁剪测试：
      2、test_slide_win(self):数据滑窗裁剪测试：
      3、test_spot_Rotate(self):数据图斑旋转裁剪测试：
    ### test_raster.py：栅格裁剪测试
    ### test_shape.py：矢量裁剪测试


