#!/usr/bin/env python3

"""
@author: l00511303
@since: 
"""

import sys
import time
import numpy as np
import pymongo
from pymongo.errors import PyMongoError
from torch.utils.data import Dataset
from tqdm import tqdm


class MongoDataset(Dataset):

    def __init__(self,
                 host,
                 db,
                 coll,
                 match,
                 project,
                 auth_db='admin',
                 user=None,
                 passwd=None,
                 fn=None,
                 read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED):
        self._host = host
        self._db = db
        self._coll_name = coll
        self._match = match if match is not None else {}
        self._project = project
        self._auth_db = auth_db
        self._user = user
        self._passwd = passwd
        self._fn = fn
        self._read_preference = read_preference

        self._id_list = []
        with pymongo.MongoClient(
                self._host,
                read_preference=read_preference,
                maxPoolSize=5
        ) as conn:
            if user is not None:
                conn[auth_db].authenticate(user, passwd)
            coll = conn[db][coll]
            size = coll.count_documents(match) if match else coll.estimated_document_count()

            cur = coll.find(match, {'_id': 1}).batch_size(8192)
            for doc in tqdm(
                    cur,
                    total=size,
                    desc=f'Scanning "{self._coll_name}"',
                    leave=False,
                    unit=' samples',
                    unit_scale=True):
                self._id_list.append(doc['_id'])

        self._conn = None
        self._coll = None
        self._cache = {}

    def __del__(self):
        if self._conn is not None:
            self._conn.close()

    def __len__(self):
        return len(self._id_list)

    def __getitem__(self, index):
        doc = None
        try:
            doc = self._find_item(index)
        except PyMongoError as e:
            while True:
                print(f'Exception {str(e)} retry after 7 seconds.', file=sys.stderr)
                time.sleep(7)
                try:
                    doc = self._find_item(index)
                    break
                except PyMongoError:
                    continue
        if self._fn is not None:
            doc = self._fn(doc)
        return doc

    def _find_item(self, index):
        _id = self._id_list[index]
        if self._coll is None:
            self._conn = pymongo.MongoClient(
                self._host,
                read_preference=self._read_preference,
                maxPoolSize=5
            )
            if self._user is not None:
                self._conn[self._auth_db].authenticate(self._user, self._passwd)
            self._coll = self._conn[self._db][self._coll_name]

        doc = self._coll.find_one({'_id': _id}, self._project)
        if self._fn is not None:
            doc = self._fn(doc)
        return doc


class MongoDatasetX(Dataset):
    """ 从多个数据表中抽取部分样本，并合并到一个表中

    Attributes:
        host: 要合并的各个表所在的数据库的ip.
        db: 要合并的各个表所在的数据库名.
        sample_list: 要合并的（表名，id） list.
        project: 属性过滤条件
        auth_db: 验证用户名
        user: 数据库用户名
        passwd: 数据库用户的密码
        fn: 数据后处理函数（如果数据库读取出来的数据是编码数据，需要解码或者其他处理，用户自定义fn函数内容）

    Returns: None

    :Example:

    .. sourcecode:: python

        from fastdata import common
        from fastdata.loader import dataset, adapter
        from torch.utils.data import ConcatDataset, DataLoader
        import tqdm
        import argparse
        from PIL import Image
        import io
        import numpy as np

        def fn(doc):
            dataio = doc['data']
            data = io.BytesIO(dataio)
            data = Image.open(data,'r')
            data = np.array(data)
            return data

        def main(args):
            host = 'xx.xx.x.xx'
            user = 'xx'
            password = 'xx'
            mongo = common.MongoServer( host=host, user=user, password=password)
            conn = mongo.connect()

            pair = conn['test_x']['pair']
            sample_list = []
            for doc in pair.find():
                coll_name = doc['coll_name']
                id = doc['id']
                print(f"coll_name {coll_name} id {id}")
                sample_list.append((coll_name,id))

            data = dataset.MongoDatasetX(host=host,
                         db='test_x',
                         sample_list = sample_list,
                         project=None,
                         auth_db='admin',
                         user=user,
                         passwd=password,
                         fn=fn)
            print(type(data))
            train_data_loader = DataLoader(data, batch_size=28, shuffle=True, num_workers=10)
            for epoch in range(100):
                for i, doc in enumerate(tqdm.tqdm(train_data_loader, desc=f'Epoch {epoch}')):
                    # your train code
                    pass

            return 0

        if __name__ =='__main__':
            _parser = argparse.ArgumentParser()
            _args = _parser.parse_args()
            main(_args)

    """

    def __init__(self,
                 host,
                 db,
                 sample_list,
                 project=None,
                 auth_db='admin',
                 user=None,
                 passwd=None,
                 fn=None,
                 read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED):
        self._host = host
        self._db = db
        self._sample_list = sample_list
        self._project = project
        self._auth_db = auth_db
        self._user = user
        self._passwd = passwd
        self._fn = fn
        self._read_preference = read_preference

        self._conn = None
        self._coll_dict = {}

    def __del__(self):
        if self._conn is not None:
            self._conn.close()

    def __len__(self):
        return len(self._sample_list)

    def __getitem__(self, index):
        doc = None
        try:
            doc = self._find_item(index)
        except PyMongoError as e:
            while True:
                print(f'Exception {str(e)} retry after 7 seconds.', file=sys.stderr)
                time.sleep(7)
                try:
                    doc = self._find_item(index)
                    break
                except PyMongoError:
                    continue
        if self._fn is not None:
            doc = self._fn(doc)
        return doc

    def _find_item(self, index):
        coll_name, _id = self._sample_list[index]
        if self._conn is None:
            self._conn = pymongo.MongoClient(
                self._host,
                read_preference=self._read_preference,
                maxPoolSize=5
            )
            if self._user is not None:
                self._conn[self._auth_db].authenticate(self._user, self._passwd)
        if coll_name not in self._coll_dict:
            coll = self._conn[self._db][coll_name]
            self._coll_dict[coll_name] = coll
        coll = self._coll_dict[coll_name]
        return coll.find_one({'_id': _id}, self._project)


def encode_numpy(a: np.ndarray):
    return a.tobytes('C'), str(a.dtype), ','.join(str(size) for size in a.shape)


def decode_numpy(data, copy=False):
    assert isinstance(data, (tuple, list)) and len(data) == 3
    shape = data[2]
    if isinstance(shape, str):
        shape = tuple(int(size) for size in shape.split(','))
    a = np.ndarray(buffer=data[0], dtype=data[1], shape=shape)
    if copy:
        a = np.array(a, copy=True)
    return a
