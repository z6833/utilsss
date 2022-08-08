* 程序入口:<br>
&ensp;&ensp;&ensp;&ensp;main.py<br>
* 运行说明:<br>
    在main.py的main函数中，分别实例化向量表示模型和聚类模型及其对应的参数
    

##### 参数配置
* 向量表示：
    - worker_num: 进程数，默认是计算机核数
* 聚类算法：
    - n_cluster: 聚类类别
    - norm_type: 数据标准化处理方式，可选['minmax', 'standard', None]
    - reduction_type: 降维方式选择，可选['pca', 'tsne', None]
    - view: 聚类结果是否可视化展示, [True, False]
    

##### 评价指标
* 轮廓系数（Silhouette Coefficient）
    - 接近0的值表示重叠的群集。负值通常表示样本已分配给错误的聚类，因为不同的聚类更为相似
* Calinski Harabasz
    - 定义为组间离散与组内离散的比率，该分值越大说明聚类效果越好。

##### 举例说明
```python
    # 设置向量化模型参数
    vector_op = GrayHistogramVector()

    # 设置聚类模型参数
    cluster_op = MinBatchKMeansModel(n_clusters=3, reduction_type='pca', norm_type=None, view=True)
    
    # 聚类分析
    runner = Runner(cropped_dir, vector_op=vector_op, cluster_op=cluster_op)
    _, s_score, c_score = runner.run()
```