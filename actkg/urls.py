"""actkg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.shortcuts import render
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
import graph.views
import robot.views
import nlp.views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="home.html")),
    url(r'^search/', TemplateView.as_view(template_name="search.html")),
    url(r'^schema/', TemplateView.as_view(template_name="schema.html")),
    url(r'^apis/', TemplateView.as_view(template_name="apis.html")),
    url(r'^display/', TemplateView.as_view(template_name="display.html")),
    url(r'^linking/', TemplateView.as_view(template_name="linking.html")),
    url(r'^extraction/', TemplateView.as_view(template_name="extraction.html")),
    url(r'^update/', TemplateView.as_view(template_name="update.html")),
    #url(r'^contributor/', TemplateView.as_view(template_name="contributor.html")),
    url(r'^demos/', TemplateView.as_view(template_name="demos.html")),
    url(r'^team/', TemplateView.as_view(template_name="team.html")),
    url(r'^publications/', TemplateView.as_view(template_name="publications.html")),
    url(r'^patents/', TemplateView.as_view(template_name="patents.html")),

    url(r'^api/graph/graph/', graph.views.graph),
    url(r'^api/graph/entity/', graph.views.entity),
    url(r'^api/graph/qa/', graph.views.qa),
    url(r'^api/graph/simple_qa/', graph.views.simple_qa),

    url(r'^api/schema/attribute/', graph.views.get_attributes),
    url(r'^api/schema/entity/', graph.views.get_category_entities),

    url(r'^api/nlp/parse/', nlp.views.parse),
    url(r'^api/nlp/linking/', nlp.views.linking),
    url(r'^api/nlp/extraction/', nlp.views.extraction),

    url(r'^api/robot/talk', robot.views.talk),
    url(r'^api/robot/wechat/', robot.views.wechat),

    url(r'^test/', graph.views.test),
]
