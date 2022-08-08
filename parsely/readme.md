# Parsley

开箱即用的深度学习微服务基础框架，各深度学习项目依赖该框架实现快速服务搭建。

开发者无需关注web访问、任务调度、进程管理、数据库相关实现细节，只需实现模型加载、参数验证、模型预测等几个方法，即可轻松完成微服务搭建。

## Feature
* **基于flask框架**
  * 微服务框架基于flask框架实现，搭建轻量化web应用
* **多进程任务调度**
  * 实现进程安全级消息队列，多进程并发执行任务
  * 微服务启动时，自动恢复之前未完成的任务，重新加入队列中执行
* **优雅的BaseService封装**
  * 提供预先定义好的任务提交、终止任务、任务查询、任务结果下载几个Service，直接注册即可
  * 开发者只需继承BaseService，并实现模型加载、参数验证、模型预测等几个方法，无需关心底层实现细节
* **统一的ServiceManager** 
  * 方便地service管理，想注册哪个Service就注册哪个
* **统一的数据访问接口**
  * 支持sqlite、mysql数据库，自动完成建表操作
* **集成配置中心、注册中心**
  * 简单易懂的本地配置文件
  * 支持从apollo配置中心获取配置信息，支持动态更新
  * 支持注册到eureka注册中心
* **进程安全级的日志模块**
  * 详细的日志文件

## Requirements:
* python 3.6/3.6+
* requests 2.24.0
* aiohttp 3.7.2
* Flask 1.1.1
* flask-restful 0.3.7
* flask-sqlalchemy 2.4.0
* py-eureka-client 0.7.4
* pymysql 0.10.1

## Examples
`examples`目录包含违建、漂浮物检测的示例代码和配置文件，可根据需求参考对应代码。
* 违建检测的请求参数为输入影像路径、概率阈值、输出结果路径，输入影像需提前上传到微服务所在服务器上，输出结果需用户自行在该服务器上访问。
* 漂浮物检测的请求参数为用户上传图片，输出结果为预测结果图片、预测数量，可通过`download`接口获取预测结果图片url及预测数量信息。

## Documentation
### 自定义类开发
需要开发者继承`BaseService`类，并实现部分方法，包含`task_type`、`url`、`setup_models`、`params`、`check_params`、`do_task`，并根据实际需要选择性地调用`update_progress`方法。

各方法具体说明参考`service/base_service.py`中`BaseService`类中的方法注释。

### 微服务配置
需要在运行微服务时传递配置文件`config.ini`的路径，使得微服务获取配置信息，并根据是否是`独立模式`，选择是否连接配置中心和注册中心。

* 若为独立模式，则不连接配置中心和注册中心，仅使用本地`config.ini`中的配置。

* 若不为独立模式，则获取配置中心的配置信息，并与本地配置融合成新的配置信息，写入文件`run.config.ini`。同时将微服务注册到注册中心。微服务启动时读取`run.config.ini`中的配置。

本地配置文件格式及说明如下，参考`examples/example_illegal_building_detection_config.ini`文件：
```ini
[configurations]
# 是否使用独立模型，若是，则不使用配置中心和注册中心
is_standalone = True
# 当前微服务的app_id，用于创建数据库的任务表、连接配置中心、注册中心
app_id = igis-illegal-building-detection
# 网关所在ip，非独立模式下构建文件url使用
gate.host = 172.20.20.1
# 网关端口号，非独立模式下构建文件url使用
gate.port = 9387
# 当前微服务所在ip
server.host = 172.20.20.198
# 当前微服务（宿主机）监听端口，端口号
server.port = 5000
# 容器监听端口号，需要在docker run时，传-p参数与server.port进行映射
container.port = 5000
# 配置中心url
config.url = http://172.20.20.1:8080
# 注册中心url
eureka.url = http://172.20.20.1:8080/eureka
# 数据库方言
database.dialect = mysql
# 数据库引擎
database.driver = pymysql
# 连接数据库用户名
database.username = root
# 连接数据库密码
database.password = root
# 数据库服务所在ip
database.host = 172.20.20.196
# 数据库服务端口
database.port = 3306
# 数据库实例名
database.dbname = igis-dl
# 当前微服务下用户自定义的BaseService所用进程数，用于实现多任务并行，最小为1，即单一子进程串行执行任务
service.illegal_building_detection.num_woker = 2
# 缓存根目录，支持绝对和相对路径，用于存储post接口上传的文件和输出的结果文件，并支持url访问
cache.root.dir = cache_data
# 用户上传文件的缓存目录，相对于缓存根目录的路径
cache.input_files.dir = inputfiles
# 输出结果文件的缓存目录，相对于缓存根目录的路径
cache.output_files.dir = outputfiles
```
### 参数验证
* 开发者需在自定义类中重写`params`方法，在方法体中定义用户http请求需要验证的参数名、参数类型、错误提示信息，支持整型、浮点型、字符串、文件类型验证。
* 开发者需在自定义类中重写`check_params`方法，在方法体中，对如上定义的参数做进一步更详细的验证，并返回符合规范的内容。
* 对于用户上传的文件，微服务会自动将其保存到配置文件中定义的缓存输入目录下，并在`check_params`方法中将该文件路径作为参数传入
* 开发者若需要下载模型输出结果文件，需要在`check_params`方法中构造`OutputParams`后，在其`add_params`方法中传入输出文件的key、输出文件名，并设置`use_cache_dir`为`True`，具体可参考漂浮物示例代码。

