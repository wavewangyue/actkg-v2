# coding=utf-8
import urllib2
import json
import actkg.config as config

alias_keyid = config.alias_keyid


def execute(statement):
    url = config.database_address+"/db/data/transaction/commit"
    data = {"statements": [{"statement": statement}]}
    header = {"Accept": "application/json; charset=UTF-8",
              "Content-Type": "application/json",
              "Authorization": "Basic bmVvNGo6MTIzNDU2"}
    req = urllib2.Request(url, headers=header)
    data = json.dumps(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data).read()
    response = json.loads(response)
    if len(response["results"]) != 0:
        return response["results"][0]["data"]
    else:
        return []


def get_entity_info_by_id(neoid):
    statement = "match (n:Instance) where id(n) = " + str(neoid) + " return n"
    result = execute(statement)
    entity = {}
    if len(result) != 0:
        entity = result[0]["row"][0]
        entity['neoId'] = neoid
        entity['label'] = 'None' if 'label' not in entity else entity['label']
    return entity


def get_entity_info_by_keyid(keyid):
    statement = "match (n:Instance) where n.keyId = \"" + str(keyid) + "\" return id(n), n"
    result = execute(statement)
    entity = {}
    if len(result) != 0:
        entity = result[0]["row"][1]
        entity['neoId'] = result[0]["row"][0]
        entity['label'] = 'None' if 'label' not in entity else entity['label']
    return entity


def get_entity_list_by_name(name):
    entity_list = []
    # 先通过简称与别名检索
    if name in alias_keyid:
        statement = "match (n:Instance) where n.keyId =\"" + str(alias_keyid[name]) + "\" return id(n), n"
        result = execute(statement)
        if len(result) != 0:
            data = result[0]
            entity = data['row'][1]
            entity['neoId'] = data['row'][0]
            entity['label'] = 'None' if 'label' not in entity else entity['label']
            entity_list.append(entity)
    # 再通过全名检索
    statement = "match (n:Instance) where n.name =\"" + str(name) + "\" return id(n), n"
    result = execute(statement)
    for data in result:
        entity = data['row'][1]
        entity['neoId'] = data['row'][0]
        entity['label'] = 'None' if 'label' not in entity else entity['label']
        entity_list.append(entity)
    return entity_list


def get_related_entities_by_id(neoid):
    statement = "match (n:Instance)-[r]->(m:Instance) where id(n) =" + str(neoid) + " return type(r), m.label, m.name, id(m)"
    related_entities = []
    result = execute(statement)
    for data in result:
        related_entities.append({'name': data['row'][0], 'target_label': data['row'][1], 'target_name': data['row'][2], 'target_neoId': data['row'][3]})
    return related_entities


def get_entities_by_label(label):
    statement = "match (n:Instance) where n.label =\"" + str(label) + "\" return id(n), n limit 200"
    entities = []
    result = execute(statement)
    for data in result:
        entity = data['row'][1]
        entity['neoId'] = data['row'][0]
        entity['label'] = 'None' if 'label' not in entity else entity['label']
        entities.append(entity)
    return entities


def get_triples_by_relation(relation):
    statement = "match (n:Instance)-[r]->(m:Instance) where type(r) =\"" + str(relation) + "\" return id(n), n, type(r), id(m), m limit 50"
    triples = []
    result = execute(statement)
    for data in result:
        entity1 = data['row'][1]
        entity1['neoId'] = data['row'][0]
        entity1['label'] = 'None' if 'label' not in entity1 else entity1['label']
        r = data['row'][2]
        entity2 = data['row'][4]
        entity2['neoId'] = data['row'][3]
        entity2['label'] = 'None' if 'label' not in entity2 else entity2['label']
        triples.append([entity1, r, entity2])
    return triples


def get_path_between_entities(e1_id, e2_id):
    statement = "MATCH p=shortestPath((n:Instance)-[*..5]-(m:Instance)) where id(n)="+str(e1_id)+" and id(m)="+str(e2_id)+" RETURN p"
    result = execute(statement)
    if len(result) != 0:
        return result[0]['row'][0]
    return []


def get_relation_between_entities(e1_keyid, e2_keyid):
    statement = "MATCH (n:Instance)-[r]->(m:Instance) where n.keyId=\""+str(e1_keyid)+"\" and m.keyId=\""+str(e2_keyid)+"\" RETURN id(n), n, type(r), id(m), m"
    result = execute(statement)
    triple = []
    if len(result) != 0:
        e1 = result[0]['row'][1]
        e1['neoId'] = result[0]['row'][0]
        e1['label'] = 'None' if 'label' not in e1 else e1['label']
        e2 = result[0]['row'][4]
        e2['neoId'] = result[0]['row'][3]
        e2['label'] = 'None' if 'label' not in e2 else e2['label']
        triple = [e1, result[0]['row'][2], e2]
    else:
        statement = "MATCH (n:Instance)-[r]->(m:Instance) where n.keyId=\"" + str(e2_keyid) + "\" and m.keyId=\"" + str(e1_keyid) + "\" RETURN id(n), n, type(r), id(m), m"
        result = execute(statement)
        if len(result) != 0:
            e1 = result[0]['row'][1]
            e1['neoId'] = result[0]['row'][0]
            e1['label'] = 'None' if 'label' not in e1 else e1['label']
            e2 = result[0]['row'][4]
            e2['neoId'] = result[0]['row'][3]
            e2['label'] = 'None' if 'label' not in e2 else e2['label']
            triple = [e1, result[0]['row'][2], e2]
    return triple
