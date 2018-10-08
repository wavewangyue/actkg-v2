#!/usr/bin/env python
# -*- coding: utf-8 -*-
from xml.etree import ElementTree
import graph.owlBingimage as owlBingimage
import graph.owlNeo4j as owlNeo4j
import serviceTalkbot
import threading
from time import sleep


answer = {}


def config(request):
    return request.GET["echostr"]


def talk(request):
    url_come = request.get_host()
    xml_come = request.body
    root = ElementTree.fromstring(xml_come)
    to_user_name = root.find('ToUserName').text
    from_user_name = root.find('FromUserName').text
    create_time = root.find('CreateTime').text
    msg_type = root.find('MsgType').text
    question = None
    reply = None
    image = None
    if msg_type == 'text':
        question = root.find('Content').text
    elif msg_type == 'voice':
        question = root.find('Recognition').text
    xml_go = "<xml>"
    xml_go += "<ToUserName><![CDATA[" + from_user_name + "]]></ToUserName>"
    xml_go += "<FromUserName><![CDATA[" + to_user_name + "]]></FromUserName>"
    xml_go += "<CreateTime>" + create_time + "</CreateTime>"
    if question is None:
        reply = "对不起，现在还无法识别你的内容，会继续努力"
    elif '/' in question:
        reply = "对不起，现在还无法识别你的表情，会继续努力"
    elif '收到不支持的消息类型' in question:
        reply = "对不起，现在还无法识别你的内容，会继续努力"
    else:
        noises = ["，", "。", "！", "？"]
        for noise in noises:
            question = str(question).replace(noise, "")
        reply, image = get_reply(question)
    if reply is None:
        reply = "对不起，我不知道该如何回答你"
    # 回复文字消息
    if image is None:
        xml_go += "<MsgType><![CDATA[text]]></MsgType>"
        xml_go += "<Content><![CDATA[" + reply + "]]></Content></xml>"
    else:
        xml_go += "<MsgType><![CDATA[news]]></MsgType>"
        xml_go += "<ArticleCount>1</ArticleCount>"
        xml_go += "<Articles><item>"
        xml_go += "<Title><![CDATA["+question+"]]></Title>"
        xml_go += "<Description><![CDATA["+reply+"\n戳进去，看图谱\n]]></Description>"
        xml_go += "<PicUrl><![CDATA["+image+"]]></PicUrl>"
        xml_go += "<Url><![CDATA["+url_come+"/graph_pure/?q="+question+"]]></Url>"
        xml_go += "</item></Articles></xml>"
    return xml_go


def get_reply(question):
    global answer
    answer = {}
    # 多线程，寻找答案与获取图片同时进行
    t1 = threading.Thread(target=get_answer, args=(question,))
    t2 = threading.Thread(target=get_image, args=(question,))
    threads = [t1, t2]
    for thread in threads:
        thread.setDaemon(True)
        thread.start()
    while 'result' not in answer:
        sleep(0.1)
    if answer['result'] is None:
        return None, None
    # 如果是问答或对话
    if answer['result']['type'] != 'et':
        return answer['result']['answer'], None
    # 如果是实体搜索，需要等待图片
    else:
        while 'image' not in answer:
            sleep(0.1)
        return answer['result']['answer'], answer['image']


def get_answer(question):
    global answer
    answer['result'] = serviceTalkbot.talk(question, autopick=True, graphed=False)


def get_image(question):
    global answer
    answer['image'] = owlBingimage.get_image(question)

