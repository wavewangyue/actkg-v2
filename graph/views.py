# -*- coding: utf-8 -*-
import serviceKG
import serviceQA
import owlBingimage
import json
from django.http import HttpResponse
import actkg.config as config
import owlSubServers
import owlNeo4j
import serviceQA_simple


# 与图谱相关
def graph(request):
    question = request.GET.get('q', None)
    neoid = request.GET.get('id', None)
    autopick = request.GET.get('autopick', "false").lower()
    if autopick == "true":
        autopick = True
    else:
        autopick = False
    response = HttpResponse(json.dumps(serviceKG.knowledge_graph(question, neoid=neoid, autopick=autopick), ensure_ascii=False))
    response["Access-Control-Allow-Origin"] = "*"
    return response


# 与实体信息相关
def entity(request):
    neoid = request.GET.get('id', None)
    name = request.GET.get('name', None)
    autopick = request.GET.get('autopick', "false").lower()
    if autopick == "true":
        autopick = True
    else:
        autopick = False
    response = HttpResponse(json.dumps(serviceKG.entity_search(name, neoid, autopick), ensure_ascii=False))
    response["Access-Control-Allow-Origin"] = "*"
    return response


# 问答
def qa(request):
    question = request.GET.get('q', None)
    if question is not None:
        # 进行中文问答
        qa_result = serviceQA.chinese_qa(question)
        if (qa_result is None) or (len(qa_result['ents']) == 0) or (len(qa_result['path']) == 0):
            response = HttpResponse(json.dumps("No answer !"))
        else:
            triples = qa_result['path']
            answer = serviceKG.answer_generate(qa_result['path'])
            result = {"triples": triples, "answer": answer}
            response = HttpResponse(json.dumps(result, ensure_ascii=False))
    else:
        response = HttpResponse(json.dumps("No parameters !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


# 问答（仅状态机方法）
def simple_qa(request):
    question = request.GET.get('q', None)
    if question is not None:
        # 进行中文问答
        qa_result = serviceQA_simple.chinese_qa(question)
        if (qa_result is None) or (len(qa_result['ents']) == 0) or (len(qa_result['path']) == 0):
            response = HttpResponse(json.dumps("No answer !"))
        else:
            triples = qa_result['path']
            answer = serviceKG.answer_generate(qa_result['path'])
            result = {"triples": triples, "answer": answer}
            response = HttpResponse(json.dumps(result, ensure_ascii=False))
    else:
        response = HttpResponse(json.dumps("No parameters !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


# schema获取固有属性
def get_attributes(request):
    category_attributes = config.category_attributes
    str_map = {'single_value': '单值类', 'multi_value':'枚举类', 'numeric_value':'数值型', 'string_value':'字符串型', 'date_value':'日期型', 'object_value':'对象型'}
    cate = request.GET.get('cate', None)
    if cate is not None:
        if cate in category_attributes:
            for attribute in category_attributes[cate]:
                for i in range(len(attribute)):
                    if attribute[i] in str_map:
                        attribute[i] = str_map[attribute[i]]
            response = HttpResponse(json.dumps(category_attributes[cate], ensure_ascii=False))
        else:
            response = HttpResponse(json.dumps([]))
    else:
        response = HttpResponse(json.dumps("No parameters !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


# schema获取类内实体
def get_category_entities(request):
    category_entitysamples = config.category_entitysamples
    cate = request.GET.get('cate', None)
    if cate is not None:
        samples = []
        if cate in category_entitysamples:
            samples = category_entitysamples[cate]
        response = HttpResponse(json.dumps(samples, ensure_ascii=False))
    else:
        response = HttpResponse(json.dumps("No parameters !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


# 测试用接口
def test(request):
    owlSubServers.test()


