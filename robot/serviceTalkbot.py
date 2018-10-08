# coding=utf-8
import graph.serviceKG as serviceKG
import owlTuring
import sys
import threading
from time import sleep
reload(sys)
sys.setdefaultencoding('utf8')
answer = {}


def talk(question, neoid=None, autopick=False):
    global answer
    answer = {}
    # 多线程，问答对话同时进行
    t1 = threading.Thread(target=get_answer_knowledge_graph, args=(question, neoid, autopick))
    t2 = threading.Thread(target=get_answer_turing, args=(question,))
    threads = [t1, t2]
    for thread in threads:
        thread.setDaemon(True)
        thread.start()
    # 先看问答结果
    while 'qa' not in answer:
        sleep(0.1)
    if answer['qa'] is not None:
        return answer['qa']
    # 再看对话结果
    while 'tk' not in answer:
        sleep(0.1)
    if answer['tk'] is not None:
        return answer['tk']
    return None


def get_answer_knowledge_graph(question, neoid, autopick):
    global answer
    answer['qa'] = serviceKG.knowledge_graph(question, neoid=neoid, autopick=autopick)


def get_answer_turing(question):
    global answer
    answer['tk'] = owlTuring.api(question)
