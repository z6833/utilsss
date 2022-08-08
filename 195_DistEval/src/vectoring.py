# -*- coding:utf-8 -*-
# @FileName  :build_vector.py
# @Time      :2022/5/24 15:54
# @Author    :zhaolun
import cv2 as cv
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np
import torchvision.models as models
import torch
from PIL import Image
from numpy import linalg as LA

from utils.constants import cores


class BaseVectorRep:

    def __init__(self, worker_num=cores):
        self.worker_num = worker_num

    def build_vector(self, img_path):
        """
        图像向量化表示，不同的向量表示需实重写该函数，返回一个向量。
        :param img_path: 图像所在路径
        :return: 向量表示
        """
        NotImplemented

    def build_vectors(self, img_path_list):
        """
        每张图像，返回一个向量表示；将所有的向量纵向拼接，构成矩阵的形式。
        :param img_path_list: 所有图像所在路径
        :return: 图像的矩阵表示。
        """
        futures = []
        with Pool(processes=self.worker_num) as pool:
            for img_path in tqdm(img_path_list, desc="Parsing image: "):
                res = pool.apply_async(self.build_vector, args=(img_path, ))
                futures.append(res)

            pool.close()
            pool.join()

        hist_mat = np.vstack([fut.get() for fut in futures])
        return hist_mat


class GrayHistogramVector(BaseVectorRep):

    def __init__(self):
        
        super(GrayHistogramVector, self).__init__()

    def build_vector(self, img_path):
        """
        图像的向量表示
        :param img_path: 图像所在路径。
        :return:
        """
        img = cv.imread(img_path, 0)
        hist = cv.calcHist([img], [0], None, [256], [0, 256])
        return hist.flatten()


def build_vgg16(vec_dim):
    """
    加载VGG16的预训练模型；并输出指定维度的向量。
    :param vec_dim: 构造的向量维度
    :return:
    """
    # todo 线性层有一个随机权重，待处理。
    model = models.vgg16(pretrained=True)
    in_features = model.classifier[6].in_features
    model.classifier[6] = torch.nn.Linear(in_features, vec_dim)

    for parameter in model.parameters():
        parameter.requires_grad = False

    return model


def build_resnet50(vec_dim):

    model = models.resnet50(pretrained=True, progress=True)
    in_features = model.fc.in_features
    model.fc = torch.nn.Linear(in_features, vec_dim)
    for p in model.parameters():
        p.requires_grad = False

    return model


def build_resnet101(vec_dim):

    model = models.resnet101(pretrained=True, progress=True)
    in_features = model.fc.in_features
    model.fc = torch.nn.Linear(in_features, vec_dim)
    for p in model.parameters():
        p.requires_grad = False

    return model


class VGG16Vector(BaseVectorRep):

    def __init__(self, vector_dim=10):
        super(VGG16Vector, self).__init__()
        self.model = build_vgg16(vector_dim)

    def build_vectors(self, img_path_list):
        """ 图像的矩阵表示 """

        # todo 修改为多进程写法；当前存在多进程写的时候，内存会爆，导致异常退出。
        matrix = []
        for img_path in tqdm(img_path_list):
            arr = self.build_vector(img_path)
            matrix.append(arr)

        mat = np.vstack(matrix)
        return mat

    def build_vector(self, img_path):

        img = Image.open(img_path)
        img = img.resize((256, 256), Image.NEAREST)  # todo 2000 X 2000的数据较大，导致读取缓慢

        x = torch.from_numpy(np.asarray(img, dtype=np.float32)).transpose(-1, 0)
        x = torch.unsqueeze(x, 0)
        # 前向推理
        x = self.model(x)
        # 模型输出结果标准化
        x = x / LA.norm(x)
        return x.tolist()[0]


class Resnet50Vector(VGG16Vector):

    def __init__(self, vector_dim=10):

        super(Resnet50Vector, self).__init__(vector_dim)
        self.model = build_resnet50(vector_dim)


class Resnet101Vector(VGG16Vector):

    def __init__(self, vector_dim=10):

        super(Resnet101Vector, self).__init__(vector_dim)
        self.model = build_resnet101(vector_dim)


if __name__ == "__main__":

    build_resnet50(10)

    # import os
    # fp = os.path.join('/data_02/不同任务训练测试数据/数据分布网格切片数据/陆良3/GF2-L1A0006361386-20220321', 'GF2L1A000636138620220321C_9_9.tif')
    #
    # vgg = VGG16Vector()
    # num_fc = vgg.model.classifier[6].in_features
    # vec_dim = 10
    # vgg.model.classifier[6] = torch.nn.Linear(num_fc, vec_dim)
    #
    # for param in vgg.model.parameters():
    #     param.requires_grad = False
    #
    # img = Image.open(fp)  # .convert("RGB")
    # img = img.resize((224, 224), Image.NEAREST)
    # x = torch.from_numpy(np.asarray(img, dtype=np.float32)).transpose(-1, 0)
    # x = torch.unsqueeze(x, 0)
    #
    # print(type(x), x.shape)
    # # x = torch.randn(size=(1, 3, 1024, 1024))
    # x = vgg.model(x)
    # vec = x / LA.norm(x)
    # print(vec)