## Usage
本微服务框架使用方法：
* 第一步，进入你自己的项目目录下，执行如下命令，将Parsley添加为子模块并自动clone下来：

`git submodule add http://192.168.10.185:8081/whrdc/parsley.git`

**注意：子模块与父模块也存在版本依赖关系，添加子模块后，需要在你自己的项目目录下，commit子模块，并push，才能更新父子依赖关系到服务器。如果子模块目录中没有文件，在父模块目录下执行`git submodule update --init`命令，才会将子模块拉下来。当远程的子模块代码有更新时，进入到子模块目录下，使用git pull命令拉取最新子模块代码，并在父模块目录下commit和push，以更新父模块与子模块的依赖。**
* 第二步，创建`config.ini`文件，并参考`examples/*_config.ini`文件内容，配置你自己项目的各项参数
* 第三步，创建`app.py`文件，并参考`examples/example_*.py`文件内容，集成微服务框架代码
* 第四步，直接运行`python app.py config.ini`，即可启动微服务，若不传配置文件路径，则无法启动微服务

在`app.py`代码中，开发者需要自定义类并继承BaseService，同时实现如下几个方法，以违建检测为例，参考代码如下：
```python
import os
from parsley.utils.log import logger
from parsley.service.argument import ReqArgument, ReqArgumentType, OutputParams
from parsley.service.base_service import BaseService, StopService, GetTaskService, GetTasksService
from parsley.service.service_manager import _service_manager
from tools.ObjectDetection_new import ObjectDetection


class IllegalBuildingDetectionService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def task_type(self):
        """
        设置Service的任务类型，由子类重写该方法，该值会记录在数据库任务表中任务类型字段中
        """
        return "illegal_building_detection"

    def url(self):
        """
        设置Service的url，由子类重写该方法，该值会用于注册api接口，这样用户可以通过url访问该接口
        """
        return "/predict"

    def setup_models(self):
        """
        微服务启动前模型初始化工作，会开启子进程执行该函数。子类自行实现，需要确保模型仅在此函数中加载，而没有在主进程中加载，否则存在CUDA张量进程间通信问题。该方法不用子类调用
        """
        logger.info("illegal building detection model setup")
        # 定义投影坐标系
        prjWkt = 'PROJCS["CGCS2000_3_degree_Gauss_Kruger_CM_114E",GEOGCS["GCS_China_Geodetic_Coordinate_System_2000",DATUM["unknown",SPHEROID["Unknown",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",114],PARAMETER["scale_factor",1],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'

        # 实例化违建检测器
        detector = ObjectDetection(('__background__', 'unapprovedconstruction'), 'res101',
                                   'models/illegalbuilding/res101_faster_rcnn_iter_530000.ckpt')
        detector.setCropParamsByGeo(50, 50, 15, 15, prjWkt)
        self.detector = detector
        pass

    def params(self):
        """
        设置Service需要验证的参数列表，利用flask-restful自带的验证方法验证http请求参数。返回ReqArgument的list。需要子类自行实现
        """
        params_list = list()
        # 得分阈值，必填，float类型
        score_thresh = ReqArgument('scorethresh', ReqArgumentType.FLOAT, True, "scorethresh should be float!")
        # 输入影像服务器路径，必填，string类型
        input_image = ReqArgument('inputimage', ReqArgumentType.STRING, True, "inputimage cannot be blank!")
        # 输出shp服务器路径，必填，string类型
        output_shp = ReqArgument('outputshp', ReqArgumentType.STRING, True, "outputshp cannot be blank!")
        params_list.append(score_thresh)
        params_list.append(input_image)
        params_list.append(output_shp)
        return params_list

    def check_params(self, params):
        """
        对用户发送的请求进行参数校验，子类自行实现校验方法，并返回校验结果，验证通过后，input_params和output_params会写入数据库task记录中。该方法不用子类调用
        该方法返回值中的input_params和output_params将作为参数传入do_task方法中，用于模型的预测。故需要开发者在这两个参数中记录do_task需要用到的信息，
        如输入路径、概率阈值放入input_params中，输出路径、输出文件名放入output_params中
        :param params: 用户请求参数dict
        :return: 校验结果，返回格式二元组(is_success, data),若成功，则data为(input_params, output_params)；若失败，则data为errmsg字符串
        """
        logger.info('check_params: {}'.format(params))
        score_thresh = params['scorethresh']
        if score_thresh >= 1.0 or score_thresh <= 0.0:
            return False, "scorethresh should between 0.0 and 1.0"
        input_image = params['inputimage']
        if not os.path.exists(input_image):
            return False, "inputimage {} Not Exists".format(input_image)
        output_shp = params['outputshp']
        output_shp_dirname = os.path.dirname(output_shp)
        # 如果shp目录不存在，则提示目录不存在
        if not os.path.exists(output_shp_dirname):
            return False, "Dir of outputshp {} Not Exists".format(output_shp)
        # 判断输出路径是否是shp文件，若不是，则提示
        ext = os.path.splitext(output_shp)[1]
        if ext != ".shp":
            return False, "Extention of outputshp {} Should Be .shp".format(output_shp)
        # 输入参数信息
        input_params = {'inputimage': input_image, 'scorethresh': score_thresh}
        # 构造输出参数对象
        output_params_obj = OutputParams()
        # 若输入文件为上传文件，则输出文件路径使用缓存输出目录
        # 若输入和输出都是指定的服务器路径，则不使用缓存目录
        output_params_obj.add_param("outputshp", output_shp, False)
        return True, (input_params, output_params_obj.as_dict())

    def do_task(self, task_id, input_params, output_params):
        """
        模型预测的函数，接收从数据库task记录中获取的input_params和output_params，子类自行实现调用模型预测相关脚本，并返回执行结果。该方法不用子类调用
        该方法返回值中的output_params将被用于更新数据库对应task记录中outputparams字段的内容。
        开发者可根据需要，修改返回体中output_params中的内容，如记录预测结果bbox数量、分类类别等信息，这样调用download接口时，即可查看对应预测结果信息
        e.g. output_params['count'] = 9
        若无需修改，则保持output_params不变返回
        :param task_id: 任务id
        :param input_params: 输入dict
        :param output_params: 输出dict
        :return: 执行结果，返回格式二元组(is_success, data),若成功，则data为output_params；若失败，则data为errmsg字符串
        """
        logger.info("do task {}, input: {}, output: {}".format(task_id, input_params, output_params))
        score_thresh = input_params['scorethresh']
        input_image = input_params['inputimage']
        output_shp = output_params['outputshp']
        is_success, data = self.detector.predictImage(task_id, input_image, output_shp, score_thresh, self.processCb)
        if is_success:
            data = output_params
        return is_success, data

    # 每次预测完一张切片的回调函数，根据需求做相应处理
    def processCb(self, taskid, finishedCount, totalCount):
        #@print('Task {} FinishedCount: {} / {}'.format(taskid, finishedCount, totalCount))
        progress = round(float(finishedCount) / totalCount * 100)
        # 更新db中任务进度
        self.update_progress(taskid, progress)
```
然后在main函数中，将自定义Service注册到service_manager中，启动service_manager即可，参考代码如下：
```python
if __name__ == "__main__":
    # 实例化开发者继承BaseService自定义的类
    ibd = IllegalBuildingDetectionService()
    # 调用__call__方法，传入子进程数，用于任务并行，子进程数最小为1
    ibd(_service_manager.config['service.illegal_building_detection.num_woker'])
    # 实例化框架预定义的停止任务service
    stop = StopService()
    # 实例化框架预定义的获取特定任务信息的service
    get_task = GetTaskService()
    # 实例化框架预定义的获取所有任务信息的service
    get_tasks = GetTasksService()
    # 注册各service到_service_manager中
    _service_manager.register_service(ibd)
    _service_manager.register_service(stop)
    _service_manager.register_service(get_task)
    _service_manager.register_service(get_tasks)
    # 启动微服务
    _service_manager.start()
    pass
```

