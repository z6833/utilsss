#!/usr/bin/env python3

"""
@author: y00520910
@since:
"""
import numpy as np
from MongoDataset import MongoDataset, decode_numpy

class WiFiDenoiseDataset(MongoDataset):

    def __init__(self, is_train, host, db, coll, user, passwd):
        super(WiFiDenoiseDataset, self).__init__(
            host=host,
            db=db,
            coll=coll,
            match={'split': 1 if is_train else 0},
            project=None,
            user=user,
            passwd=passwd,
        )
        self._is_train = is_train

    def __getitem__(self, index):
        doc = super(WiFiDenoiseDataset, self).__getitem__(index)
        #input:key
        key = decode_numpy(doc['keys'])
        key = np.where(key > 100, 100, key)
        key = np.array(key / 100)  # shape: T
        #input:query
        query = np.array(decode_numpy(doc['query_t']))  # shape: T

        #label
        target = int(doc['label'])
        if target > 100:
            target = 100

        return {'query': query, 'key': key, 'target': target}
