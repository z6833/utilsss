from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from prestodb import dbapi


def select():
    conn = dbapi.Connection(host="172.20.20.11", port=9080, user="kudu", catalog="yn_sd")
    cur = conn.cursor()
    cur.execute("select rowid, * from  yunnan1900")
    res = cur.fetchone()
    for item in res:
        #@print(item)


if __name__ == "__main__":
    select()
