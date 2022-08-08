from functools import partial
import os
import pathlib
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'rs_utils'))

from rs_utils.sample_makes.sample_make_bace import SampleMakeBase
from rs_utils.rasters.raster import RasterData

class GridClip(SampleMakeBase):
    def __init__(self, input_tif, output_dir, out_shape=(2000,2000), step=(2000,2000)):
        
        super().__init__(
            task=2, 
            input_tif=input_tif,
            out_shape=out_shape,
            step=step,
            output_dir=output_dir,
            type_crop=True,
            callback=partial(print, end='%   \r')
        )
        self.tif_name = pathlib.Path(input_tif).stem

    def _init_dir(self):
        output_dir = pathlib.Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    def _init_load(self):
        """
        初始化并加载影像
        """
        # 样本加载
        self.rs = RasterData.build_file(self.input_tif)
        self.left, self.bottom, self.right, self.top = self.rs.region
        self.rs.load()
        self.out_shape_rs = (self.rs.count, self.out_shape[0], self.out_shape[1])
        self.shp_buffer = None

    def judge_win(self, crop_win):
        # todo 函数命名有歧义，judge或者check应该返回bool值，此处表示对样本进行裁剪
        """
        判断将要切片的样本是否符合要求
        :param crop_win:
        :return:
        """
        if not crop_win:
            return None
        if crop_win.left < self.left or crop_win.right > self.right or \
                crop_win.top > self.top or crop_win.bottom < self.bottom:
            return None
        # crop_shp = self.shp.crop(crop_win)
        # 跳过空白图像
        # if not crop_shp.data:
        #     return None
        crop_rs = self.rs.crop(crop_win, out_shape=self.out_shape_rs)
        # 跳过全空影像
        if np.all(crop_rs.data == 0):
            return None
        # 图片像素占比大于一半进行保存
        if np.count_nonzero(crop_rs.data, axis=None) / np.size(crop_rs.data) < 0.95:
            return None
        return [crop_rs, None]

    def __call__(self):
        row = 0
        col = 0
        last_y = None

        total_num = len(self.data_coordinator)
        for num, item in enumerate(self.data_coordinator):
            if last_y is None:
                last_y = item[1]
            elif item[1] != last_y:
                row += 1
                col = 0
                last_y = item[1]
            
            # 窗口选择
            crop_win = self.get_win(item=item)

            crop_result = self.judge_win(crop_win)
            if crop_result is None:
                continue
            crop_rs, crop_shp = crop_result

            # 保存切片的image
            save_name = "{}_{}_{}.tif".format(self.tif_name, row, col)
            self.img_save(crop_rs, self.output_dir, save_name)

            col += 1

            if (self.callback is not None) and num % 5 == 0:
                progress = (num / total_num) * 100
                self.callback(int(progress))

        if self.callback is not None:
            self.callback(100)


if __name__ == '__main__':
    g = GridClip(
        '/mnt/cephfs/deeplearning/data/archive/语义分割数据/非农影像图斑/2021_云南地矿院耕地数据/202205全部影像/陆良3/GF2-L1A0006361386-20220321/GF2L1A000636138620220321C.tif',
        '/mnt/cephfs/deeplearning/data/clip_test',
        out_shape=(2000, 2000),
        step=(2000, 2000)
    )
    g()
    print('done')

