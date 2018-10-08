# coding=utf-8
import owlNeo4j
import serviceQA
import json
import owlSubServers
import actkg.config as config

keyid_pop = config.keyid_pop


def knowledge_graph(question, neoid=None, autopick=False):
    # 如果已经选好了实体，直接返回实体检索结果
    if neoid is not None:
        return decorate(neoid, style='BASIC')
    question.strip()
    # 如果是类别查询
    symbol = "c::"
    if question.find(symbol) == 0:
        question = question[len(symbol):]
        return decorate(question, style='CS')
    # 如果是关系查询
    symbol = "r::"
    if question.find(symbol) == 0:
        question = question[len(symbol):]
        return decorate(question, style='RS')
    # 如果是双实体查询
    if ' ' in question:
        return decorate(question.split(' '), style='TES')
    # 中文问答：计算型问答
    qa_result = owlSubServers.count_qa(question)
    if qa_result is not None:
        return decorate(qa_result, style='QA_count')
    # 中文问答：检索型问答
    qa_result = serviceQA.chinese_qa(question)
    if (qa_result is None) or (qa_result['ents'] == []):
        return None
    # 如果是实体检索
    if qa_result['path'] == []:
        if autopick or (len(qa_result['ents']) == 1):  # 如果开启自动选择或不存在同名实体
            return decorate(qa_result['ents'][0]['neoId'], style='BASIC')
        else:  # 如果存在同名实体且没开启自动选择
            return decorate(qa_result['ents'], style='SNET')
    # 如果是问答检索
    else:
        return decorate(qa_result['path'], style='QA')


# 针对不同的需求配置不同的结果json文件
def decorate(data, style):
    if style == 'BASIC':  # 普通实体查询配置，data为实体的neoId
        result = bloom(data)
        result['answer'] = "为你找到关于 " + result['nodes'][0]['name'] + " 的信息"
        return result
    if style == 'SNET':  # 同名实体列表配置，data为同名实体列表
        result = {'entities': data, 'answer': '请在同名实体列表中选择'}
        return result
    if style == 'QA':  # 问答配置，data为问答结果
        result = bloom(data[0][0]['neoId'], path=data)
        result['answer'] = answer_generate(data)
        return result
    if style == 'CS':  # 类别查询配置，data为类别名
        entities = owlNeo4j.get_entities_by_label(data)
        if entities is None:
            return "No entity found"
        entities = eneities_sort(entities)[:80]
        graph_result = {'nodes': [], 'links': []}
        for index, entity in enumerate(entities):
            graph_result['nodes'].append({'id': index, 'name': entity['name'], 'neoId': entity['neoId'], 'value': 1, 'category': entity['label']})
        graph_result['answer'] = '为您找到 '+data+' 类别下的实体'
        return graph_result
    if style == 'RS':  # 关系查询配置，data为关系名
        triples = owlNeo4j.get_triples_by_relation(data)
        if triples is None:
            return "No entity found"
        graph_result = {'nodes': [], 'links': []}
        for index, triple in enumerate(triples):
            i = None
            j = None
            for index0, e0 in enumerate(graph_result['nodes']):
                if triple[0]['neoId'] == e0['neoId']:
                    i = index0
                if triple[2]['neoId'] == e0['neoId']:
                    j = index0
            if i is None:
                i = len(graph_result['nodes'])
                graph_result['nodes'].append({'id': i, 'name': triple[0]['name'], 'neoId': triple[0]['neoId'], 'value': 1,
                                              'category': triple[0]['label']})
            if j is None:
                j = len(graph_result['nodes'])
                graph_result['nodes'].append({'id': j, 'name': triple[2]['name'], 'neoId': triple[2]['neoId'], 'value': 1,
                                              'category': triple[2]['label']})
            graph_result['links'].append({'id': len(graph_result['links']), 'source': i, 'target': j, 'name': triple[1]})
        graph_result['answer'] = '为您找到具有 '+data+' 关系的实体对'
        return graph_result
    if style == 'TES':  # 双实体关系查询配置，data为实体名列表
        if len(data) != 2:
            return {'answer': '输入实体个数不正确'}
        path = two_entity_relation_path(data[0], data[1])
        if path is not None:
            graph_result = bloom(path[0][0]['neoId'], path=path)
            graph_result['answer'] = '为您找到 '+data[0]+' 到 '+data[1]+' 的最短路径'
            return graph_result
    if style == 'QA_count': # 计算型问答，data为问答子服务返回的结果
        graph_result = {'nodes': [], 'links': []}
        for triple in data['triples']:
            node1 = {'id': len(graph_result['nodes']), 'name': triple[0]['name'], 'category': triple[0]['label'], 'neoId': triple[0]['neoId'], 'value':1}
            graph_result['nodes'].append(node1)
            node2 = {'id': len(graph_result['nodes']), 'name': triple[2], 'category': '属性值', 'neoId': None, 'value':1}
            graph_result['nodes'].append(node2)
            graph_result['links'].append({'id':len(graph_result['links']), 'source': node1['id'], 'target': node2['id'], 'name': triple[1]})
        if data['type'] == 'compare':
            graph_result['answerpath'] = [node['id'] for node in graph_result['nodes']]
            graph_result['answer'] = data['target']
        elif data['type'] == 'rank':
            graph_result['answerpath'] = [data['target']*2, data['target']*2+1]
            graph_result['answer'] = data['triples'][data['target']][0]['name']
        for fnode in graph_result['answerpath']:
            graph_result['nodes'][fnode]['value'] = 0
        return graph_result
    return None


