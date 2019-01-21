#coding:utf-8

from django.shortcuts import render,HttpResponse
from .. import conf_list,query_dsl
from django import http
import datetime
import json
import time
import os

__query__ = query_dsl.Query()

client = conf_list.client
target_index = conf_list.target_index
target_type = conf_list.target_type
update_path = conf_list.update_path
status_path = conf_list.status_path

def update(request):
    if request.method == "GET":
        version = ""
        try:
            f = open(status_path,'r')
            content = json.loads(f.read())
            f.close()
            upgrade_url = content.get("upgrade_url","")
            version = content.get("version","")
        except Exception,e:
            print str(e)
            upgrade_url = ""
        return render(request,"scan/update.html",{
            "upgrade_url":upgrade_url,
            "version":version
        })
    elif request.method == "POST":
        try:
            obj = request.FILES.get("file")
            filename = update_path + obj.name
            f = open(filename,"wb")
            for chunk in obj.chunks():
                f.write(chunk)
            f.close()
            content = {
                "success":True
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"上传失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))


def upgrade(request):
    if request.method == "GET":
        return render(request,"scan/upgrade.html",{})

def get_upgrade_status(request):
    if request.method == "POST":
        pass

def modify_upgrade_url(request):
    if request.method == "POST":
        url = request.POST.get("url","")
        try:
            f = open(status_path,'r')
            status = json.loads(f.read())
            f.close()
            status["upgrade_url"] = url
            fw = open(status_path,'wb')
            fw.write(json.dumps(status,ensure_ascii=False))
            fw.close()
            content = {
                "success":True
            }
        except Exception,e:
            print str(e)
            content = {
                "success": False,
                "msg": "url保存失败！"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))