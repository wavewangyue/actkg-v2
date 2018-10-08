# coding=UTF-8
import jieba
import jieba.posseg as posseg
import graph.serviceKG as serviceKG
import logging


def parse(content, level):
    result = {}
    # 分词
    if level == 1:
        seg = list(jieba.cut(content))
        result['seg'] = seg
        #logging.info('nlp parse seg:' + '/'.join(seg))
    # 词性标注
    if level >= 2:
        seg = []
        pos = []
        words = posseg.cut(content)
        for w in words:
            seg.append(w.word)
            pos.append(w.flag)
        result['seg'] = seg
        result['pos'] = pos
        #logging.info('nlp parse seg:' + '/'.join(seg))
        #logging.info('nlp parse pos:' + '/'.join(pos))
    # 实体识别
    if level >= 3:
        ner = []
        for flag in result['pos']:
            if (flag == 'j') or ((flag[0] == 'n')and(len(flag)>1)):
                ner.append('B')
            else:
                ner.append('O')
        result['ner'] = ner
        #logging.info('nlp parse ner:' + '/'.join(ner))
    # 实体链接
    if level >= 4:
        nel = []
        for i in range(len(result['seg'])):
            if result['ner'][i] == 'B':
                ent_info = serviceKG.entity_search(name=result['seg'][i], autopick=True)
                if len(ent_info) > 0:
                    nel.append(str(ent_info['neoId']))
                else:
                    nel.append("")
            else:
                nel.append("")
        result['nel'] = nel
        #logging.info('nlp parse nel:' + '/'.join(nel))
    return result
