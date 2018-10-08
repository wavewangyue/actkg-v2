# coding=utf-8
import jieba.posseg as posseg
import jieba
import owlNeo4j
import serviceWord2vec
import logging
import sys
import serviceKG
import json

reload(sys)
sys.setdefaultencoding('utf8')


def chinese_qa(question):
    logging.info('question:' + question)
    # 分词
    seg_list_complete = segment(question)
    seg_list = []
    seg_result = ""
    for word in seg_list_complete:
        seg_list.append(word.word)
        seg_result += word.word + '/' + word.flag + ' '
    logging.info('segment result:' + seg_result)
    # 有效性检验
    if not valuable(seg_list_complete):
        return None
    # 问答有穷自动机
    qa_result = automata(seg_list)
    return qa_result


# 问答有穷自动机
def automata(seg_list):
    threshold_1 = 0.6  # 向量相似度匹配的状态转移阈值
    threshold_2 = 0.15  # 关系预测匹配的状态转移阈值
    threshold_3 = 0.4  # 文本答案选择匹配的状态转移阈值
    states = [{'header': None, 'tailer': None, 'available_words': [], 'path': [], 'score': 0}]
    caches = {}
    for word in seg_list:
        new_states = []
        for state in states:
            state['available_words'].append(word)
            # 对于START状态
            if (state['header'] is None):
                entity_name = "".join(state['available_words'])
                same_name_entity_list = owlNeo4j.get_entity_list_by_name(entity_name)
                for entity in same_name_entity_list:
                    new_states.append({'header': entity, 'tailer': None, 'available_words': [], 'path': [], 'score': 1})
            # 对于非START状态
            else:
                if state['tailer'] is None:
                    source = {'name': state['header']['name'], 'label': state['header']['label'], 'neoId': state['header']['neoId']}
                else:
                    source = state['tailer']
                if source['neoId'] is None:  # neoId is None 意味着路径走到了一个不可跳转的状态
                    continue
                if source['neoId'] not in caches:   # 整理这个实体的关系与属性集，加入到缓存中等待使用
                    caches[source['neoId']] = []
                    relations = owlNeo4j.get_related_entities_by_id(source['neoId'])
                    for relation in relations:  # 添加关系
                        caches[source['neoId']].append(relation)
                    props = owlNeo4j.get_entity_info_by_id(source['neoId'])
                    for prop in props:  # 添加属性，如果已经有同名关系出现，则该属性不添加
                        if any(prop == relation['name'] for relation in caches[source['neoId']]):
                            continue
                        caches[source['neoId']].append({'name': prop, 'target_label': '属性值', 'target_name': props[prop], 'target_neoId': None})
                # 对于所有关系属性逐个进行相似度匹配, 大于阈值就进行状态转移
                link2state_map = {}
                for link in caches[source['neoId']]:
                    score = serviceWord2vec.get_similarity(state['available_words'], list(jieba.cut(link['name'])))
                    if score > threshold_1:
                        # 如果之前没添加过同名关系，直接进行状态转移，记录跳转路径
                        if link['name'] not in link2state_map:
                            new_path = [step for step in state['path']]
                            target = {'name': link['target_name'], 'label': link['target_label'], 'neoId': link['target_neoId']}
                            new_path.append([source, link['name'], target])
                            new_score = state['score']*(1+score-threshold_1)
                            new_states.append({'header': state['header'], 'tailer': target, 'available_words': [], 'path': new_path, 'score': new_score})
                            link2state_map[link['name']] = len(new_states) - 1
                        # 如果之前已经添加过一个同名关系，说明此关系是多值类(比如：知名校友)，直接把此关系追加到同名关系上
                        else:
                            state_num = link2state_map[link['name']]
                            new_tailer = new_states[state_num]['tailer'].copy()
                            new_tailer['neoId'] = None  # 如果此关系是多值类，则它不能再进行状态转移，所以把tailer neoId标记为None
                            new_states[state_num]['tailer'] = new_tailer
                            target = {'name': link['target_name'], 'label': link['target_label'], 'neoId': link['target_neoId']}
                            new_states[state_num]['path'].append([source, link['name'], target])
        states += new_states

    # 选择获取最高评分的那些路径
    max_states = []
    for state in states:
        if (state['header'] is not None):
            if (max_states == []) or (state['score'] > max_states[0]['score']):
                max_states = [state]
            elif (state['score'] == max_states[0]['score']):
                if (state['score'] == 1) and (len(state['available_words']) < len(max_states[0]['available_words'])): # 在只识别到了实体的状态里，优先选择最长匹配到的实体
                    max_states = [state]
                else:
                    max_states.append(state)
    # 再对状态里的中心实体根据实体知名度进行排序
    entities = [state['header'] for state in max_states if state['header'] is not None]
    entities = serviceKG.eneities_sort(entities)
    # 如果只识别到实体，则返回实体列表，否则返回最优路径
    if (max_states == []) or (max_states[0]['score'] == 0):
        return {'ents': entities, 'path': []}
    else:
        paths = [state['path'] for state in max_states if state['header'] == entities[0]]
        return {'ents': [entities[0]], 'path': paths[0]}


# 分词
def segment(sentence):
    fliter_list = ['的']
    seg_list_unflit = list(posseg.cut(sentence))
    seg_list_flit = []
    for word in seg_list_unflit:
        if word.word not in fliter_list:
            seg_list_flit.append(word)
    return seg_list_flit


# 有效性检验，目的是避免问答系统应答范围太广而干涉到对话系统
def valuable(seg_list_complete):
    value_list = ['i', 'j', 'k']
    for word in seg_list_complete:
        if ('n' in word.flag) or (word.flag in value_list):
            return True
    return False
