class DriverError(RuntimeError):
    pass


class DriverBase:
    def load(self,data_obj):
        """
        载入数据方法
        :param data_obj: 数据对象，可以是矢量或者栅格数据
        :return:
        """
        raise NotImplementedError

    def save(self,data_obj,uri=None):
        """
        保存数据方法
        :param data_obj:  数据对象，可以是矢量或者栅格数据
        :param uri: 需要保存的路径
        """
        raise NotImplementedError

    def close(self):
        """释放当前占用资源"""
        raise NotImplementedError