## Test
开发者需要安装Postman，用于对自定义service进行测试，以违建为例：
* **提交预测任务：**
  * **url**: 172.20.20.199:5000/predict
  * **method**: Post
  * **http body**: 
    * scorethresh: 0.2
    * inputimage: /code/haizhu_cl1.tif
    * outputshp: /code/haizhu3.shp
* **查询指定任务信息：**
  * **url**: 172.20.20.199:5000/task/`<taskid>`
  * **method**: Get
* **获取满足查询条件的任务信息，最新在最前：**
  * **url**: 172.20.20.199:5000/tasks
  * **method**: Get
  * **http params**: 
    * pagenum: 第几页，必填，最小1
    * pagesize: 每页返回数量，选填，默认10个
    * status: 任务状态，选填，默认-1，返回所有任务；0：等待中；1：成功；2：失败；3：执行中
* **终止指定任务：**
  * **url**: 172.20.20.199:5000/stop
  * **method**: Post
  * **http body**: 
    * taskid: 任务号
* **下载指定任务预测结果：**
  * **url**: 172.20.20.199:5000/download`<taskid>`
  * **method**: Get

## Logger
使用日志请在代码头部引用：`from parsley.utils.log import logger`

默认日志级别为info，可通过 `logger.setLevel(logging.INFO)`修改日志级别。

使用logger.info(/debug/warning/error)可打印不同级别的日志，日志格式如下：

`2020-10-23 01:23:06,117 - service_manager.py - Line: 38 - [INFO] - Service /predict registered`
