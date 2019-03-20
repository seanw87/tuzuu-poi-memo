#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import time
import requests
import json
import pprint

REQUEST_DOMAIN = "https://tuzhuxin5.tuzuu.com"
URI_ROUTESBYTIME = "/user/v1/api/get/user/memo/routesByTime"
URI_ADDUSERMEMO = "/user/v1/api/add/user/memo"
RET_SUCCESS = 10000

curtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def get_route_data(tuzuulog):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=8)
    today_ts = int(time.mktime(time.strptime(str(today), '%Y-%m-%d')))
    yesterday_ts = int(time.mktime(time.strptime(str(yesterday), '%Y-%m-%d')))


    request_url = REQUEST_DOMAIN + URI_ROUTESBYTIME
    headers = {'content-type':'application/json'}
    post_data = {
      "end_time": today_ts,
      "start_time": yesterday_ts,
      "token": "string"
    }

    r = requests.post(request_url, data=json.dumps(post_data), headers=headers)
    ret = json.loads(r.text)
    # pprint.pprint(ret)


    # if "Code" in ret:
    #     if ret["Code"] == RET_SUCCESS:
    #         if "Body" in ret:
    #             if "data" in ret["Body"]:
    #                 return ret["Body"]["data"]
    #     else:
    #         tuzuulog.warning("time: {}, request routes between {} and {} failed. RetCode: {}".format(
    #             curtime, yesterday_ts, today_ts, ret["Code"]), printable=True)
    #
    # tuzuulog.error("time: {}, request routes between {} and {} failed. Data corruption: {}".format(
    #     curtime, yesterday_ts, today_ts, r.text), printable=True)
    # return []

    return [{
        "uid": 123,
        "author": "狂拽酷炫",
        "route_id": 1,
        "route_name": "桂林一日游",
        "finishtime": 1554858302,
        "route": [
            {
                "node": "cut1",
                "materials": [
                    [
                        {"ts": 1544858301, "type": 1, "content": "2018年7月1日"},
                        {"ts": 1544858302, "type": 2, "file": "../static/sample/POI_2/WechatIMG33.jpeg"}
                    ],
                    [
                        {"ts": 1544858303, "type": 2, "file": "../static/sample/POI_2/WechatIMG132.jpeg"}
                    ],
                    [
                        {"ts": 1544858304, "type": 2, "file": "../static/sample/POI_2/WechatIMG133.jpeg"}
                    ],
                    [
                        {"ts": 1544858310, "type": 2, "file": "../static/sample/POI_2/WechatIMG141.jpeg"}
                    ],
                    [
                        {"ts": 1544858501, "type": 1, "content": "看瀑布、坐大象"},
                        {"ts": 1544858602, "type": 2, "file": "../static/sample/POI_2/WechatIMG143.jpeg"},
                        {"ts": 1544858602, "type": 2, "file": "../static/sample/POI_2/WechatIMG145.jpeg"}
                    ],
                    [
                        {"ts": 1544858610, "type": 2, "file": "../static/sample/POI_2/WechatIMG147.jpeg"}
                    ]
                ]
            },
            {
                "node": "cut2",
                "materials": [
                    [
                        {"ts": 1544958610, "type": 2, "file": "../static/sample/POI_4/WechatIMG18.jpeg"}
                    ],
                    [
                        {"ts": 1544958611, "type": 1, "content": "大地一片苍茫"},
                        {"ts": 1544958613, "type": 2, "file": "../static/sample/POI_4/WechatIMG19.jpeg"},
                        {"ts": 1544958615, "type": 2, "file": "../static/sample/POI_4/WechatIMG20.jpeg"}
                    ],
                    [
                        {"ts": 1544959615, "type": 3, "file": "../static/sample/POI_4/2019-03-03-15.07.42.mp4"}
                    ],
                    [
                        {"ts": 1544969620, "type": 1, "content": "山林徒步"},
                        {"ts": 1544969620, "type": 2, "file": "../static/sample/POI_4/WechatIMG21.jpeg"},
                        {"ts": 1544969620, "type": 2, "file": "../static/sample/POI_4/WechatIMG29.jpeg"},
                        {"ts": 1544969620, "type": 3, "file": "../static/sample/POI_4/2019-03-03-15.07.47.mp4"}
                    ]
                ]
            },
            {
                "node": "cut3",
                "materials": [
                    [
                        {"ts": 1544969660, "type": 1, "content": "日常记录"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG22.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG23.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG24.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG25.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG26.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG34.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG37.jpeg"},
                        {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG38.jpeg"},
                    ]
                ]
            }]
        },
        {
            "uid": 123,
            "author": "狂拽酷炫2",
            "route_id": 1,
            "route_name": "桂林一日游",
            "finishtime": 1554858302,
            "route": [
                {
                    "node": "cut1",
                    "materials": [
                        [
                            {"ts": 1544858301, "type": 1, "content": "2018年7月1日"},
                            {"ts": 1544858302, "type": 2, "file": "../static/sample/POI_2/WechatIMG33.jpeg"}
                        ],
                        [
                            {"ts": 1544858303, "type": 2, "file": "../static/sample/POI_2/WechatIMG132.jpeg"}
                        ],
                        [
                            {"ts": 1544858304, "type": 2, "file": "../static/sample/POI_2/WechatIMG133.jpeg"}
                        ],
                        [
                            {"ts": 1544858310, "type": 2, "file": "../static/sample/POI_2/WechatIMG141.jpeg"}
                        ],
                        [
                            {"ts": 1544858501, "type": 1, "content": "看瀑布、坐大象"},
                            {"ts": 1544858602, "type": 2, "file": "../static/sample/POI_2/WechatIMG143.jpeg"},
                            {"ts": 1544858602, "type": 2, "file": "../static/sample/POI_2/WechatIMG145.jpeg"}
                        ],
                        [
                            {"ts": 1544858610, "type": 2, "file": "../static/sample/POI_2/WechatIMG147.jpeg"}
                        ]
                    ]
                },
                {
                    "node": "cut2",
                    "materials": [
                        [
                            {"ts": 1544958610, "type": 2, "file": "../static/sample/POI_4/WechatIMG18.jpeg"}
                        ],
                        [
                            {"ts": 1544958611, "type": 1, "content": "大地一片苍茫"},
                            {"ts": 1544958613, "type": 2, "file": "../static/sample/POI_4/WechatIMG19.jpeg"},
                            {"ts": 1544958615, "type": 2, "file": "../static/sample/POI_4/WechatIMG20.jpeg"}
                        ],
                        [
                            {"ts": 1544959615, "type": 3, "file": "../static/sample/POI_4/2019-03-03-15.07.42.mp4"}
                        ],
                        [
                            {"ts": 1544969620, "type": 1, "content": "山林徒步"},
                            {"ts": 1544969620, "type": 2, "file": "../static/sample/POI_4/WechatIMG21.jpeg"},
                            {"ts": 1544969620, "type": 2, "file": "../static/sample/POI_4/WechatIMG29.jpeg"},
                            {"ts": 1544969620, "type": 3, "file": "../static/sample/POI_4/2019-03-03-15.07.47.mp4"}
                        ]
                    ]
                },
                {
                    "node": "cut3",
                    "materials": [
                        [
                            {"ts": 1544969660, "type": 1, "content": "日常记录"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG22.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG23.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG24.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG25.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG26.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG34.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG37.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG38.jpeg"},
                        ]
                    ]
                }
            ]
        },
        {
            "uid": 123,
            "author": "狂拽酷炫3",
            "route_id": 1,
            "route_name": "桂林一日游",
            "finishtime": 1554858302,
            "route": [
                {
                    "node": "cut1",
                    "materials": [
                        [
                            {"ts": 1544858301, "type": 1, "content": "2018年7月1日"},
                            {"ts": 1544858302, "type": 2, "file": "../static/sample/POI_2/WechatIMG33.jpeg"}
                        ],
                        [
                            {"ts": 1544858303, "type": 2, "file": "../static/sample/POI_2/WechatIMG132.jpeg"}
                        ],
                        [
                            {"ts": 1544858304, "type": 2, "file": "../static/sample/POI_2/WechatIMG133.jpeg"}
                        ],
                        [
                            {"ts": 1544858310, "type": 2, "file": "../static/sample/POI_2/WechatIMG141.jpeg"}
                        ],
                        [
                            {"ts": 1544858501, "type": 1, "content": "看瀑布、坐大象"},
                            {"ts": 1544858602, "type": 2, "file": "../static/sample/POI_2/WechatIMG143.jpeg"},
                            {"ts": 1544858602, "type": 2, "file": "../static/sample/POI_2/WechatIMG145.jpeg"}
                        ],
                        [
                            {"ts": 1544858610, "type": 2, "file": "../static/sample/POI_2/WechatIMG147.jpeg"}
                        ]
                    ]
                },
                {
                    "node": "cut2",
                    "materials": [
                        [
                            {"ts": 1544958610, "type": 2, "file": "../static/sample/POI_4/WechatIMG18.jpeg"}
                        ],
                        [
                            {"ts": 1544958611, "type": 1, "content": "大地一片苍茫"},
                            {"ts": 1544958613, "type": 2, "file": "../static/sample/POI_4/WechatIMG19.jpeg"},
                            {"ts": 1544958615, "type": 2, "file": "../static/sample/POI_4/WechatIMG20.jpeg"}
                        ],
                        [
                            {"ts": 1544959615, "type": 3, "file": "../static/sample/POI_4/2019-03-03-15.07.42.mp4"}
                        ],
                        [
                            {"ts": 1544969620, "type": 1, "content": "山林徒步"},
                            {"ts": 1544969620, "type": 2, "file": "../static/sample/POI_4/WechatIMG21.jpeg"},
                            {"ts": 1544969620, "type": 2, "file": "../static/sample/POI_4/WechatIMG29.jpeg"},
                            {"ts": 1544969620, "type": 3, "file": "../static/sample/POI_4/2019-03-03-15.07.47.mp4"}
                        ]
                    ]
                },
                {
                    "node": "cut3",
                    "materials": [
                        [
                            {"ts": 1544969660, "type": 1, "content": "日常记录"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG22.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG23.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG24.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG25.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG26.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG34.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG37.jpeg"},
                            {"ts": 1544969660, "type": 2, "file": "../static/sample/POI_5/WechatIMG38.jpeg"},
                        ]
                    ]
                }
            ]
        }
    ]

def add_user_memo(post_data, tuzuulog):
    request_url = REQUEST_DOMAIN + URI_ADDUSERMEMO
    headers = {'content-type': 'application/json'}

    r = requests.post(request_url, data=json.dumps(post_data), headers=headers)
    ret = json.loads(r.text)
    pprint.pprint(ret)

    if "Code" in ret:
        if ret["Code"] == RET_SUCCESS:
            tuzuulog.info("time: {}, Post add user memo succeeded, info: {}".format(
                curtime, json.dumps(post_data)), printable=True)
            return True
        else:
            tuzuulog.warning("time: {}, Post add user memo failed, info: {}".format(
                curtime, json.dumps(post_data)), printable=True)

    tuzuulog.error("time: {}, Post add user memo failed, Data corruption: {}, info: {},".format(
        curtime, r.text, json.dumps(post_data)), printable=True)
    return False