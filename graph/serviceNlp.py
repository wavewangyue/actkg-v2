# coding=utf-8
import jieba.posseg as posseg
import jieba
import owlNeo4j
import modelWord2vec
import sys

reload(sys)
sys.setdefaultencoding('utf8')


# 分词
def segment(statement):
    fliter_list = ['的']
    seg_list_unflit = list(posseg.cut(statement))
    seg_list_flit = []
    for word in seg_list_unflit:
        if word.word not in fliter_list:
            seg_list_flit.append(word)
    return seg_list_flit


# 命名实体识别
def ner(seg_list_complete):
    entity = None
    for word in seg_list_complete:
        content = word.word
        flag = word.flag
        if flag.find("n") >= 0:
            entity = content
            break
    return entity


# 问题的求索过程
def lightment(graph_result, seg_list_origin):

    Threshold_bt = 0.15

    stand_now = 0
    seg_list = []
    for seg_word in seg_list_origin:
        seg_list.append(seg_word)
    # 渐进探索后续实体
    while len(seg_list) > 0:
        # 整理当前实体的关系与属性集
        matcher_list = []
        # 整理关系集
        for link in graph_result['links']:
            if link['source'] == stand_now:
                matcher = {'name': link['name'], 'target': link['target'], 'isLink': True}
                matcher_list.append(matcher)
        # 整理属性集
        entity_info = owlNeo4j.get_entity_info(graph_result['nodes'][stand_now]['keyId'])
        entity_info = entity_info
        for key in entity_info.keys():
            if any(key == matcher_pick['name'] for matcher_pick in matcher_list):
                continue
            matcher = {'name': key, 'target': entity_info[key], 'isLink': False}
            matcher_list.append(matcher)
        # 逐个计算集合元素与问题的匹配度
        similarity_most = {'matcher': {}, 'point': 0, 'hop': -1}
        for matcher_pick in matcher_list:
            point, hop = modelWord2vec.get_similarity(seg_list, list(jieba.cut(matcher_pick['name'])))
            if point > similarity_most['point']:
                similarity_most['point'] = point
                similarity_most['hop'] = hop
                similarity_most['matcher'] = matcher_pick
        if similarity_most['point'] > Threshold_bt:
            # 如果匹配到关系，继续渐进
            if similarity_most['matcher']['isLink']:
                new_answerlist = [graph_result['nodes'][stand_now]['name'],
                                  similarity_most['matcher']['name'],
                                  graph_result['nodes'][similarity_most['matcher']['target']]['name']]
                stand_now = similarity_most['matcher']['target']
                graph_result['answerpath'].append(stand_now)
                graph_result['answerlist'].append(new_answerlist)
                if similarity_most['hop']+1 < len(seg_list):
                    seg_list = seg_list[similarity_most['hop']+1:]
                    continue
                else:
                    break
            # 如果匹配到属性，则中止
            else:
                new_answerlist = [graph_result['nodes'][stand_now]['name'],
                                  similarity_most['matcher']['name'],
                                  similarity_most['matcher']['target']]
                graph_result['answerlist'].append(new_answerlist)
                break
        else:
            break
    # 计算这个图谱对于这个问题的得分
    point = 0
    answer_match_list = []
    for answer in graph_result['answerlist']:
        answer_match_list.append(answer[1])
    if len(answer_match_list) > 0:
        point, hop = modelWord2vec.get_similarity(seg_list_origin, answer_match_list)
    return graph_result, point


# 答案句子加工
def answerment(graph_result):
    if len(graph_result['answerlist']) == 0:
        statement = "为你找到关于 "+graph_result['nodes'][0]['name']+" 的信息"
    else:
        statement = ""
        for i, answer_item in enumerate(graph_result['answerlist']):
            statement += answer_item[0]+"的"+answer_item[1]+"是"+answer_item[2]
            if i+1 < len(graph_result['answerlist']):
                statement += "，"
    graph_result['answer'] = statement
    return graph_result
