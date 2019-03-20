#!/usr/bin/python
# -*- coding: utf-8 -*-
import time


class TuzuuLog:
    def __init__(self, appconf):
        self.curdate = time.strftime("%Y%m%d", time.localtime())

        self.applog = appconf["applog"]
        self.ffmpeglog = appconf["ffmpeglog"]
        self.ffmpegcmd = appconf["ffmpegcmd"]

    def log(self, content, printable=False):
        """
        通用日志方法
        :param content:
        :param printable:
        :return:
        """
        applog_segs = self.applog.rsplit(".", 1)
        applog = applog_segs[0] + "-" + self.curdate + "." + applog_segs[1]
        flog = open(applog, "a", encoding='utf-8')
        flog.write("INFO " + content + "\n")
        flog.close()
        if printable:
            print(content)

    def warning(self, content, printable=False):
        """
        通用日志方法
        :param content:
        :param printable:
        :return:
        """
        applog_segs = self.applog.rsplit(".", 1)
        applog = applog_segs[0] + "-" + self.curdate + "." + applog_segs[1]
        flog = open(applog, "a", encoding='utf-8')
        flog.write("WARN " + content + "\n")
        flog.close()
        if printable:
            print(content)

    def error(self, content, printable=False):
        """
        通用日志方法
        :param content:
        :param printable:
        :return:
        """
        applog_segs = self.applog.rsplit(".", 1)
        applog = applog_segs[0] + "-" + self.curdate + "." + applog_segs[1]
        flog = open(applog, "a", encoding='utf-8')
        flog.write("ERROR " + content + "\n")
        flog.close()
        if printable:
            print(content)

    def ffmpeg_log(self, content):
        """
        ffmpeg执行结果日志
        :param content:
        :return:
        """
        ffmpeglog_segs = self.ffmpeglog.rsplit(".", 1)
        ffmpeglog = ffmpeglog_segs[0] + "-" + self.curdate + "." + ffmpeglog_segs[1]
        flog = open(ffmpeglog, "a", encoding='utf-8')
        flog.write(content + "\n\n")
        flog.close()

    def ffmpeg_cmd_export(self, content):
        """
        ffmpeg命令生成日志
        :param content:
        :return:
        """
        ffmpegcmd_segs = self.ffmpegcmd.rsplit(".", 1)
        ffmpegcmd = ffmpegcmd_segs[0] + "-" + self.curdate + "." + ffmpegcmd_segs[1]
        flog = open(ffmpegcmd, "a", encoding='utf-8')
        flog.write(content + "\n")
        flog.close()

    @staticmethod
    def ffmpeg_filter_complex_export(filter_complex_file, cmd):
        """
        ffmpeg filter complex参数生成文件
        :param filter_complex_file:
        :param cmd:
        :return:
        """
        fc = open(filter_complex_file, "w", encoding="utf-8")
        fc.write(cmd + "\n")
        fc.close()