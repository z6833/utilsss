import threading
import traceback

import requests
from ..utils.log import logger
import time


def check_request(request):
    if request and request.status_code == 200:
        return True
    else:
        return False


def post_url(url, json_data, timeout=1):
    try:
        r = requests.post(url, json=json_data, timeout=timeout)
        return r
    except Exception as e:
        logger.error("post url failed! {}".format(repr(e)))
        logger.error(traceback.format_exc())


class NotifyUrl(threading.Thread):
    TIME_WAIT = 5

    def __init__(self, url, json_data, check_func=check_request, timeout=1, try_num=1):
        self.url = url
        self.json_data = json_data
        self.try_num = max(1, try_num)
        self.timeout = timeout
        self.check_func = check_func
        super(NotifyUrl, self).__init__()
        self.start()

    def run(self):
        for i in range(self.try_num):
            r = post_url(self.url, self.json_data, self.timeout)
            if r and r.status_code == 200:
                return
            else:
                time.sleep(NotifyUrl.TIME_WAIT)
        logger.error("post url {} times failed! {}".format(self.try_num,self.json_data))
