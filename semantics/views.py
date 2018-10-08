# -*- coding: utf-8 -*-
import json
import serviceExtractor
from django.http import HttpResponse


def extraction(request):
    content = request.GET.get('content', None)
    if content is not None:
        triples = serviceExtractor.Relation_Extraction(content)
        graph = paint_graph(triples)
        response = HttpResponse(json.dumps({'triples': triples, 'graph': graph}))
    else:
        response = HttpResponse("No parameters !")
    response["Access-Control-Allow-Origin"] = "*"
    return response


def paint_graph(triples):
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

