#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import random
import copy
import datetime
import yaml
# from yaml.scanner import ScannerError
from pprint import pprint
import subprocess
import data_source


class Memo:
    BG_BLACK_DURATION = 1
    UGC_INPUT_OFFSET = 3
    OUTPUTRES = "720x1280"
    OUTPUTR = 25
    AR = "16/9"
    POICOVERTYPE = 0
    CAPTIONTYPE = 1
    PICTYPE = 2
    VIDEOTYPE = 3
    PADSCALE = "6400x3600"
    VPADSCALE = "1280x720"
    PIXFMT = "yuv420p"
    POI_CAPTION_FONT = "msyh.ttc"
    POI_DEFAULT_COVER = "cut_default.png"
    POI_TITLE_FONTSIZE = 48
    POI_SUBTITLE_FONTSIZE = 32
    POI_CAPTION_COLOR = "white"
    POI_CAPTION_DURATION = 4
    POI_TRANSIT_DURATION = 0.3

    routeData = None

    scriptConf = {}
    staticPath = "materials/"
    poiCoverPath = staticPath + "poi_cover/"
    logoPath = staticPath + "logo.png"
    poiNum = 0

    ffmpegCmd = "ffmpeg -y "
    ffmpegFilterComplexFile = "filter_complex."
    ffmpegFilterComplexCmd = ""
    ffmpegVoutConf = "-c:v libx264 -pix_fmt yuv420p -r {0} -profile:v main -bf 0 -level 3".format(OUTPUTR)
    ffmpegAoutConf = "-c:a aac -qscale:a 1 -ac 2 -ar 48000 -ab 192k"
    ffmpegMetaConf = "-metadata title=\"我的旅游日记\" -metadata artist=\"我的名字\" -metadata album=\"路线名称\" " \
                     "-metadata comment=\"\""

    # ffmpeg filter graph 输入序号
    ffmpegInputOffset = 0

    # ffmpeg 图片放大scale(用于动画平滑)
    ffmpegPad = "pad=iw+1:ceil(iw*{0}/sar)+1:(ow-iw)/2:(oh-ih)/2".format(AR)

    # ffmpeg 1: 缩小效果; 2: 放大效果
    ffmpegAnimations = {
        1: "zoompan=z='if(eq(on,0),1.3,zoom-0.0005)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={0}".format(OUTPUTRES),
        2: "zoompan=z='min(max(zoom,pzoom)+0.0005,2.0)':x='iw/2-(iw/zoom/2)':"
           "y='ih/2-(ih/zoom/2)':s={0}".format(OUTPUTRES)
    }

    # POI cover animation
    ffmpegPoiCoverAnimation = ""
    ffmpegLogoPos = "10:10"  # top-right: "main_w-overlay_w-10:10"

    ffmpegPoiTitleX = "((w-tw)/2)"
    ffmpegPoiTitleY = "min(h/4.5+n,h/4.5+20)"
    ffmpegPoiSubtitleX = "((w-tw)/2)"
    ffmpegPoiSubtitleY = "max(h/3.0-n,h/3.0-20)"
    ffmpegPoiAlpha = "min(1, n/15)"
    ffmpegPoiBoxY = "ih/5.7"
    ffmpegPoiBoxWidth = "iw"
    ffmpegPoiBoxHeight = 300

    def __init__(self, script_conf_path, route_data):
        try:
            f = open(script_conf_path, encoding="utf-8")
            self.scriptConf = yaml.load(f)
            self.routeData = route_data
        except FileNotFoundError:
            print("script conf file not found：" + str(FileNotFoundError))
            exit(0)

    def generate_memo(self):
        # 获取用户上传路线材料
        # route_data = sample_route_data.gen_sample_route()

        # 生成filter complex脚本配置文件名字
        self.get_filter_complex_filename(self.routeData)

        # 背景时长(DEPRECATED)、所有POI(CUT)格式化过的素材列表
        bg_duration, total_materials = self.materials_join_conf(self.routeData)
        """
        total_materials .eg:
            [{'poi_cover': 'cut1.png',
              'poi_cover_duration': 3,
              'poi_subtitle': '老上海调调',
              'poi_title': '塞纳河畔，咖啡屋',
              'ucontents': [{'captions': {'content': '2018年7月1日',
                                          'duration': 3,
                                          'subtitle_color': '0xffffff',
                                          'subtitle_font': 'msyh.ttc',
                                          'subtitle_font_size': 64,
                                          'subtitle_vfx': None,
                                          'subtitle_x': '(w-text_w)/2',
                                          'subtitle_y': '(h-text_h)/2'},
                             'vplist': [{'animation': 2,
                                         'duration': 4,
                                         'file': 'materials/sample/POI_2/WechatIMG33.jpeg',
                                         'subtitle': '',
                                         'subtitle_color': '0xffffff',
                                         'subtitle_font': 'msyh.ttc',
                                         'subtitle_font_size': 32,
                                         'subtitle_vfx': None,
                                         'subtitle_x': 0,
                                         'subtitle_y': 0,
                                         'trans_in': 1,
                                         'trans_out': 2,
                                         'type': 2
                                        }]
                             }]
             }]
        """
        # pprint(total_materials[0])

        # 随机获取背景音乐
        self.get_random_bgmusic()

        # 添加黑色背景(用于blend效果) - input no.0
        self.get_blank_bg()

        # 添加透明背景(用于poi cover字幕) - input no.1
        self.get_transparent_bg()

        # 添加输入素材
        for poi_materials in total_materials:
            # POI COVER
            poi_cover_path = self.poiCoverPath + str(self.routeData["route_id"]) + "/" + poi_materials["poi_cover"]
            if not os.path.exists(poi_cover_path):
                poi_cover_path = self.poiCoverPath + self.POI_DEFAULT_COVER
            self.ffmpegCmd += " -i {}".format(poi_cover_path)
            # UGC CONTENT
            for material_segs in poi_materials["ucontents"]:
                for input_material in material_segs["vplist"]:
                    self.ffmpegCmd += " -i {}".format(input_material["file"])

        self.ffmpegCmd += " -filter_complex_script " + self.ffmpegFilterComplexFile

        # 添加水印graph
        cmd = "movie={0}[watermask];\n".format(self.logoPath)
        self.ffmpegFilterComplexCmd += cmd

        # 处理黑色背景(用于blend效果)
        self.ffmpegInputOffset += 1
        cmd = "[{0}:v]trim=duration={1}[over0];\n".format(self.ffmpegInputOffset, self.BG_BLACK_DURATION)
        self.ffmpegFilterComplexCmd += cmd

        self.poiNum = len(total_materials)

        # 根据POI cover数量生成对应数量的透明背景graph
        self.ffmpegInputOffset += 1
        cmd = "[{0}:v]split=4".format(self.ffmpegInputOffset)
        poi_title_offset = 0
        for poi_materials in total_materials:
            if poi_materials["poi_title"]:
                poi_subtitle_index = 2 * poi_title_offset
                cmd += "[poi{0}]".format(poi_subtitle_index)
                cmd += "[poi{0}]".format(poi_subtitle_index+1)
                poi_title_offset += 1
        cmd += ";\n"
        self.ffmpegFilterComplexCmd += cmd

        # 1. 单素材处理层
        # pic_offset = 0
        # video_offset = 0
        for poi_materials in total_materials:
            # POI COVER
            self.ffmpegInputOffset += 1
            cmd = "[{0}:v]{1},scale={2},{3}{4}" \
                   "zoompan=z='min(max(zoom,pzoom)+0.00001,2.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={11}," \
                  "drawbox=enable='lt(t,{10})':y={6}:w={7}:h={8}:color=black@0.5:t=fill,trim=duration={5}," \
                  "setpts=PTS-STARTPTS[out{9}];\n".format(
                self.ffmpegInputOffset, self.ffmpegPad, self.PADSCALE, self.ffmpegPoiCoverAnimation, "",
                poi_materials["poi_cover_duration"],
                self.ffmpegPoiBoxY, self.ffmpegPoiBoxWidth, self.ffmpegPoiBoxHeight,
                self.ffmpegInputOffset - self.UGC_INPUT_OFFSET,
                poi_materials["poi_cover_duration"],
                self.OUTPUTRES
            )
            self.ffmpegFilterComplexCmd += cmd

            for material_segs in poi_materials["ucontents"]:
                # 需要叠加的字幕
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
                    self.ffmpegInputOffset += 1

                    duration = material["duration"]
                    # 如果是图片
                    if material["type"] == self.PICTYPE:
                        animation = self.ffmpegAnimations[material["animation"]]

                        cmd = "[{0}:v]{1},scale={2},{3}{4},trim=duration={5}".format(
                            self.ffmpegInputOffset, self.ffmpegPad, self.PADSCALE, animation, "", duration)     # {4}：d:100
                        self.ffmpegFilterComplexCmd += cmd

                        if subtitle:
                            self.ffmpegFilterComplexCmd += subtitle
                        # pic_offset += 1
                    # 如果是视频
                    elif material["type"] == self.VIDEOTYPE:
                        cmd = "[{0}:v]{1},{2},scale={3},trim=duration={4}".format(
                            self.ffmpegInputOffset, "format=pix_fmts=yuv420p", self.ffmpegPad, self.OUTPUTRES, duration)
                        self.ffmpegFilterComplexCmd += cmd

                        if subtitle:
                            self.ffmpegFilterComplexCmd += subtitle
                        # video_offset += 1
                    cmd = ",setpts=PTS-STARTPTS [out{0}];\n".format(self.ffmpegInputOffset-self.UGC_INPUT_OFFSET)
                    self.ffmpegFilterComplexCmd += cmd

        # 音频处理层
        bgmusic_cmd = "[0:a]afade=enable='between(t,0,2)':t=in:st=0:d=2"
        vaudio_cmd = ""

        # 2. 素材合成

        # PIO字幕偏移
        poi_title_offset = 0
        # 叠加层偏移
        over_offset = 0
        # 叠加层时间偏移
        setopts_ts_offset = 0
        # 音频偏移
        vaover_offset = 0
        for poi_materials in total_materials:
            poi_subtitle_index = 2 * poi_title_offset
            cmd = ""
            if poi_materials["poi_title"]:
                cmd += "[poi{0}]drawtext=enable='lt(t, {1})':fontsize={2}:fontcolor={3}:fontfile={4}:text={5}:x='{6}':y='{7}':alpha='{8}'," \
                       "trim=duration={9},setpts=PTS-STARTPTS{10}[poit{11}];\n".format(poi_subtitle_index,
                                                                    self.POI_CAPTION_DURATION,
                                                                    self.POI_TITLE_FONTSIZE,
                                                                    self.POI_CAPTION_COLOR,
                                                                    self.staticPath + "font/" + self.POI_CAPTION_FONT,
                                                                    poi_materials["poi_title"],
                                                                    self.ffmpegPoiTitleX,
                                                                    self.ffmpegPoiTitleY,
                                                                    self.ffmpegPoiAlpha,
                                                                    self.POI_CAPTION_DURATION,
                                                                    "" if setopts_ts_offset == 0 else "+" + str(
                                                                                           setopts_ts_offset) + "/TB",
                                                                    poi_subtitle_index)
                cmd += "[poi{0}]drawtext=enable='lt(t, {1})':fontsize={2}:fontcolor={3}:fontfile={4}:text={5}:x='{6}':y='{7}':alpha='{8}'," \
                       "trim=duration={9},setpts=PTS-STARTPTS{10}[poit{11}];\n".format(poi_subtitle_index + 1,
                                                                    self.POI_CAPTION_DURATION,
                                                                    self.POI_SUBTITLE_FONTSIZE,
                                                                    self.POI_CAPTION_COLOR,
                                                                    self.staticPath + "font/" + self.POI_CAPTION_FONT,
                                                                    poi_materials["poi_subtitle"],
                                                                    self.ffmpegPoiSubtitleX,
                                                                    self.ffmpegPoiSubtitleY,
                                                                    self.ffmpegPoiAlpha,
                                                                    self.POI_CAPTION_DURATION,
                                                                    "" if setopts_ts_offset == 0 else "+" + str(
                                                                                           setopts_ts_offset) + "/TB",
                                                                    poi_subtitle_index + 1)
                if poi_title_offset == 0:
                    cmd += "[out{0}]format=pix_fmts={1},setpts=PTS-STARTPTS{2}[va{3}];\n".format(
                        over_offset, self.PIXFMT, "" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                        over_offset)
                else:
                    cmd += "[out{0}]format=pix_fmts={1},fade=t=in:st=0:d={4}:alpha=0," \
                        "setpts=PTS-STARTPTS{2}[va{3}];\n".format(over_offset, self.PIXFMT,
                                                               "" if setopts_ts_offset == 0 else "+" + str(
                                                                                           setopts_ts_offset) + "/TB",
                                                               over_offset, self.POI_TRANSIT_DURATION)
                cmd += "[over{0}][va{1}]overlay[poioo{2}];\n".format(over_offset, over_offset, poi_title_offset)
                cmd += "[poioo{0}][poit{1}]overlay[poiover{2}];\n".format(poi_title_offset, poi_subtitle_index, poi_title_offset)
                cmd += "[poiover{0}][poit{1}]overlay[over{2}];\n".format(poi_title_offset, poi_subtitle_index+1, over_offset+1)

                poi_title_offset += 1
            else:
                if poi_title_offset == 0:
                    cmd += "[out{0}]format=pix_fmts={1},setpts=PTS-STARTPTS{2}[va{3}];\n".format(
                        over_offset, self.PIXFMT, "" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                        over_offset)
                else:
                    cmd += "[out{0}]format=pix_fmts={1},fade=t=in:st=0:d={4}:alpha=0," \
                           "setpts=PTS-STARTPTS{2}[va{3}];\n".format(over_offset, self.PIXFMT,
                                                                     "" if setopts_ts_offset == 0 else "+" + str(
                                                                         setopts_ts_offset) + "/TB",
                                                                     over_offset, self.POI_TRANSIT_DURATION)
                cmd += "[over{0}][va{1}]overlay[over{2}];\n".format(over_offset, over_offset, over_offset+1)
            self.ffmpegFilterComplexCmd += cmd
            over_offset += 1

            if poi_title_offset > 0:
                setopts_ts_offset += poi_materials["poi_cover_duration"] - self.POI_TRANSIT_DURATION

            for material_segs in poi_materials["ucontents"]:
                for material in material_segs["vplist"]:
                    # 如果是图片
                    if material["type"] == self.PICTYPE:
                        cmd = "[out{0}]format=pix_fmts={1},fade=t=in:st=0:d=1:alpha=1," \
                                          "setpts=PTS-STARTPTS{2}[va{3}];\n".format(
                                                over_offset, self.PIXFMT,
                                                "" if setopts_ts_offset == 0 else "+"+str(setopts_ts_offset)+"/TB",
                                                over_offset)
                        self.ffmpegFilterComplexCmd += cmd

                        cmd = "[over{0}][va{1}]overlay[over{2}];\n".format(
                            over_offset, over_offset, over_offset+1)
                        self.ffmpegFilterComplexCmd += cmd
                    # 如果是视频
                    elif material["type"] == self.VIDEOTYPE:
                        cmd = "[over{0}][out{1}]concat=n=2:v=1:a=0,format={2}[over{3}];\n".format(
                            over_offset, over_offset, self.PIXFMT, over_offset+1)
                        self.ffmpegFilterComplexCmd += cmd

                        bgmusic_cmd += ",afade=enable='between(t,{0},{1})':t=out:st={2}:d=2," \
                                       "volume=enable='between(t,{3},{4})':volume=0.0:eval=frame," \
                                       "afade=enable='between(t,{5},{6})':t=in:st={7}:d=2".format(
                                        setopts_ts_offset+1, setopts_ts_offset+1+2, setopts_ts_offset+1,
                                        setopts_ts_offset+1+2, setopts_ts_offset+1+material["duration"],
                                        setopts_ts_offset+1+material["duration"], setopts_ts_offset+1+material["duration"]+2,
                                        setopts_ts_offset+1+material["duration"])
                        vaudio_cmd += ";\n[{0}:a]adelay={1},volume=volume=0.8:eval=frame,apad[outa{2}];\n" \
                                      "[outa{3}][aover{4}]amerge=inputs=2[aover{5}]".format(
                                        over_offset+self.UGC_INPUT_OFFSET, (setopts_ts_offset+1)*1000, vaover_offset, vaover_offset,
                                        vaover_offset, vaover_offset+1)
                        vaover_offset += 1

                    over_offset += 1
                    setopts_ts_offset += material["duration"] - 1
        bgmusic_cmd += ",atrim=0:{0}[aover0]".format(setopts_ts_offset+1)

        # 添加水印
        cmd = "[over{0}][watermask]overlay={1}[outv_relay1];\n".format(over_offset, self.ffmpegLogoPos)
        self.ffmpegFilterComplexCmd += cmd

        # 添加作者
        script_author_conf = self.scriptConf["memoflow"]["author"]
        if script_author_conf["display"]:
            cmd = "[outv_relay1]drawtext=fontfile={0}:fontcolor={1}:x={2}:y={3}:text='@{4}':" \
                              "fontsize={5}[outv];\n".format(
                                self.staticPath + "font/" + script_author_conf["font"],
                                script_author_conf["color"],
                                script_author_conf["x"],
                                script_author_conf["y"],
                                self.routeData["author"],
                                script_author_conf["font_size"])
            self.ffmpegFilterComplexCmd += cmd
        else:
            cmd = "[outv_relay1][outv];\n"
            self.ffmpegFilterComplexCmd += cmd

        # 添加音频
        self.ffmpegFilterComplexCmd += bgmusic_cmd
        self.ffmpegFilterComplexCmd += vaudio_cmd

        # 添加输出选项
        self.ffmpegCmd += " -map [outv] {0} -map [{1}] {2} {3} -shortest mymemo_{4}.mp4".format(
            self.ffmpegVoutConf, "aover"+str(vaover_offset), self.ffmpegAoutConf, self.ffmpegMetaConf,
            str(self.routeData["author"])+"_"+self.routeData["route_name"]+"_"+str(self.routeData["finishtime"])
        )

        # 生成filter_complex脚本文件
        self.export_ffmpeg_filter_complex()

        # 导出ffmpeg命令到文件
        self.export_ffmpeg_cmd()

        # 执行ffmpeg命令
        code = 0
        try:
            out_bytes = subprocess.check_output(self.ffmpegCmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            out_bytes = e.output  # Output generated before error
            code = e.returncode  # Return code
        self.ffmpeg_log_output("uid: {0}, ts: {1}, code: {2}, msg: {3}\n\n".format(
            self.routeData["uid"], datetime.datetime.now(), code, out_bytes.decode('utf-8')))

    def get_random_bgmusic(self):
        conf_bgmusic = self.scriptConf["memoflow"]["bgmusic"]
        bgmusic = random.choice(conf_bgmusic)
        self.ffmpegCmd += " -i {}musics/{} " . format(self.staticPath, bgmusic)
        # 输入偏移从背景音乐开始
        self.ffmpegInputOffset = 0

    def get_blank_bg(self):
        self.ffmpegCmd += " -f lavfi -i \"color=black:s={}\" ".format(self.OUTPUTRES)

    def get_transparent_bg(self):
        self.ffmpegCmd += " -f lavfi -i \"color=black@0.0:s={},format=rgba\" ".format(self.OUTPUTRES)

    def materials_join_conf(self, route_data):
        # 输入素材列表
        # input_materials = []

        # DEPRECATED - 背景时长
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

            script_node_config = self.scriptConf["memoflow"][node["node"]]

            # 构建POI数据
            poi_materials = {
                "poi_cover": script_node_config["poi_cover"],
                "poi_title": script_node_config["poi_title"],
                "poi_subtitle": script_node_config["poi_subtitle"],
                "poi_cover_duration": script_node_config["poi_cover_duration"],
                # ugc内容列表
                "ucontents": []
            }

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
                # cur_caption_duration = 0
                # 生成图片、视频特效配置
                cur_materials = {}
                cur_vplist = []
                cur_caption_conf = {}
                # 遍历一个组合内的素材（同一时间上传）
                for m_item in m:
                    type_conf = script_node_config["type" + str(m_item["type"])]
                    if m_item["type"] in [self.PICTYPE, self.VIDEOTYPE]:
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
                        # cur_caption_duration += cur_duration
                        cur_vplist.append(cur_vp_conf)

                        # bg_duration += cur_duration-1 if m_item["type"] == self.PICTYPE else 0
                        # input_materials.append(m_item["file"])
                    if m_item["type"] == self.CAPTIONTYPE:
                        if type_conf["strategy"] == "random":
                            cur_caption_conf = random.choice(type_conf["lists"])
                            cur_caption_conf["content"] = m_item["content"]
                cur_materials["captions"] = cur_caption_conf
                cur_materials["vplist"] = cur_vplist
                poi_materials["ucontents"].append(copy.deepcopy(cur_materials))

            total_materials.append(poi_materials)
        return bg_duration, total_materials

    def get_filter_complex_filename(self, route_data):
        self.ffmpegFilterComplexFile += \
            str(route_data["uid"]) + "." + str(route_data["route_id"]) + "." + str(route_data["finishtime"])

    def export_ffmpeg_filter_complex(self):
        fc = open(self.ffmpegFilterComplexFile, "w", encoding="utf-8")
        fc.write(self.ffmpegFilterComplexCmd)
        fc.close()

    def export_ffmpeg_cmd(self):
        fo = open("generated_ffmpeg_cmd.txt", "w")
        fo.write(self.ffmpegCmd)
        fo.close()

    def ffmpeg_log_output(self, content):
        fl = open("ffmpeg_gen_log.log", "a", encoding='utf-8')
        fl.write(content)
        fl.close()


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

    route_data_batch = data_source.get_route_data()

    for route_data in route_data_batch:
        script_conf_path = r"script_conf_r{}.yaml".format(route_data["route_id"])
        if os.path.exists(script_conf_path):
            memo = Memo(script_conf_path, route_data)
            memo.generate_memo()
            log("uid: {}, route_id: {} memo generated.".format(route_data["uid"], route_data["route_id"]))
            print("uid: {}, route_id: {} memo generated.".format(route_data["uid"], route_data["route_id"]))
        else:
            log("uid: {}, route_id: {} route script not found!".format(route_data["uid"], route_data["route_id"]))

        exit(0)


if __name__ == "__main__":
    sys.exit(main())
