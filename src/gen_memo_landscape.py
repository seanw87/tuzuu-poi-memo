#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import random
# import re
import copy
import yaml
# from yaml.scanner import ScannerError
import sample_route_data


class Memo:
    scriptConf = {}
    staticPath = "materials/"
    logoPath = staticPath + "logo.png"
    OUTPUTRES = "hd720"
    AR = "16/9"
    CAPTIONTYPE = 1
    PICTYPE = 2
    VIDEOTYPE = 3
    PADSCALE = "6400x3600"
    PIXFMT = "yuv420p"

    ffmpegCmd = "ffmpeg -y "
    ffmpegFilterComplexFile = "filter_complex."
    ffmpegFilterComplexCmd = ""
    ffmpegVoutConf = "-c:v libx264 -pix_fmt yuv420p -r 25 -profile:v main -bf 0 -level 3"
    ffmpegAoutConf = "-c:a aac -qscale:a 1 -ac 2 -ar 48000 -ab 192k"
    ffmpegMetaConf = "-metadata title=\"我的旅游日记\" -metadata artist=\"我的名字\" -metadata album=\"路线名称\" " \
                     "-metadata comment=\"\""
    # ffmpeg filter graph 输入序号
    ffmpegInputOffset = 0
    # ffmpeg 图片放大scale(用于动画平滑)
    ffmpegPad = "pad=ih*{0}/sar:ih:(ow-iw)/2:(oh-ih)/2".format(AR)
    # ffmpeg 1: 缩小效果; 2: 放大效果
    ffmpegAnimations = {
        1: "zoompan=z='if(eq(on,0),1.3,zoom-0.0005)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={0}".format(OUTPUTRES),
        2: "zoompan=z='min(max(zoom,pzoom)+0.0005,2.0)':x='iw/2-(iw/zoom/2)':"
           "y='ih/2-(ih/zoom/2)':s={0}".format(OUTPUTRES)
    }
    ffmpegLogoPos = "10:10"  # top-right: "main_w-overlay_w-10:10"

    def __init__(self, script_conf_path):
        try:
            f = open(script_conf_path, encoding="utf-8")
            self.scriptConf = yaml.load(f)
        except FileNotFoundError:
            print("script conf file not found：" + str(FileNotFoundError))
            exit(0)

    def generate_memo(self):
        # 获取用户上传路线材料
        route_data = sample_route_data.gen_sample_route()

        # 随机获取背景音乐
        self.get_random_bgmusic()

        # 添加黑色背景(用于blend效果)
        self.get_blank_bg()

        # 背景时长、所有POI(CUT)格式化过的素材列表
        bg_duration, total_materials = self.materials_join_conf(route_data)

        # 添加输入素材
        for material_segs in total_materials:
            for input_material in material_segs["vplist"]:
                self.ffmpegCmd += " -i {}".format(input_material["file"])

        self.ffmpegFilterComplexFile += \
            str(route_data["uid"]) + "." + str(route_data["route_id"]) + "." + str(route_data["finishtime"])
        self.ffmpegCmd += " -filter_complex_script " + self.ffmpegFilterComplexFile

        # 添加水印graph
        cmd = "movie={0}[watermask];\n".format(self.logoPath)
        self.ffmpegFilterComplexCmd += cmd
        # self.ffmpegCmd += cmd

        # 处理黑色背景(用于blend效果)
        self.ffmpegInputOffset = 1
        cmd = "[{0}:v]trim=duration={1}[over0];\n".format(self.ffmpegInputOffset, 1)
        self.ffmpegFilterComplexCmd += cmd
        # self.ffmpegCmd += cmd

        # 得到POI遍历结果
        """
        eg.
        [{
            'vplist':[
                {'type': 2, 'trans_out': 2, 'animation': 1, 'subtitle_font': 'msyh.ttc', 'subtitle_vfx': None,'duration': 5,'file': 'materials/sample/POI_2/WechatIMG33.jpeg','subtitle_x': 0,'subtitle_font_size': 12,'trans_in': 4,'subtitle_y': 0,'subtitle': '','subtitle_color': None}, 
                {'type': 2, 'trans_out': 3, 'animation': 1, 'subtitle_font': 'msyh.ttc', 'subtitle_vfx': None, 'duration': 3, 'file': 'materials/sample/POI_2/WechatIMG145.jpeg', 'subtitle_x': 0, 'subtitle_font_size': 12, 'trans_in': 1, 'subtitle_y': 0, 'subtitle': '', 'subtitle_color': None}
            ],
            'captions': {'content': '文字内容文字内容1','duration': 3,'subtitle_font': 'msyh.ttc','subtitle_x': 0,'subtitle_vfx': None,'subtitle_font_size': 12,'subtitle_y': 0,'subtitle_color': None}
        }, {
            'vplist': [
                {'type': 2, 'trans_out': 2, 'animation': 1, 'subtitle_font': 'msyh.ttc', 'subtitle_vfx': None,'duration': 5,'file': 'materials/sample/POI_2/WechatIMG132.jpeg','subtitle_x': 0,'subtitle_font_size': 12,'trans_in': 3,'subtitle_y': 0,'subtitle': '','subtitle_color ': None}
            ],
            'captions ': {}
        }]
        """
        # 单素材处理层
        # pic_offset = 0
        # video_offset = 0
        for material_segs in total_materials:
            # 叠加字幕
            subtitle = ""
            if material_segs["captions"]:
                # subtitle_x = re.sub(r'W\s*-([0-9]*)]', r'w-text_w-\1', str(material_segs["captions"]["subtitle_x"]))
                # subtitle_y = re.sub(r'H\s*-([0-9]*)]', r'h-text_h-\1', str(material_segs["captions"]["subtitle_y"]))
                subtitle = ",drawtext=fontfile={0}:fontcolor={1}:x={2}:y={3}:enable='lt(t, {4})':text='{5}':" \
                           "fontsize={6}".format(
                                self.staticPath + "font/" + material_segs["captions"]["subtitle_font"],
                                material_segs["captions"]["subtitle_color"],
                                material_segs["captions"]["subtitle_x"], material_segs["captions"]["subtitle_y"],
                                material_segs["captions"]["duration"],
                                material_segs["captions"]["content"],
                                material_segs["captions"]["subtitle_font_size"])

            for material in material_segs["vplist"]:
                # print(material)
                self.ffmpegInputOffset += 1

                duration = material["duration"]
                # 如果是图片
                if material["type"] == self.PICTYPE:
                    animation = self.ffmpegAnimations[material["animation"]]

                    cmd = "[{0}:v]{1},scale={2},{3}{4},trim=duration={5}".format(
                        self.ffmpegInputOffset, self.ffmpegPad, self.PADSCALE, animation, "", duration)     # {4}：d:100
                    self.ffmpegFilterComplexCmd += cmd
                    # self.ffmpegCmd += cmd
                    if subtitle:
                        self.ffmpegFilterComplexCmd += subtitle
                        # self.ffmpegCmd += subtitle
                    # pic_offset += 1
                # 如果是视频
                elif material["type"] == self.VIDEOTYPE:
                    cmd = "[{0}:v]{1},{2},scale={3},trim=duration={4}".format(
                        self.ffmpegInputOffset, "format=pix_fmts=yuv420p", self.ffmpegPad, self.OUTPUTRES, duration)
                    self.ffmpegFilterComplexCmd += cmd
                    # self.ffmpegCmd += cmd
                    if subtitle:
                        self.ffmpegFilterComplexCmd += subtitle
                        # self.ffmpegCmd += subtitle
                    # video_offset += 1
                cmd = ",setpts=PTS-STARTPTS [out{0}];\n".format(self.ffmpegInputOffset-2)
                self.ffmpegFilterComplexCmd += cmd
                # self.ffmpegCmd += cmd

        # 音频处理层
        bgmusic_cmd = "[0:a]afade=enable='between(t,0,2)':t=in:st=0:d=2"
        vaudio_cmd = ""
        # 素材合成
        over_offset = 0
        setopts_ts_offset = 0
        vaover_offset = 0
        for material_segs in total_materials:
            for material in material_segs["vplist"]:
                # 如果是图片
                if material["type"] == self.PICTYPE:
                    cmd = "[out{0}]format=pix_fmts={1},fade=t=in:st=0:d=1:alpha=1," \
                                      "setpts=PTS-STARTPTS{2}[va{3}];\n".format(
                                            over_offset, self.PIXFMT,
                                            "" if setopts_ts_offset == 0 else "+"+str(setopts_ts_offset)+"/TB",
                                            over_offset)
                    self.ffmpegFilterComplexCmd += cmd
                    # self.ffmpegCmd += cmd
                    cmd = "[over{0}][va{1}]overlay[over{2}];\n".format(
                        over_offset, over_offset, over_offset+1)
                    self.ffmpegFilterComplexCmd += cmd
                    # self.ffmpegCmd += cmd
                # 如果是视频
                elif material["type"] == self.VIDEOTYPE:
                    cmd = "[over{0}][out{1}]concat=n=2:v=1:a=0,format={2}[over{3}];\n".format(
                        over_offset, over_offset, self.PIXFMT, over_offset+1)
                    self.ffmpegFilterComplexCmd += cmd
                    # self.ffmpegCmd += cmd

                    bgmusic_cmd += ",afade=enable='between(t,{0},{1})':t=out:st={2}:d=2," \
                                   "volume=enable='between(t,{3},{4})':volume=0.0:eval=frame," \
                                   "afade=enable='between(t,{5},{6})':t=in:st={7}:d=2".format(
                                    setopts_ts_offset+1, setopts_ts_offset+1+2, setopts_ts_offset+1,
                                    setopts_ts_offset+1+2, setopts_ts_offset+1+material["duration"],
                                    setopts_ts_offset+1+material["duration"], setopts_ts_offset+1+material["duration"]+2,
                                    setopts_ts_offset+1+material["duration"])

                    vaudio_cmd += ";\n[{0}:a]adelay={1},volume=volume=0.8:eval=frame,apad[outa{2}];\n" \
                                  "[outa{3}][aover{4}]amerge=inputs=2[aover{5}]".format(
                                    over_offset+2, (setopts_ts_offset+1)*1000, vaover_offset, vaover_offset,
                                    vaover_offset, vaover_offset+1)
                    vaover_offset += 1

                over_offset += 1
                setopts_ts_offset += material["duration"] - 1
        bgmusic_cmd += ",atrim=0:{0}[aover0]".format(setopts_ts_offset+1)

        # print(self.ffmpegCmd)

        # 添加水印
        cmd = "[over{0}][watermask]overlay={1}[outv_relay1];\n".format(over_offset, self.ffmpegLogoPos)
        self.ffmpegFilterComplexCmd += cmd
        # self.ffmpegCmd += cmd
        # 添加作者
        script_author_conf = self.scriptConf["memoflow"]["author"]
        if script_author_conf["display"]:
            cmd = "[outv_relay1]drawtext=fontfile={0}:fontcolor={1}:x={2}:y={3}:text='@{4}':" \
                              "fontsize={5}[outv];\n".format(
                                self.staticPath + "font/" + script_author_conf["font"],
                                script_author_conf["color"],
                                script_author_conf["x"],
                                script_author_conf["y"],
                                route_data["author"],
                                script_author_conf["font_size"])
            self.ffmpegFilterComplexCmd += cmd
            # self.ffmpegCmd += cmd
        else:
            cmd = "[outv_relay1][outv];\n"
            self.ffmpegFilterComplexCmd += cmd
            # self.ffmpegCmd += cmd

        # 添加音频
        self.ffmpegFilterComplexCmd += bgmusic_cmd
        # self.ffmpegCmd += bgmusic_cmd
        self.ffmpegFilterComplexCmd += vaudio_cmd
        # self.ffmpegCmd += vaudio_cmd

        self.ffmpegCmd += " -map [outv] {0} -map [{1}] {2} {3} -shortest mymemo_{4}.mp4".format(
            self.ffmpegVoutConf, "aover"+str(vaover_offset), self.ffmpegAoutConf, self.ffmpegMetaConf,
            str(route_data["author"])+"_"+route_data["route_name"]+"_"+str(route_data["finishtime"])
        )

        # 生成filter_complex脚本文件
        self.export_ffmpeg_filter_complex()

        # 导出ffmpeg命令
        self.export_ffmpeg_cmd()

        os.system(self.ffmpegCmd)
        exit(0)

    def get_random_bgmusic(self):
        conf_bgmusic = self.scriptConf["memoflow"]["bgmusic"]
        bgmusic = random.choice(conf_bgmusic)
        self.ffmpegCmd += " -i {}musics/{} " . format(self.staticPath, bgmusic)

    def get_blank_bg(self):
        self.ffmpegCmd += " -f lavfi -i \"color=black:s={}\" ".format(self.OUTPUTRES)

    def materials_join_conf(self, route_data):
        # 输入素材列表
        # input_materials = []

        # 背景时长
        bg_duration = 0
        # 所有POI(CUT)格式化过的素材列表
        total_materials = []

        # 遍历每个POI(CUT)
        for node in route_data["route"]:
            """
            eg. 
            {
                "node": "POI_2",
                "materials": [
                    [
                        {"ts": 1544858301, "type": 1, "content": "文字内容文字内容1"},
                        {"ts": 1544858302, "type": 2, "file": "WechatIMG33.jpeg"},
                        {"ts": 1544858303, "type": 3, "file": "2019-03-03-15.07.47.mp4"}
                    ],
                ]
            }
            """
            # print("node name: {}".format(node["node"]))
            # 遍历每个material
            for m in node["materials"]:
                """
                [
                    {"ts": 1544858301, "type": 1, "content": "文字内容文字内容1"},
                    {"ts": 1544858302, "type": 2, "file": "WechatIMG33.jpeg"},
                    {"ts": 1544858303, "type": 3, "file": "2019-03-03-15.07.47.mp4"}
                ]
                """
                # 对于图片和视频，获取张数，以确定字幕时长
                cur_caption_duration = 0
                # 生成图片、视频特效配置
                cur_materials = {}
                cur_vplist = []
                cur_caption_conf = {}
                # 遍历一个组合内的素材（同一时间上传）
                for m_item in m:
                    type_conf = self.scriptConf["memoflow"][node["node"]]["type" + str(m_item["type"])]
                    if m_item["type"] in [self.PICTYPE, self.VIDEOTYPE]:
                        # print(self.scriptConf["memoflow"][node["node"]])

                        # 获取配置信息
                        cur_duration = random.choice(type_conf["duration"])
                        cur_vp_conf = {
                                       "type": m_item["type"],
                                       "file": m_item["file"],
                                       "duration": cur_duration,
                                       "trans_in": random.choice(type_conf["trans_in"]),
                                       "trans_out": random.choice(type_conf["trans_out"]),
                                       "animation": random.choice(type_conf["animation"]) if type_conf["animation"] else "",
                                       "subtitle": type_conf["subtitle"],
                                       "subtitle_font": type_conf["subtitle_font"],
                                       "subtitle_font_size": type_conf["subtitle_font_size"],
                                       "subtitle_x": type_conf["subtitle_x"],
                                       "subtitle_y": type_conf["subtitle_y"],
                                       "subtitle_color": type_conf["subtitle_color"],
                                       "subtitle_vfx": type_conf["subtitle_vfx"]
                                    }

                        cur_caption_duration += cur_duration
                        cur_vplist.append(cur_vp_conf)

                        bg_duration += cur_duration-1 if m_item["type"] == self.PICTYPE else 0

                        # input_materials.append(m_item["file"])
                    if m_item["type"] == self.CAPTIONTYPE:
                        if type_conf["strategy"] == "random":
                            cur_caption_conf = random.choice(type_conf["lists"])
                            cur_caption_conf["content"] = m_item["content"]
                cur_materials["captions"] = cur_caption_conf
                cur_materials["vplist"] = cur_vplist
                total_materials.append(copy.deepcopy(cur_materials))

        return bg_duration, total_materials

    def export_ffmpeg_filter_complex(self):
        fc = open(self.ffmpegFilterComplexFile, "w", encoding="utf-8")
        fc.write(self.ffmpegFilterComplexCmd)
        fc.close()

    def export_ffmpeg_cmd(self):
        fo = open("generated_ffmpeg_cmd.txt", "w")
        fo.write(self.ffmpegCmd)
        fo.close()


class UsageError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error:
            raise UsageError(str(getopt.error))
        # more code, unchanged
    except UsageError:
        print(str(UsageError))
        print(sys.stderr, "for help use --help")
        return 2
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
    # process arguments
    # for arg in args:
        # process(arg)  # process() is defined elsewhere

    script_conf_path = r"script_conf.yaml"
    memo = Memo(script_conf_path)
    memo.generate_memo()


if __name__ == "__main__":
    sys.exit(main())


