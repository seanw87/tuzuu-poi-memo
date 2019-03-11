#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt
import os
import sys

import yaml

import data_source
from tuzuu_log import TuzuuLog
from tuzuu_memo import Memo


class UsageError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

def log(content):
    flog = open("gen_mem.log", "a", encoding='utf-8')
    flog.write(content)
    flog.close()


def main(argv=None):
    # 切换为脚本所在目录
    os.chdir(os.path.split(os.path.realpath(__file__))[0])

    if argv is None:
        argv = sys.argv

    appconf = "../conf/main.yaml"

    try:
        try:
            opts, args = getopt.getopt(argv[1:], "-h-c:", ["help", "config="])
        except getopt.error:
            raise UsageError(str(getopt.error))
    except UsageError:
        print("unknown param, for help use --help")
        return 2
    for o, a in opts:
        if o in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        if o in ("-c", "--config"):
            if os.path.exists(a):
                appconf = a
    # for arg in args:
        # process(arg)  # process() is defined elsewhere

    script_conf = {}
    try:
        f = open(appconf, encoding="utf-8")
        script_conf = yaml.load(f)
    except FileNotFoundError:
        print("script conf file not found：" + appconf + ", " + str(FileNotFoundError))
        exit(0)

    # 初始化日志类
    tuzuulog = TuzuuLog(script_conf["main"])

    # 获取数据
    route_data_batch = data_source.get_route_data()

    route_script_dir = r"../conf/route_scripts/"
    for route_data in route_data_batch:
        script_conf_path = route_script_dir + r"script_conf_r{}.yaml".format(route_data["route_id"])
        if os.path.exists(script_conf_path):
            memo = Memo(script_conf_path, route_data, tuzuulog, script_conf)
            memo.generate_memo()
            tuzuulog.log("uid: {}, route_id: {} memo generated.".format(route_data["uid"], route_data["route_id"]))
            print("uid: {}, route_id: {} memo generated.".format(route_data["uid"], route_data["route_id"]))
        else:
            tuzuulog.log("uid: {}, route_id: {} route script: {} not found!".format(route_data["uid"],
                                                                                    route_data["route_id"],
                                                                                    script_conf_path))

        exit(0)

if __name__ == "__main__":
    sys.exit(main())
