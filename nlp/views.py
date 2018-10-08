# -*- coding: utf-8 -*-
import json
import graph.owlSubServers as owlSubServers
from django.http import HttpResponse
import serviceNLP


def parse(request):
    content = request.GET.get('content', None)
    level = int(request.GET.get('level', 2))
    if content is not None:
        response = HttpResponse(json.dumps(serviceNLP.parse(content, level), ensure_ascii=False))
    else:
        response = HttpResponse(json.dumps("No content !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


def extraction(request):
    content = request.GET.get('content', None)
    if content is not None:
        results = owlSubServers.triple_extraction(content)
        all_triples = []
        for result in results:
            all_triples += result['triples']
        graph = bloom_by_triples(all_triples)
        response = HttpResponse(json.dumps({'results':results, 'graph': graph}, ensure_ascii=False))
    else:
        response = HttpResponse(json.dumps("No content !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


def linking(request):
    content = request.GET.get('content', None)
    if content is not None:
        result = serviceNLP.parse(content, 4)
        content_plus = ''
        for i in range(len(result['seg'])):
            if result['nel'][i] != '':
                content_plus += '<>'
        response = HttpResponse(json.dumps({'content': content_plus, 'graph': {}}, ensure_ascii=False))
    else:
        response = HttpResponse(json.dumps("No content !"))
    response["Access-Control-Allow-Origin"] = "*"
    return response


def bloom_by_triples(triples):
    nodes = []
    links = []
    for triple in triples:
        e1 = triple[0]
        r = triple[1]
        e2 = triple[2]
        e1_index = None
        e2_index = None
        for i in range(len(nodes)):
            if nodes[i]['name'] == e1:
                e1_index = i
            elif nodes[i]['name'] == e2:
                e2_index = i
        if e1_index is None:
            e1_index = len(nodes)
            nodes.append({'name': e1, 'id': e1_index, 'category': e1})
        if e2_index is None:
            e2_index = len(nodes)
            nodes.append({'name': e2, 'id': e2_index, 'category': e2})
        links.append({'id': len(links), 'source': e1_index, 'target': e2_index, 'name': r})
    return {'nodes': nodes, 'links': links}

