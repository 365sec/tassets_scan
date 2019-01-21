# coding:utf-8

from django.shortcuts import render,HttpResponse
import json
import os
from .. import conf_list
conf_path = conf_list.conf_path

class Scan():

    def asset_scan(self,request):
        try:
            f = open(conf_path,'rb')
            conf = f.read()
            content = os.popen('td01_status').read().rstrip()
            status_dict = json.loads(content)
            success = "true"
        except Exception as e:
            print str(e)
            conf = ""
            success = "false"
            status_dict = {
            }
        return render(request,'scan/scan.html',{
            "status":status_dict.get("status",""),
            "result":status_dict,
            "success":success,
            "conf":conf
        })

    def get_scan_status(self,request):
        try:
            content = os.popen('td01_status').read().rstrip()
            status_dict = json.loads(content.replace("'","\""))
            print content
        except:
            status_dict = {
                "status": "STOP",
                "start_time": "2018-09-13 11:06:26",
                "elapsedtime": "0:1:34",
                "end_time": "2018-09-13 11:08:00",
                "scanip": "comptuing",
                "td01_status": "2018-09-13 09:48:34",
                "loginfo": "",
                "scandomain": "comptuing"
            }
        return HttpResponse(json.dumps(status_dict))

    def start_scan(self,request):
        if request.method == "POST":
            conf = request.POST.get("conf","")
            f = open(conf_path,'wb')
            f.write(conf)
            f.close()
            try:
                content = os.popen('td01_start -i '+conf_path).read().rstrip()
                start_status_dict = json.loads(content.replace("'","\""))
            except Exception as e:
                print str(e)
                start_status_dict = {
                    "start_task":"no"
                }
            start_task = start_status_dict.get('start_task','')
            content_dict = {
                "start_task":start_task
            }
            if start_task == "ok":
                try:
                    content = os.popen('td01_status').read().rstrip()
                    status_dict = json.loads(content)
                    content_dict = dict(content_dict,**status_dict)
                    content_dict["success"] = True
                except:
                    content_dict["success"] = False
                    content_dict["msg"] = "获取状态失败"
                    # status_dict = {
                    #     "status": "RUNNING",
                    #     "start_time": "2018-09-13 11:06:26",
                    #     "elapsedtime": "0:1:34",
                    #     "end_time": "2018-09-13 11:08:00",
                    #     "scanip": "comptuing",
                    #     "td01_status": "2018-09-13 09:48:34",
                    #     "loginfo": "test",
                    #     "scandomain": "comptuing"
                    # }
                    # content_dict = dict(content_dict,**status_dict)
                    # content_dict["success"] = True
            else:
                content_dict["success"] = False
                content_dict["msg"] = "启动失败"
            return HttpResponse(json.dumps(content_dict))

    def stop_scan(self,request):
        if request.method == "POST":
            try:
                content = os.popen('td01_stop').read().rstrip()
                print content
                stop_status_dict = json.loads(content.replace("'","\""))
            except Exception as e:
                print str(e)
                stop_status_dict = {
                    "stop_task":"no"
                }
            stop_task = stop_status_dict.get('stop_task','')
            if stop_task == "ok":
                try:
                    content = os.popen('td01_status').read().rstrip()
                    status_dict = json.loads(content)
                    status_dict["success"] = True
                except:
                    status_dict["success"] = False
                    status_dict["msg"] = "获取状态失败"
                    # status_dict = {
                    #     "status": "STOP",
                    #     "start_time": "2018-09-13 11:06:26",
                    #     "elapsedtime": "0:1:34",
                    #     "end_time": "2018-09-13 11:08:00",
                    #     "scanip": "comptuing",
                    #     "td01_status": "2018-09-13 09:48:34",
                    #     "loginfo": "test",
                    #     "scandomain": "comptuing"
                    # }
                    # status_dict["success"] = True
            else:
                status_dict = {
                    "success":False,
                    "msg":"停止失败"
                }
            return HttpResponse(json.dumps(status_dict))















