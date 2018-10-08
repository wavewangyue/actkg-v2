import urllib2
import urllib
import json


def get_image(entity):

    subscription_key = "ae636eeb43bb460e92434fa6089b52aa"

    entity = urllib.quote(str(entity))
    url = "https://api.cognitive.microsoft.com/bing/v5.0/images/search?"
    url += "q="+entity+"&count=1"
    header = {"Ocp-Apim-Subscription-Key": subscription_key}
    req = urllib2.Request(url, headers=header)
    result = urllib2.urlopen(req).read()
    result = json.loads(result)
    return result['value'][0]['thumbnailUrl']
