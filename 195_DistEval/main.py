# -*- coding:utf-8 -*-
# @FileName  :main.py
# @Time      :2022/5/24 15:41
# @Author    :zhaolun
import os
import numpy as np

from src.vectoring import GrayHistogramVector, VGG16Vector, Resnet50Vector, Resnet101Vector
from src.cluster import MinBatchKMeansModel, AgglomerativeClusteringModel, DBSCANModel
from utils.constants import cropped_dir


class Runner:

    def __init__(self, cropped_dir, vector_op, cluster_op):
        """
        :param cropped_dir: 裁剪后的数据所在路径
        :param vector_mod: 向量表示模型
        :param cluster_mod: 聚类模型
        """
        self.cropped_dir = cropped_dir
        self.vector_op = vector_op
        self.cluster_op = cluster_op

    def get_imgs_path(self):
        """
        文件所在路径，及该路径下所有的tif文件；
        :return: 字典; key=path, value=[fp1, fp2, ...]
        """
        img_dict = {}
        for root, dirs, filenames in os.walk(cropped_dir):
            filenames = [name for name in filenames if name.endswith('.tif')]
            if filenames:
                img_path_list = [os.path.join(root, name) for name in filenames]
                img_dict[root] = img_path_list

        return img_dict

    def convert_images(self, path_imgs):
        """
        将图像转化向量；多个图像拼接成为矩阵；shape=(n_samples, features)
        :param path_imgs:图像存放路径
        :return:标签，向量表示拼接成的矩阵
        """
        matrix = []
        labels = []
        for index, item in enumerate(path_imgs.items()):

            # 调用向量化表示模型的函数，返回所有图像的向量表示，并拼接成矩阵形式。
            mat = self.vector_op.build_vectors(item[1])
            labels += [index] * mat.shape[0]
            matrix.append(mat)

        return labels, np.vstack(matrix)

    def get_cluster_result(self, data, labels):
        """
        返回聚类结果
        :param data: 所有图像的向量构成的矩阵
        :param labels:给图像构造的标签
        :return:评价指标，及预测的标签。
        """

        y_pred, s_score, c_score = self.cluster_op.cluster_(data, labels)
        return y_pred, s_score, c_score

    def run(self):

        # 1. 获取所有键值对表示的文件路径及对应的文件名
        path_imgs = self.get_imgs_path()

        # 2. 将imgs转化为对应向量表示的矩阵，及其对应的标签
        labels, matrix = self.convert_images(path_imgs)

        # 3. 聚类分析
        y_pred, s_score, c_score = self.get_cluster_result(data=matrix, labels=labels)
        return y_pred, s_score, c_score


def main():
    """
    s_score: 轮廓系数（Silhouette Coefficient），最佳值为1，最差值为-1。
    v_score: 取值在[0, 1]之间，同质性（homogeneity）度量h和完整性（completeness）度量c值的调和平均值，类似与F值；
    c_score: 定义为组间离散与组内离散的比率，该分值越大说明聚类效果越好。
    """

    # 设置向量化模型参数
    vector_op = GrayHistogramVector()
    # vector_op = VGG16Vector(vector_dim=10)
    # vector_op = Resnet101Vector(vector_dim=10)

    # 设置聚类模型参数
    cluster_op = MinBatchKMeansModel(n_clusters=3, reduction_type='pca', norm_type=None, view=True)
    # cluster_op = DBSCANModel(n_clusters=3, reduction_type=None, norm_type=None, view=True)
    # cluster_op = AgglomerativeClusteringModel(n_clusters=5, reduction_type='pca', norm_type='standard', view=True)

    # 聚类分析
    runner = Runner(cropped_dir, vector_op=vector_op, cluster_op=cluster_op)
    _, s_score, c_score = runner.run()

    print(s_score, c_score)
    return


if __name__ == "__main__":
    main()
