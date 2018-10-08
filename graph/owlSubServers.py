import urllib2
import json
import actkg.config as config
import logging


def relation_predict(question):
    url = config.server_RelationPredict_address
    url += "?q="+question
    try:
        result = json.loads(urllib2.urlopen(url, timeout=10).read())
    except Exception:
        result = None
        logging.error("Error: Sub server 20001 raise an error, please check")
    return result


def answer_selection(question, description):
    url = config.server_AnswerSelection_address
    url += "?q="+question+"&desc="+description
    try:
        result = json.loads(urllib2.urlopen(url, timeout=10).read())
    except Exception:
        result = None
        logging.error("Error: Sub server 20002 raise an error, please check")
    return result


def triple_extraction(content):
    url = config.server_TripleExtraction_address
    url += "?content="+content
    try:
        result = json.loads(urllib2.urlopen(url, timeout=10).read())
    except Exception:
        result = None
        logging.error("Error: Sub server 20004 raise an error, please check")
    return result


def count_qa(question):
    url = config.server_CountQA_address
    url += "?q="+question
    try:
        result = json.loads(urllib2.urlopen(url, timeout=10).read())
    except Exception:
        result = None
        logging.error("Error: Sub server 20005 raise an error, please check")
    return result


def test():
    url = "10.1.1.28:20006"
    try:
        result = json.loads(urllib2.urlopen(url, timeout=10).read())
    except Exception:
        result = None
        logging.error("Error: Sub server 20005 raise an error, please check")
    return result