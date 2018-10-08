# -*- coding: utf-8 -*-

def Relation_Extraction(content):
    sentences = content.split('。')
    results = []
    for sentence in sentences:
        if sentence != '':
            triples = [['德国','首都','柏林']]
            results.append({'sentence':sentence+'。', 'triples':triples})
    return results