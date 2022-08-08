# -*- coding:utf-8 -*-
# @FileName  :cluster.py
# @Time      :2022/5/24 15:45
# @Author    :zhaolun
import time
from sklearn.cluster import MiniBatchKMeans, DBSCAN, AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import matplotlib.pyplot as plt
from itertools import cycle
import logging
from sklearn import metrics

from utils.constants import random_state

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class BaseModel:

    def __init__(self, n_clusters, reduction_type=None, norm_type=None, view=False, name="ClusterResult"):
        """
        聚类模型父类
        :param n_clusters: int, 聚类列别
        :param reduction_type: str, default=None; pca:使用PCA降维; tsne: 使用tsne降维
        :param norm_type: str, default=None; 数据标准化处理方式；None: 不做标准化处理；minmax: 最大最小值标准化；standard
        :param view: bool, default=False; 是否聚类结果可视化
        """

        self.n_clusters = n_clusters
        self.reduction_type = reduction_type
        self.norm_type = norm_type
        self.view = view
        self.scaler = None
        self.fit_flag = False
        self.model = None
        self.name = name

    def reduction(self, X):
        """
        数据降维
        :param X:
        :return:
        """

        assert self.reduction_type in [None, 'pca', 'tsne'], "降维类型错误"

        if self.reduction_type is not None:
            logging.info("reduction processing .")
            if self.reduction_type == 'pca':
                reduction_func = PCA(n_components=10, random_state=random_state)
            else:
                reduction_func = TSNE(n_components=3, random_state=random_state)

            start_time = time.time()
            X = reduction_func.fit_transform(X)
            logging.info("reduction processing finished with seconds: {} s".format(round(time.time() - start_time), 2))

        return X

    def normalize(self, X):
        """
        数据标准化处理，按照norm_type的值，进行标准化处理
        :param X:
        :return:
        """

        assert self.norm_type in ['minmax', 'standard', None], '数据标准化类型指定错误'

        if self.norm_type is None:
            return X

        if self.norm_type == 'minmax':
            self.scaler = MinMaxScaler()
        else:
            self.scaler = StandardScaler()

        X = self.scaler.fit_transform(X)
        return X

    def evaluate(self, X, y, y_pred):
        """
        对模型性能进行评估,
        s_score: 轮廓系数（Silhouette Coefficient），最佳值为1，最差值为-1。
                接近0的值表示重叠的群集。负值通常表示样本已分配给错误的聚类，因为不同的聚类更为相似
        v_score: 取值在[0, 1]之间，同质性（homogeneity）度量h和完整性（completeness）度量c值的调和平均值，类似与F值；
        c_score: 定义为组间离散与组内离散的比率，该分值越大说明聚类效果越好。
        :param X:输入数据
        :param y: 标签
        :return: 预测的标签；c-score, v-score
        """

        assert self.fit_flag, "model is not fitted yet ."

        s_score = metrics.silhouette_score(X, y_pred)
        # v_score = metrics.v_measure_score(y, y_pred)
        c_score = metrics.calinski_harabasz_score(X, y_pred)
        return y_pred, round(s_score, 6), round(c_score, 6)

    def cluster_(self, X, y):
        """
        聚类整体流程实现
        :param X: 输入数据
        :param y: 数据标签，针对有标签数据；主要看评估结果是否关注标签内容
        :return: c_score和s_score两个评估指标的值
        """

        # 数据标准化
        X = self.normalize(X)

        # 数据降维
        X = self.reduction(X)

        # 聚类分析
        start_time = time.time()
        y_pred = self.model.fit_predict(X)

        # report = metrics.classification_report(y, y_pred)
        # print(report)

        self.fit_flag = True

        logging.info("fitted with time {} seconds".format(round(time.time() - start_time, 2)))
        _, s_score, c_score = self.evaluate(X, y, y_pred)

        # 可视化呈现
        if self.view:
            self.plot(X, y_pred, name=self.name)

        return y_pred, s_score, c_score

    def plot(self, X, y_pred, name):

        colors = cycle("bgrcmykbgrcmykbgrcmykbgrcmyk")
        for k, col in zip(range(self.n_clusters), colors):
            my_members = y_pred == k
            cluster_center = self.model.cluster_centers_[k]
            plt.plot(X[my_members, 0], X[my_members, 1], col + ".")
            plt.plot(
                cluster_center[0],
                cluster_center[1],
                "o",
                markerfacecolor=col,
                markeredgecolor="k",
                markersize=14,
            )
        plt.title(f"cluster: {self.n_clusters}/{self.norm_type}/{self.reduction_type}")
        plt.savefig(f"{name}_{self.n_clusters}_{self.norm_type}_{self.reduction_type}.png")
        plt.show()
        return

    def plot_(self, X, y_pred, name):

        plt.style.use('ggplot')

        fig, axs = plt.subplots(ncols=2, nrows=1)
        ax1, ax2 = axs.flat

        # scatter plot (Note: `plt.scatter` doesn't use default colors)
        ax1.scatter(X[:, 0], X[:, 1], s=60, c='gray')
        ax1.set_title('Before')

        ax2.scatter(X[:, 0], X[:, 1], s=60, c=y_pred)
        ax2.set_title("Cluster")

        fig.suptitle(f"cluster: {self.n_clusters}/{self.norm_type}/{self.reduction_type}")
        plt.savefig(f"{name}_{self.n_clusters}_{self.norm_type}_{self.reduction_type}.png")
        plt.show()

        return


"""
继承BaseModel，在__init__里面实现各个不同模型实例化过程。
"""


class MinBatchKMeansModel(BaseModel):

    def __init__(self, n_clusters, reduction_type, norm_type, view=False, name="Kmeans"):
        super(MinBatchKMeansModel, self).__init__(n_clusters, reduction_type, norm_type, view, name)

        # self.model = MiniBatchKMeans(n_clusters, random_state=random_state)
        self.model = KMeans(n_clusters, random_state=random_state)


class DBSCANModel(BaseModel):

    def __init__(self, n_clusters, reduction_type, norm_type, view=False, name="dbscan"):
        super(DBSCANModel, self).__init__(n_clusters, reduction_type, norm_type, view, name)

        self.model = DBSCAN(eps=0.05, min_samples=3)


class AgglomerativeClusteringModel(BaseModel):

    def __init__(self, n_clusters, reduction_type, norm_type, view=False, name="Agglomerative"):
        super(AgglomerativeClusteringModel, self).__init__(n_clusters, reduction_type, norm_type, view, name)

        self.model = AgglomerativeClustering(n_clusters)