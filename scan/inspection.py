# coding:utf-8

from django.shortcuts import render,HttpResponse
import json
import os


def one_click_inspection(request):
    try:
        content = os.popen('td01_inspection').read().rstrip()
        status_dict = json.loads(content.replace("'","\""))
        status_dict["ttag"] = status_dict.get("ttag","")
        status_dict["masscan"] = status_dict.get("masscan","")
        status_dict["tscantarget"] = status_dict.get("tscantarget","")
        status_dict["tgrab"] = status_dict.get("tgrab","")
        status_dict["td01_loader"] = status_dict.get("td01_loader","")
        status_dict["redis_server"] = status_dict.get("redis-server","")
        status_dict["td01_outgoing"] = status_dict.get("td01_outgoing","")
        status_dict["td01_merge"] = status_dict.get("td01_merge","")
        status = 'true'
    except Exception as e:
        print str(e)
        status = 'false'
        status_dict={}
    return render(request,'scan/one-click_inspection.html',{
        "status":status,
        "result":status_dict
    })