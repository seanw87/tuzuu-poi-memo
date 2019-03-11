#!/usr/bin/python
# -*- coding: utf-8 -*-
import copy
import datetime
import os
import random
import subprocess
import time

import yaml


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

    scriptConf = {}
    cmdPath = "../cmd/"
    staticPath = "../static/"
    outputPath = "../output/"
    poiCoverPath = staticPath + "poi_cover/"
    audioPath = staticPath + "audio/"
    fontPath = staticPath + "font/"
    samplePath = staticPath + "sample/"
    logoPath = staticPath + "logo.png"

    routeData = None

    ffmpegCmd = "ffmpeg -y "
    ffmpegFilterComplexFile = cmdPath + "filter_complex."
    ffmpegFilterComplexCmd = ""
    # 音频处理层
    ffmpegBgmusicCmd = "[0:a]afade=enable='between(t,0,2)':t=in:st=0:d=2"   # init
    ffmpegVaudioCmd = ""
    # 输出设置
    ffmpegVoutConf = "-c:v libx264 -pix_fmt {} -r {} -profile:v main -bf 0 -level 3".format(PIXFMT, OUTPUTR)
    ffmpegAoutConf = "-c:a aac -qscale:a 1 -ac 2 -ar 48000 -ab 192k"
    ffmpegMetaConf = "-metadata title=\"我的旅游日记\" -metadata artist=\"土著游\" -metadata album=\"\" " \
                     "-metadata comment=\"\""
    # logo水印位置
    ffmpegLogoPos = "10:10"  # top-right: "main_w-overlay_w-10:10"
    # ffmpeg filter graph 输入序号
    ffmpegInputOffset = 0
    # ffmpeg 图片放大scale(用于动画平滑)
    ffmpegPad = "iw+1:ceil(iw*{0}/sar)+1:(ow-iw)/2:(oh-ih)/2".format(AR)
    # ffmpeg 1: 缩小效果; 2: 放大效果
    ffmpegAnimations = {
        1: "zoompan=z='if(eq(on,0),1.3,zoom-0.0005)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':s={0}".format(OUTPUTRES),
        2: "zoompan=z='min(max(zoom,pzoom)+0.0005,2.0)':x='iw/2-(iw/zoom/2)':"
           "y='ih/2-(ih/zoom/2)':s={0}".format(OUTPUTRES)
    }
    # POI cover style
    ffmpegPoiCoverAnimation = ""
    ffmpegPoiTitleX = "((w-tw)/2)"
    ffmpegPoiTitleY = "min(h/4.5+n,h/4.5+20)"
    ffmpegPoiSubtitleX = "((w-tw)/2)"
    ffmpegPoiSubtitleY = "max(h/3.0-n,h/3.0-20)"
    ffmpegPoiAlpha = "min(1, n/15)"
    ffmpegPoiBoxY = "ih/5.7"
    ffmpegPoiBoxWidth = "iw"
    ffmpegPoiBoxHeight = 300

    def __init__(self, script_conf_path, route_data, tuzuulog, appconf):
        try:
            f = open(script_conf_path, encoding="utf-8")
            self.scriptConf = yaml.load(f)
            self.routeData = route_data
            self.tuzuulog = tuzuulog
            self.appconf = appconf
        except FileNotFoundError:
            self.tuzuulog.log("script conf file not found：" + str(FileNotFoundError))
            print("script conf file not found：" + str(FileNotFoundError))
            exit(0)

    def generate_memo(self):
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
              'ucontents': [{'captions': {'content': '2018年7月1日', 'duration': 3, 'subtitle_color': '0xffffff',
                                          'subtitle_font': 'msyh.ttc', n'subtitle_font_size': 64,
                                          'subtitle_vfx': None, 'subtitle_x': '(w-text_w)/2', 'subtitle_y': '(h-text_h)/2'},
                             'vplist': [{'animation': 2, 'duration': 4, 'file': 'materials/sample/POI_2/WechatIMG33.jpeg',
                                         'subtitle': '', 'subtitle_color': '0xffffff', 'subtitle_font': 'msyh.ttc',
                                         'subtitle_font_size': 32, 'subtitle_vfx': None, 'subtitle_x': 0, 'subtitle_y': 0,
                                         'trans_in': 1, 'trans_out': 2, 'type': 2}]
                             }]
             }]
        """

        # 随机获取背景音乐
        self.get_random_bgmusic()

        # 添加黑色背景(用于blend效果) - input no.0
        self.get_black_bg()

        # 添加透明背景(用于poi cover字幕) - input no.1
        self.get_transparent_bg()

        # 添加输入素材
        self.get_input_materials(total_materials)

        # 超长指令支持
        self.ffmpegCmd += " -filter_complex_script " + self.ffmpegFilterComplexFile

        # 添加水印graph
        self.get_watermark()

        # 处理黑色背景(用于blend效果)
        self.proc_black_bg()

        # 根据POI cover数量生成对应数量的透明背景graph
        self.proc_transparent_bg(total_materials)

        # 1. 单素材处理层
        self.proc_input_materials(total_materials)

        # 2. 素材合成
        over_offset, vaover_offset = self.filter_compose(total_materials)

        # 添加水印
        self.add_watermark(over_offset)

        # 添加作者
        self.add_author()

        # 添加音频
        self.add_audio()

        # 添加输出选项
        self.add_output(vaover_offset)


        # 生成filter_complex脚本文件
        self.tuzuulog.ffmpeg_filter_complex_export(self.ffmpegFilterComplexFile, self.ffmpegFilterComplexCmd)

        # 导出ffmpeg命令到文件
        self.tuzuulog.ffmpeg_cmd_export(self.ffmpegCmd)

        # 执行ffmpeg命令
        self.execute()


    def get_filter_complex_filename(self, route_data):
        self.ffmpegFilterComplexFile += \
            str(route_data["uid"]) + "." + str(route_data["route_id"]) + "." + str(route_data["finishtime"])

    def get_random_bgmusic(self):
        conf_bgmusic = self.scriptConf["memoflow"]["bgmusic"]
        bgmusic = random.choice(conf_bgmusic)
        self.ffmpegCmd += " -i {}{} " . format(self.audioPath, bgmusic)
        # 输入偏移从背景音乐开始
        self.ffmpegInputOffset = 0

    def get_black_bg(self):
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

    def get_input_materials(self, total_materials):
        for poi_materials in total_materials:
            # POI COVER
            poi_cover_path = "{}{}/{}".format(self.poiCoverPath, self.routeData["route_id"], poi_materials["poi_cover"])
            if not os.path.exists(poi_cover_path):
                poi_cover_path = "{}{}".format(self.poiCoverPath, self.POI_DEFAULT_COVER)
            self.ffmpegCmd += " -i {}".format(poi_cover_path)
            # UGC CONTENT
            for material_segs in poi_materials["ucontents"]:
                for input_material in material_segs["vplist"]:
                    inputfile = input_material["file"]

                    # ffmpeg无法读取exif信息，需要事先旋转图片
                    if os.path.exists(inputfile):
                        code = 0
                        try:
                            cmd = "magick mogrify -auto-orient {}".format(input_material["file"])
                            out_bytes = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
                        except subprocess.CalledProcessError as e:
                            out_bytes = e.output  # Output generated before error
                            code = e.returncode  # Return code
                        self.tuzuulog.log("uid: {p0}, ts: {p1}, file: {p4}, code: {p2}, msg: {p3}".format(
                            p0=self.routeData["uid"],
                            p1=datetime.datetime.now(),
                            p2=code,
                            p3=out_bytes.decode('utf-8'),
                            p4=inputfile)
                        )

                    self.ffmpegCmd += " -i {}".format(inputfile)

    def get_watermark(self):
        cmd = "movie={}[watermask];\n".format(self.logoPath)
        self.ffmpegFilterComplexCmd += cmd

    def proc_black_bg(self):
        self.ffmpegInputOffset += 1
        cmd = "[{}:v]trim=duration={}[over0];\n".format(self.ffmpegInputOffset, self.BG_BLACK_DURATION)
        self.ffmpegFilterComplexCmd += cmd

    def proc_transparent_bg(self, total_materials):
        self.ffmpegInputOffset += 1
        cmd = "[{}:v]split=4".format(self.ffmpegInputOffset)
        poi_title_offset = 0
        for poi_materials in total_materials:
            if poi_materials["poi_title"]:
                poi_subtitle_index = 2 * poi_title_offset
                cmd += "[poi{}]".format(poi_subtitle_index)
                cmd += "[poi{}]".format(poi_subtitle_index + 1)
                poi_title_offset += 1
        cmd += ";\n"
        self.ffmpegFilterComplexCmd += cmd

    def proc_input_materials(self, total_materials):
        for poi_materials in total_materials:
            # POI COVER
            self.ffmpegInputOffset += 1
            cmd = "[{p0}:v]pad={p1},scale={p2},{p3}{p4}" \
                  "zoompan=z='min(max(zoom,pzoom)+0.00001,2.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={p11}," \
                  "drawbox=enable='lt(t,{p10})':y={p6}:w={p7}:h={p8}:color=black@0.5:t=fill,trim=duration={p5}," \
                  "setpts=PTS-STARTPTS[out{p9}];\n".format(
                p0=self.ffmpegInputOffset,
                p1=self.ffmpegPad,
                p2=self.PADSCALE,
                p3=self.ffmpegPoiCoverAnimation,
                p4="",
                p5=poi_materials["poi_cover_duration"],
                p6=self.ffmpegPoiBoxY,
                p7=self.ffmpegPoiBoxWidth,
                p8=self.ffmpegPoiBoxHeight,
                p9=self.ffmpegInputOffset - self.UGC_INPUT_OFFSET,
                p10=poi_materials["poi_cover_duration"],
                p11=self.OUTPUTRES)
            self.ffmpegFilterComplexCmd += cmd

            for material_segs in poi_materials["ucontents"]:
                # 需要叠加的字幕
                subtitle = ""
                if material_segs["captions"]:
                    subtitle = ",drawtext=fontfile={p0}:fontcolor={p1}:x={p2}:y={p3}:enable='lt(t, {p4})':text='{p5}':" \
                               "fontsize={p6}".format(
                        p0=self.fontPath + material_segs["captions"]["subtitle_font"],
                        p1=material_segs["captions"]["subtitle_color"],
                        p2=material_segs["captions"]["subtitle_x"],
                        p3=material_segs["captions"]["subtitle_y"],
                        p4=material_segs["captions"]["duration"],
                        p5=material_segs["captions"]["content"],
                        p6=material_segs["captions"]["subtitle_font_size"])

                for material in material_segs["vplist"]:
                    self.ffmpegInputOffset += 1

                    duration = material["duration"]
                    # 如果是图片
                    if material["type"] == self.PICTYPE:
                        animation = self.ffmpegAnimations[material["animation"]]

                        cmd = "[{p0}:v]pad={p1},scale={p2},{p3}{p4},trim=duration={p5}".format(
                            p0=self.ffmpegInputOffset,
                            p1=self.ffmpegPad,
                            p2=self.PADSCALE,
                            p3=animation,
                            p4="",
                            p5=duration)
                        self.ffmpegFilterComplexCmd += cmd

                        if subtitle:
                            self.ffmpegFilterComplexCmd += subtitle
                    # 如果是视频
                    elif material["type"] == self.VIDEOTYPE:
                        cmd = "[{p0}:v]format=pix_fmts={p1},pad={p2},scale={p3},trim=duration={p4}".format(
                            p0=self.ffmpegInputOffset,
                            p1=self.PIXFMT,
                            p2=self.ffmpegPad,
                            p3=self.OUTPUTRES,
                            p4=duration)
                        self.ffmpegFilterComplexCmd += cmd

                        if subtitle:
                            self.ffmpegFilterComplexCmd += subtitle
                    cmd = ",setpts=PTS-STARTPTS [out{}];\n".format(self.ffmpegInputOffset - self.UGC_INPUT_OFFSET)
                    self.ffmpegFilterComplexCmd += cmd

    def filter_compose(self, total_materials):
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
                cmd += "[poi{p0}]drawtext=enable='lt(t, {p1})':fontsize={p2}:fontcolor={p3}:fontfile={p4}:text={p5}:x='{p6}':y='{p7}':alpha='{p8}'," \
                       "trim=duration={p9},setpts=PTS-STARTPTS{p10}[poit{p11}];\n".format(
                    p0=poi_subtitle_index,
                    p1=self.POI_CAPTION_DURATION,
                    p2=self.POI_TITLE_FONTSIZE,
                    p3=self.POI_CAPTION_COLOR,
                    p4=self.fontPath + self.POI_CAPTION_FONT,
                    p5=poi_materials["poi_title"],
                    p6=self.ffmpegPoiTitleX,
                    p7=self.ffmpegPoiTitleY,
                    p8=self.ffmpegPoiAlpha,
                    p9=self.POI_CAPTION_DURATION,
                    p10="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                    p11=poi_subtitle_index)
                cmd += "[poi{p0}]drawtext=enable='lt(t, {p1})':fontsize={p2}:fontcolor={p3}:fontfile={p4}:text={p5}:x='{p6}':y='{p7}':alpha='{p8}'," \
                       "trim=duration={p9},setpts=PTS-STARTPTS{p10}[poit{p11}];\n".format(
                    p0=poi_subtitle_index + 1,
                    p1=self.POI_CAPTION_DURATION,
                    p2=self.POI_SUBTITLE_FONTSIZE,
                    p3=self.POI_CAPTION_COLOR,
                    p4=self.staticPath + "font/" + self.POI_CAPTION_FONT,
                    p5=poi_materials["poi_subtitle"],
                    p6=self.ffmpegPoiSubtitleX,
                    p7=self.ffmpegPoiSubtitleY,
                    p8=self.ffmpegPoiAlpha,
                    p9=self.POI_CAPTION_DURATION,
                    p10="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                    p11=poi_subtitle_index + 1)
                if poi_title_offset == 0:
                    cmd += "[out{p0}]format=pix_fmts={p1},setpts=PTS-STARTPTS{p2}[va{p3}];\n".format(
                        p0=over_offset,
                        p1=self.PIXFMT,
                        p2="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                        p3=over_offset)
                else:
                    cmd += "[out{p0}]format=pix_fmts={p1},fade=t=in:st=0:d={p4}:alpha=0," \
                           "setpts=PTS-STARTPTS{p2}[va{p3}];\n".format(
                        p0=over_offset,
                        p1=self.PIXFMT,
                        p2="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                        p3=over_offset,
                        p4=self.POI_TRANSIT_DURATION)
                cmd += "[over{p0}][va{p1}]overlay[poioo{p2}];\n".format(
                    p0=over_offset,
                    p1=over_offset,
                    p2=poi_title_offset)
                cmd += "[poioo{p0}][poit{p1}]overlay[poiover{p2}];\n".format(
                    p0=poi_title_offset,
                    p1=poi_subtitle_index,
                    p2=poi_title_offset)
                cmd += "[poiover{p0}][poit{p1}]overlay[over{p2}];\n".format(
                    p0=poi_title_offset,
                    p1=poi_subtitle_index + 1,
                    p2=over_offset + 1)

                poi_title_offset += 1
            else:
                if poi_title_offset == 0:
                    cmd += "[out{p0}]format=pix_fmts={p1},setpts=PTS-STARTPTS{p2}[va{p3}];\n".format(
                        p0=over_offset,
                        p1=self.PIXFMT,
                        p2="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                        p3=over_offset)
                else:
                    cmd += "[out{p0}]format=pix_fmts={p1},fade=t=in:st=0:d={p4}:alpha=0," \
                           "setpts=PTS-STARTPTS{p2}[va{p3}];\n".format(
                        p0=over_offset,
                        p1=self.PIXFMT,
                        p2="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                        p3=over_offset,
                        p4=self.POI_TRANSIT_DURATION)
                cmd += "[over{p0}][va{p1}]overlay[over{p2}];\n".format(
                    p0=over_offset,
                    p1=over_offset,
                    p2=over_offset + 1)
            self.ffmpegFilterComplexCmd += cmd
            over_offset += 1

            if poi_title_offset > 0:
                setopts_ts_offset += poi_materials["poi_cover_duration"] - self.POI_TRANSIT_DURATION

            for material_segs in poi_materials["ucontents"]:
                for material in material_segs["vplist"]:
                    # 如果是图片
                    if material["type"] == self.PICTYPE:
                        cmd = "[out{p0}]format=pix_fmts={p1},fade=t=in:st=0:d=1:alpha=1," \
                              "setpts=PTS-STARTPTS{p2}[va{p3}];\n".format(
                            p0=over_offset,
                            p1=self.PIXFMT,
                            p2="" if setopts_ts_offset == 0 else "+" + str(setopts_ts_offset) + "/TB",
                            p3=over_offset)
                        self.ffmpegFilterComplexCmd += cmd

                        cmd = "[over{p0}][va{p1}]overlay[over{p2}];\n".format(
                            p0=over_offset,
                            p1=over_offset,
                            p2=over_offset + 1)
                        self.ffmpegFilterComplexCmd += cmd
                    # 如果是视频
                    elif material["type"] == self.VIDEOTYPE:
                        cmd = "[over{p0}][out{p1}]concat=n=2:v=1:a=0,format={p2}[over{p3}];\n".format(
                            p0=over_offset,
                            p1=over_offset,
                            p2=self.PIXFMT,
                            p3=over_offset + 1)
                        self.ffmpegFilterComplexCmd += cmd

                        self.ffmpegBgmusicCmd += ",afade=enable='between(t,{p0},{p1})':t=out:st={p2}:d=2," \
                                                 "volume=enable='between(t,{p3},{p4})':volume=0.0:eval=frame," \
                                                 "afade=enable='between(t,{p5},{p6})':t=in:st={p7}:d=2".format(
                            p0=setopts_ts_offset + 1,
                            p1=setopts_ts_offset + 1 + 2,
                            p2=setopts_ts_offset + 1,
                            p3=setopts_ts_offset + 1 + 2,
                            p4=setopts_ts_offset + 1 + material["duration"],
                            p5=setopts_ts_offset + 1 + material["duration"],
                            p6=setopts_ts_offset + 1 + material["duration"] + 2,
                            p7=setopts_ts_offset + 1 + material["duration"])
                        self.ffmpegVaudioCmd += ";\n[{p0}:a]adelay={p1},volume=volume=0.8:eval=frame,apad[outa{p2}];\n" \
                                                "[outa{p3}][aover{p4}]amerge=inputs=2[aover{p5}]".format(
                            p0=over_offset + self.UGC_INPUT_OFFSET,
                            p1=(setopts_ts_offset + 1) * 1000,
                            p2=vaover_offset,
                            p3=vaover_offset,
                            p4=vaover_offset,
                            p5=vaover_offset + 1)
                        vaover_offset += 1

                    over_offset += 1
                    setopts_ts_offset += material["duration"] - 1
        self.ffmpegBgmusicCmd += ",atrim=0:{}[aover0]".format(setopts_ts_offset + 1)
        return over_offset, vaover_offset

    def add_watermark(self, over_offset):
        cmd = "[over{}][watermask]overlay={}[outv_relay1];\n".format(over_offset, self.ffmpegLogoPos)
        self.ffmpegFilterComplexCmd += cmd

    def add_author(self):
        script_author_conf = self.scriptConf["memoflow"]["author"]
        if script_author_conf["display"]:
            cmd = "[outv_relay1]drawtext=fontfile={p0}:fontcolor={p1}:x={p2}:y={p3}:text='@{p4}':" \
                  "fontsize={p5}[outv];\n".format(
                p0=self.fontPath + script_author_conf["font"],
                p1=script_author_conf["color"],
                p2=script_author_conf["x"],
                p3=script_author_conf["y"],
                p4=self.routeData["author"],
                p5=script_author_conf["font_size"])
            self.ffmpegFilterComplexCmd += cmd
        else:
            cmd = "[outv_relay1][outv];\n"
            self.ffmpegFilterComplexCmd += cmd

    def add_audio(self):
        self.ffmpegFilterComplexCmd += self.ffmpegBgmusicCmd
        self.ffmpegFilterComplexCmd += self.ffmpegVaudioCmd

    def add_output(self, vaover_offset):
        output_dir = self.outputPath + time.strftime("%Y%m%d", time.localtime())
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        self.ffmpegCmd += " -map [outv] {p0} -map [{p1}] {p2} {p3} -shortest {p5}/mymemo_{p4}.mp4".format(
            p0=self.ffmpegVoutConf,
            p1="aover" + str(vaover_offset),
            p2=self.ffmpegAoutConf,
            p3=self.ffmpegMetaConf,
            p4=self.routeData["author"] + "_" + self.routeData["route_name"] + "_" + str(self.routeData["finishtime"]),
            p5=output_dir
        )

    def execute(self):
        code = 0
        try:
            out_bytes = subprocess.check_output(self.ffmpegCmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            out_bytes = e.output  # Output generated before error
            code = e.returncode  # Return code
        self.tuzuulog.ffmpeg_log("uid: {p0}, ts: {p1}, code: {p2}, msg: {p3}".format(
            p0=self.routeData["uid"],
            p1=datetime.datetime.now(),
            p2=code,
            p3=out_bytes.decode('utf-8'))
        )