# 生成图谱
def bloom(root, path=None):
    graph_result = {'nodes': [], 'links': [], 'answerpath': [], 'answerlist': []}
    if root is None:
        return graph_result
    pointer = 0  # 待被查询的节点队列指针
    max_level = 3
    # 添加根节点
    entity_info = owlNeo4j.get_entity_info_by_id(root)
    new_node = {'id': 0, 'name': entity_info['name'], 'category': entity_info['label'], 'neoId': root, 'value': 0}
    graph_result['nodes'].append(new_node)
    # 广度递归后续节点，如果层数没有达到上限，并且还存在待被查询的节点，并且目前节点数小于100就继续
    while (len(graph_result['nodes']) > pointer) and (len(graph_result['nodes']) < 100) and (graph_result['nodes'][pointer]['value'] < max_level):
        related_entities = owlNeo4j.get_related_entities_by_id(graph_result['nodes'][pointer]['neoId'])
        for related_entity in related_entities:
            relation = related_entity['name']
            label = related_entity['target_label']
            name = related_entity['target_name']
            neoid = related_entity['target_neoId']
            # 如果这个节点已经存在，只加入新关系，不加入新节点
            flag_exist = False
            for i, node_exist in enumerate(graph_result['nodes']):
                if node_exist['neoId'] == neoid:
                    new_edge = {'id': len(graph_result['links']), 'source': pointer, 'target': i, 'level': graph_result['nodes'][pointer]['value']+1, 'name': relation}
                    graph_result['links'].append(new_edge)
                    flag_exist = True
                    break
            if flag_exist:
                continue
            # 如果这个节点之前不存在，加入新关系，加入新节点
            new_node = {'id': len(graph_result['nodes']), 'name': name, 'category': label, 'neoId': neoid, 'value': graph_result['nodes'][pointer]['value']+1}
            new_edge = {'id': len(graph_result['links']), 'source': pointer, 'target': new_node['id'], 'level': new_node['value'], 'name': relation}
            graph_result['nodes'].append(new_node)
            graph_result['links'].append(new_edge)
        pointer += 1
    graph_result['answerpath'].append(0)
    # 加入答案路径
    if path is not None:
        graph_result['answerlist'] = path
        for index, triple in enumerate(path):
            i = None
            j = None
            for index0, e0 in enumerate(graph_result['nodes']):
                if triple[0]['neoId'] == e0['neoId']:
                    i = index0
                if triple[2]['neoId'] == e0['neoId']:
                    j = index0
            if i is None:
                i = len(graph_result['nodes'])
                graph_result['nodes'].append({'id': i, 'name': triple[0]['name'], 'neoId': triple[0]['neoId'], 'value': 1,
                                              'category': triple[0]['label']})
            if j is None:
                j = len(graph_result['nodes'])
                graph_result['nodes'].append({'id': j, 'name': triple[2]['name'], 'neoId': triple[2]['neoId'], 'value': 1,
                                              'category': triple[2]['label']})
            graph_result['links'].append({'id': len(graph_result['links']), 'source': i, 'target': j, 'name': triple[1]})
            if i not in graph_result['answerpath']:
                graph_result['answerpath'].append(i)
            if j not in graph_result['answerpath']:
                graph_result['answerpath'].append(j)
    return graph_result


