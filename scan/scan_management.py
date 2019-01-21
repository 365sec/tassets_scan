# coding:utf-8

from django.shortcuts import render,HttpResponse
import json
import os
from .. import conf_list
conf_path = conf_list.conf_path
target_status_path = conf_list.target_status_path
client = conf_list.client
target_index = conf_list.target_index
target_type = conf_list.target_type

class Scan():

    def asset_scan(self,request):
        hits = []
        target_list = []
        scan_type = "1"
        try:
            res = client.search(index=target_index,
                                doc_type=target_type,
                                body={
                                    "size":1000,
                                    "_source":"name"
                                }
                                )
            print res["hits"]["total"]
            for hit_dict in res["hits"]["hits"]:
                source = hit_dict.get("_source",{})
                hit = {
                    "name":source.get("name",""),
                    "id":hit_dict["_id"]
                }
                hits.append(hit)
            f = open(conf_path,'rb')
            conf = f.read()
            f.close()
            content = os.popen('td01_status').read().rstrip()
            status_dict = json.loads(content)
            status = status_dict.get("status","FINISH")
            if status == "RUNING":
                fs = open(target_status_path,'rb')
                target_status = json.loads(fs.read())
                type = target_status.get("type","custom")
                if type == "target_template":
                    scan_type = "2"
                    id_list = target_status.get("id_list",[])
                    target_list = target_status.get("target_list",[])
                    for hit in hits:
                        if hit.get("id","") in id_list:
                            hits.remove(hit)
            success = "true"
        except:
            success = "false"
            conf = ""
            status_dict = {
                "status": "STOP"
            }
        return render(request,'scan/asset_scan.html',{
            "status":status_dict.get("status","FINISH"),
            "result":status_dict,
            "success":success,
            "conf":conf,
            "hits":hits,
            "target_list":target_list,
            "scan_type":scan_type
        })

    def get_scan_status(self,request):
        try:
            content = os.popen('td01_status').read().rstrip()
            status_dict = json.loads(content.replace("'","\""))
            status_dict["success"] = True
        except:
            status_dict = {
                "success":False
            }
        return HttpResponse(json.dumps(status_dict))

    def start_scan(self,request):
        if request.method == "POST":
            scan_type = request.POST.get("scan_type","1")
            fs = open(target_status_path,"w")
            conf = ""
            if scan_type == "1":
                conf = request.POST.get("conf","")
                status_dict = {
                    "type":"custom"
                }
                fs.write(json.dumps(status_dict,ensure_ascii=False))
                fs.close()
            elif scan_type == "2":
                id_list = request.POST.getlist("ids[]",[])
                res = client.search(
                    index=target_index,
                    doc_type=target_type,
                    body={
                        "size":1000,
                        "_source":["name","target"],
                        "query":{
                            "terms":{
                                "_id":id_list
                            }
                        }
                    }
                )
                target_list = []
                for hit in res["hits"]["hits"]:
                    source = hit["_source"]
                    hit_dict = {
                        "id":hit["_id"],
                        "name":source.get("name","")
                    }
                    target_list.append(hit_dict)
                    conf += source.get("target","")+"\n"
                status_dict = {
                    "type":"target_template",
                    "id_list":id_list,
                    "target_list":target_list
                }
                fs.write(json.dumps(status_dict,ensure_ascii=False))
                fs.close()
            f = open(conf_path,'wb')
            f.write(conf)
            f.close()
            try:
                content = os.popen('td01_start -i '+conf_path).read().rstrip()
                start_status_dict = json.loads(content)
            except:
                start_status_dict = {
                    "start_task":'ok'
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
                    status_dict = {
                        "msg":"获取状态失败"
                    }
                    content_dict = dict(content_dict,**status_dict)
                    content_dict["success"] = False
            else:
                content_dict["success"] = False
                content_dict["msg"] = "启动失败"
            return HttpResponse(json.dumps(content_dict))

    def stop_scan(self,request):
        if request.method == "POST":
            try:
                content = os.popen('td01_stop').read().rstrip()
                stop_status_dict = json.loads(content)
            except:
                stop_status_dict = {
                    "stop_task":'ok'
                }
            stop_task = stop_status_dict.get('stop_task','')
            if stop_task == "ok":
                try:
                    content = os.popen('td01_status').read().rstrip()
                    status_dict = json.loads(content)
                    status_dict["success"] = True
                except:
                    # content_dict["success"] = False
                    # content_dict["msg"] = "获取状态失败"
                    status_dict = {
                        "msg":"获取状态失败"
                    }
                    status_dict["success"] = False
            else:
                status_dict = {
                    "success":False,
                    "msg":"停止失败"
                }
            return HttpResponse(json.dumps(status_dict))















