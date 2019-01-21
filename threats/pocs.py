# coding:utf-8

from django.shortcuts import render,HttpResponse
from .. import conf_list
from pymongo import MongoClient
import os
import json

poc_page_num = conf_list.poc_page_num
mongo_host = conf_list.mongo_host
mongo_port = conf_list.mongo_port
mongo_db = conf_list.mongo_db
mongo_collection = conf_list.mongo_collection
mongo_client = MongoClient(mongo_host,mongo_port)
db = mongo_client[mongo_db]

status_dict = {
    "0":"扫描成功",
    "1":"正在扫描"
}
sort_dict = {
    "asc":1,
    "desc":-1
}


def pocs(request):
    collection = db[mongo_collection]
    keyword = request.GET.get("keyword","")
    page = int(request.GET.get("page",1))
    sort_content = request.GET.get("sort","threat_num:desc")
    offset = (page-1)*poc_page_num
    query = {
        "name":{
            '$regex':keyword,
            '$options':'i'
        }
    }
    sort_way = "asc"
    sort_field = ""
    if sort_content == "":
        result = collection.find(query).limit(poc_page_num).skip(offset)
    else:
        sort_list = sort_content.split(":")
        sort_field = sort_list[0]
        sort_way = sort_list[1]
        result = collection.find(query,).sort(sort_field,sort_dict.get(sort_way,1)).limit(poc_page_num).skip(offset)
    total = collection.count(query)
    page_nums = int(total / poc_page_num) + 1 if (total % poc_page_num) > 0 else int(total / poc_page_num)
    page_list = [
        i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
    ]
    hits = []
    for hit in result:
        last_scantime = hit.get("last_scantime","")
        last_status = 0
        if last_scantime != "":
            last_status = 1
        threat_num = int(hit.get("threat_num",0))
        scan_enable_status = 1
        if threat_num == 0 :
            scan_enable_status = 0
        hit_dict = {
            "id":hit["_id"],
            "name":hit.get("name",""),
            "risk":hit.get("risk",""),
            "update":hit.get("updateDate",""),
            "threat_num":hit.get("threat_num",0),
            "esquery":hit.get("esquery",""),
            "infection_num":hit.get("infection_num",0),
            "status":hit.get("status",""),
            "task_state_info":status_dict.get(str(hit.get("status",0)),""),
            "last_status":last_status,
            "last_scantime":hit.get("last_scantime",""),
            "last_scan_use":hit.get("last_scan_use",""),
            "scan_enable_status":scan_enable_status
        }
        hits.append(hit_dict)
    return render(request,"threats/pocs.html",{
        "total":total,
        "hits":hits,
        "keyword":keyword,
        "sort_field":sort_field,
        "sort_way":sort_way,
        "page":page,
        "sort_content":sort_content,
        "current_page":page,
        "last_page":page-1,
        "next_page":page+1,
        "page_nums":page_nums,
        "page_list":page_list
    })



def scan_start(request):
    if request.method == "POST":
        type = request.POST.get("type","")
        try:
            if type != "all":
                id = request.POST.get("id","")
                if id == "":
                    id_list = request.POST.getlist("id[]",[])
                    id_str = ",".join(id_list)
                else:
                    id_str = id
                cmd = "td01_scanpoc  -p%s" % id_str
            else:
                cmd = "td01_scanpoc"
            content = os.popen(cmd).read().rstrip()
            print content
            status_dict = json.loads(content)
            status = status_dict.get("td01_scanpoc","")
            if status == "ok":
                return_content = {
                    "success":True
                }
            else:
                return_content = {
                    "success":False,
                    "msg":status
                }
        except Exception,e:
            print str(e)
            return_content = {
                "success":False,
                "msg":"开启扫描失败"
            }
        return HttpResponse(json.dumps(return_content,ensure_ascii=False))


def pocs_scan_status(request):
    collection = db[mongo_collection]
    if request.method == "POST":
        try:
            id_list = request.POST.getlist("ids[]",[])
            new_id_list = [int(id) for id in id_list]
            query = {
                "_id":{
                    "$in":new_id_list
                }
            }
            res = collection.find(query)
            list_dict = {}
            for hit in res:
                id = hit["_id"]
                last_scantime = hit.get("last_scantime","")
                if last_scantime != "":
                    last_scan_info = last_scantime+"("+hit.get("last_scan_use","")+")"
                else:
                    last_scan_info = ""
                hit_dict = {
                    "id":id,
                    "task_state":hit.get("status",0),
                    "threat_num":hit.get("threat_num",0),
                    "infection_num":hit.get("infection_num",0),
                    "task_percent":hit.get("task_percent",0),
                    "last_scan_info":last_scan_info,
                    "task_state_info":status_dict.get(str(hit.get("status",0)),"")
                }
                list_dict[str(id)] = hit_dict
            content = {
                "success":True,
                "list":list_dict
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"获取扫描状态失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))








