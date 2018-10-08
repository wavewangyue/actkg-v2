import serviceTalkbot
import serviceWechat
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


def talk(request):
    question = request.GET.get('q', None)
    neoid = request.GET.get('id', None)
    autopick = request.GET.get('autopick', "false").lower()
    if autopick == "true":
        autopick = True
    else:
        autopick = False
    response = HttpResponse(json.dumps(serviceTalkbot.talk(question, neoid=neoid, autopick=autopick)))
    response["Access-Control-Allow-Origin"] = "*"
    return response

@csrf_exempt
def wechat(request):
    if request.method == 'GET':
        return HttpResponse(serviceWechat.config(request))
    if request.method == 'POST':
        return HttpResponse(serviceWechat.talk(request))
