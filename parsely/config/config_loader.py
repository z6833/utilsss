# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/21 11:55
# @File    : config_loader.py
# @Desc    : 管理微服务配置

import os
import configparser
from ..config.apollo_client import ApolloClient
from ..utils.log import logger


# from config.apollo_client import ApolloClient
# from utils.log import logger


def get_local_config(local_config_path):
    if not os.path.exists(local_config_path):
        logger.warning("Config File {} Not Found".format(local_config_path))
        return None
    # 创建管理对象
    conf_parser = configparser.ConfigParser()
    # 读ini文件
    conf_parser.read(local_config_path, encoding="utf-8")
    conf = {}
    for section in conf_parser.sections():
        conf[section] = {}
        for option in conf_parser.options(section):
            conf[section][option] = conf_parser.get(section, option)
    if 'configurations' not in conf:
        logger.warning("session configurations should be top session")
        return None
    return conf['configurations']


def start_config_client(app_id, config_url):
    return ApolloClient(app_id=app_id, config_url=config_url)


def get_remote_config(client, namespace="application"):
    conf = client.get_json_from_net(namespace)
    if conf is None:
        logger.warning("No config in namespace {}".format(namespace))
        return None
    if 'configurations' not in conf:
        logger.warning("key configurations not found in namespace {}".format(namespace))
        return None
    return conf['configurations']


def update_configs_with_remote(local_conf, merged_config_path):
    """
    远程配置中心配置覆盖本地配置，并生成新的配置文件，微服务运行时从中读取配置信息
    :param local_conf: 原本地配置
    :param merged_config_path: 新的本地配置文件路径
    """
    if 'app_id' not in local_conf:
        logger.warning("app_id not found in config file")
        return False
    if 'config.url' not in local_conf:
        logger.warning("config.url not found in config file")
        return False
    app_id = local_conf['app_id']
    config_url = local_conf['config.url']
    logger.info("appid: {}, config_url: {}".format(app_id, config_url))
    # 获取配置中心配置
    remote_conf_client = start_config_client(app_id=app_id, config_url=config_url)
    remote_conf = get_remote_config(remote_conf_client)
    if remote_conf is None:
        return False
    # 用远程配置更新本地配置，并将最新配置导出到新的文件
    for key in remote_conf:
        local_conf[key] = remote_conf[key]
    new_conf = configparser.ConfigParser()
    session_name = "configurations"
    new_conf.add_section(session_name)
    for key in local_conf:
        new_conf.set(session_name, key, local_conf[key])  # 给添加的section组增加option-value
    new_conf.write(open(merged_config_path, "w"))
    logger.info("update local configs with remote")
    return True
