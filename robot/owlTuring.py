import urllib
import urllib2
import json


def api(question):

    url = "http://www.tuling123.com/openapi/api"
    data = {'key': 'f02da40881a24da2af7c1cad3e9f523e', 'info': question, 'userid': '0'}
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data).read()
    response = json.loads(response)
    return {'answer': response['text'], 'type': 'tk'}
