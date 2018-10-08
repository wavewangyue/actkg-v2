# coding=utf-8
import serviceNlp
import logging
import owlNeo4j
import owlBingimage

# 图谱搜索深度
maxLevel = 3


def knowledge_graph(question, keyid=None, autopick=False):
    # 如果已经锁定实体，直接加入同名实体列表；如果没有锁定实体，需要查询同名实体列表
    same_name_entity_list = []
    seg_list = []
    if keyid is not None:
        same_name_entity_list.append({'keyid_neo4j': keyid})
    else:
        logging.info('question:' + question)
        # 分词及词性标注
        seg_list_complete = serviceNlp.segment(question)
        seg_result = ""
        for word in seg_list_complete:
            seg_list.append(word.word)
            seg_result += word.word + '/' + word.flag + ' '
        logging.info('segment result:' + seg_result)
        # 实体链接
        entity_focus = serviceNlp.ner(seg_list_complete)
        if entity_focus is None:
            return None
        logging.info('ner_result:' + entity_focus)
        del seg_list[seg_list.index(entity_focus)]
        # 通过实体名获取同名实体id列表
        same_name_entity_list_complete = owlNeo4j.get_entity_id(entity_focus)
        for entity in same_name_entity_list_complete:
            same_name_entity_list.append({'keyid_neo4j': entity['row'][0], 'subname': entity['row'][1], 'keyid_baike':entity['row'][2]})
        # 如果是实体搜索而不是问答，且出现同名实体，则需要返回同名实体列表供用户选择
        if len(seg_list) == 0 and len(same_name_entity_list) > 1:
            if autopick:
                same_name_entity_list = graph_autopick(same_name_entity_list)
            else:
                return {'entities': same_name_entity_list}
    # 获取同名实体图谱列表
    graph_result_list = []
    for entity in same_name_entity_list:
        graph_result_list.append(bloom(entity['keyid_neo4j']))
    # 基于图谱列表进行中文问答，并选择最优图谱
    graph_result = chinese_qa(seg_list, graph_result_list)
    return graph_result


def chinese_qa(seg_list, graph_result_list):
    max_point = -1
    max_graph_result = None
    if len(seg_list) > 0:
        for graph_result in graph_result_list:
            graph_result, point = serviceNlp.lightment(graph_result, seg_list)
            if point > max_point:
                max_graph_result = graph_result
                max_point = point
    else:
        max_graph_result = graph_result_list[0]
    # 答句自然语言生成
    max_graph_result = serviceNlp.answerment(max_graph_result)
    return max_graph_result


def bloom(keyid):
    graph_result = {'nodes': [], 'links': [], 'answerpath': [0], 'answerlist': [], 'answer': None}
    pointer = 0  # 待被查询的节点队列指针
    # 添加根节点
    entity_info = owlNeo4j.get_entity_info(keyid)
    new_node = {'id': 0, 'name': entity_info['name'], 'category': entity_info['label'], 'keyId': keyid, 'value': 0}
    graph_result['nodes'].append(new_node)
    # 广度递归后续节点，如果层数没有达到上限，并且还存在待被查询的节点，并且目前节点数小于100就继续
    while (len(graph_result['nodes']) > pointer) and (len(graph_result['nodes']) < 100) and (graph_result['nodes'][pointer]['value'] < maxLevel):
        related_entities = owlNeo4j.get_related_entities(graph_result['nodes'][pointer]['keyId'])
        for related_entity in related_entities:
            related_entity = related_entity['row']
            relation = related_entity[0]
            label = related_entity[1]
            name = related_entity[2]
            keyid = related_entity[3]
            # 如果这个节点已经存在，只加入新关系，不加入新节点
            flag_exist = False
            for i, node_exist in enumerate(graph_result['nodes']):
                if node_exist['keyId'] == keyid:
                    new_edge = {'id': len(graph_result['links']), 'source': pointer, 'target': i, 'level': graph_result['nodes'][pointer]['value']+1, 'name': relation}
                    graph_result['links'].append(new_edge)
                    flag_exist = True
                    break
            if flag_exist:
                continue
            # 如果这个节点之前不存在，加入新关系，加入新节点
            new_node = {'id': len(graph_result['nodes']), 'name': name, 'category': label, 'keyId': keyid, 'value': graph_result['nodes'][pointer]['value']+1}
            new_edge = {'id': len(graph_result['links']), 'source': pointer, 'target': new_node['id'], 'level': new_node['value'], 'name': relation}
            graph_result['nodes'].append(new_node)
            graph_result['links'].append(new_edge)
        pointer += 1
    return graph_result


def get_entity_info_with_image(keyid):
    result = owlNeo4j.get_entity_info(keyid)
    image_url = owlBingimage.get_image(result['name'])
    result['image'] = image_url
    return result


def graph_autopick(same_name_entity_list):
    result = None
    for entity in same_name_entity_list:
        if result is None:
            result = entity
        elif entity['keyid_baike'] < result['keyid_baike']:
            result = entity
    return [result]
