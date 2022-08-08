#!/usr/bin/env python3

"""
@author: l00511303
@since: 
"""

import random

import numpy as np
import pymongo
from torch.utils.data import Dataset
from tqdm import tqdm


class MongoDataset(Dataset):

    def __init__(self,
                 addr,
                 db,
                 coll,
                 match,
                 project,
                 auth_db='admin',
                 user=None,
                 passwd=None,
                 fn=None,
                 use_cache=False):
        self._addr = addr
        self._db = db
        self._coll_name = coll
        self._match = match
        self._project = project
        self._auth_db = auth_db
        self._user = user
        self._passwd = passwd
        self._fn = fn
        self._use_cache = use_cache

        self._id_list = []
        with pymongo.MongoClient(self._addr) as conn:
            if user is not None:
                conn[auth_db].authenticate(user, passwd)
            coll = conn[db][coll]
            coll = coll.with_options(read_preference=pymongo.ReadPreference.NEAREST)
            cur = coll.find(match, {'_id': 1}).batch_size(4096)
            size = coll.count_documents(match) if match else coll.estimated_document_count()
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
        _id = self._id_list[index]
        if self._use_cache and _id in self._cache:
            return self._cache[_id]
        if self._coll is None:
            self._conn = pymongo.MongoClient(self._addr)
            if self._user is not None:
                self._conn[self._auth_db].authenticate(self._user, self._passwd)
            self._coll = self._conn[self._db][self._coll_name]
            if random.uniform(0, 1) > 0.5:
                self._coll = self._coll.with_options(read_preference=pymongo.ReadPreference.PRIMARY_PREFERRED)
            else:
                self._coll = self._coll.with_options(read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED)
        doc = self._coll.find_one({'_id': _id}, self._project)
        if self._use_cache:
            self._cache[_id] = doc
        if self._fn is not None:
            doc = self._fn(doc)
        return doc


def encode_numpy(a: np.ndarray):
    return a.tobytes('C'), str(a.dtype), a.shape


def decode_numpy(data, copy=False):
    assert isinstance(data, (tuple, list)) and len(data) == 3
    a = np.ndarray(buffer=data[0], dtype=data[1], shape=data[2])
    if copy:
        a = np.array(a, copy=True)
    return a