# 从结构化数据生成自然语言回答
def answer_generate(path):
    if 'ans_from_desc' in path[-1][-1]:  # 如果答案来自于描述文本
        result = path[-1][-1]['ans_from_desc']
    else:
        result = ""
        for i in range(len(path)):
            if (i < len(path)-1) and (path[i][0]['name'] == path[i+1][0]['name']) and (path[i][1] == path[i+1][1]):  # 枚举类型答案实体
                enumerate_answer_list = [step[2]['name'] for step in path[i:]]
                result += path[i][0]['name'] + '的' + path[i][1] + '有' + str(len(enumerate_answer_list)) + '个：'
                result += "、".join(enumerate_answer_list)
                break
            else:
                if i > 0:
                    result += "，"
                result += path[i][0]['name']+'的'+path[i][1]+'是'+path[i][2]['name']

    return result


# 同名实体列表排序
def eneities_sort(entities):
    new_list = []
    while len(entities) > 0:
        top_entity = None
        for entity in entities:
            if top_entity is None:
                top_entity = entity
            if entity['keyId'] in keyid_pop:
                if (top_entity['keyId'] not in keyid_pop)or(keyid_pop[entity['keyId']] > keyid_pop[top_entity['keyId']]):
                    top_entity = entity
        new_list.append(top_entity)
        entities.remove(top_entity)
    return new_list


# 双实体关系路径检索
def two_entity_relation_path(e1_name, e2_name):
    entities1 = owlNeo4j.get_entity_list_by_name(e1_name)
    entities1 = eneities_sort(entities1)
    entities2 = owlNeo4j.get_entity_list_by_name(e2_name)
    entities2 = eneities_sort(entities2)
    path = None
    for e1 in entities1:
        for e2 in entities2:
            if e1['neoId'] == e2['neoId']:
                continue
            shortest_path = owlNeo4j.get_path_between_entities(e1['neoId'], e2['neoId'])
            if shortest_path is None:
                continue
            path = []
            source = None
            for step in shortest_path:
                if len(step) == 0:
                    continue
                target = step['keyId']
                if source is not None:
                    triple = owlNeo4j.get_relation_between_entities(source, target)
                    path.append(triple)
                source = target
            if path is not None:
                break
        if path is not None:
            break
    return path


# 简单实体搜索
def entity_search(name=None, neoid=None, autopick=False):
    # 如果按id搜索，直接返回信息
    if neoid is not None:
        return owlNeo4j.get_entity_info_by_id(neoid)
    # 如果是按名搜索，返回同名实体列表
    else:
        results = owlNeo4j.get_entity_list_by_name(name)
        results_sorted = eneities_sort(results)
        if len(results_sorted) == 0:
            return []
        if autopick or (len(results_sorted) == 1):
            return results_sorted[0]
        else:
            return results_sorted
