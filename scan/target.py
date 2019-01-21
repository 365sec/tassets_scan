#coding:utf-8

from django.shortcuts import render,HttpResponse
from .. import conf_list,query_dsl
from django import http
import datetime
import json
import time

__query__ = query_dsl.Query()

client = conf_list.client
target_index = conf_list.target_index
target_type = conf_list.target_type

def management(request):
    if request.method == "GET":
        keyword = request.GET.get("keyword","")
        query = __query__.get_query(keyword)
        page = int(request.GET.get("page",1))
        from_num = (page-1)*15
        res = client.search(index=target_index,
                            doc_type=target_type,
                            body={
                                "from":from_num,
                                "size":15,
                                "query":query
                            }
                            )
        hits =[]
        total = res["hits"]["total"]
        page_nums = int(total / 15) + 1 if (total % 15) > 0 else int(total / 15)
        page_list = [
            i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
        ]
        for hit in res["hits"]["hits"]:
            id = hit["_id"]
            source = hit["_source"]
            hit_dict = {
                "name":source.get("name",""),
                "description":source.get("description",""),
                "timestamp":source.get("timestamp",""),
                "id":id
            }
            hits.append(hit_dict)
        return render(request,"scan/target_management.html",{
            "total":total,
            "hits":hits,
            "page_nums":page_nums,
            "current_page":page,
            "last_page":page-1,
            "next_page":page+1,
            "page_list":page_list,
            "keyword":keyword
        })


def new(request):
    if request.method == "GET":
        return render(request,"scan/target/new.html",{})
    elif request.method == "POST":
        name = request.POST.get("name","")
        description = request.POST.get("description","")
        target = request.POST.get("target","")
        try:
            action = {
                "name":name,
                "target":target,
                "description":description,
                "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.index(index=target_index,
                                  doc_type=target_type,
                                  body=action
                                  )
            time.sleep(1)
            content = {
                "success":True
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"配置入库失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))


def edit(request):
    if request.method == "GET":
        id = request.GET.get("id","")
        try:
            res = client.get(index=target_index,doc_type=target_type,id=id)
            source = res.get("_source",{})
            return render(request,"scan/target/edit.html",{
                "id":id,
                "name": source.get("name",""),
                "description":source.get("description",""),
                "target":source.get("target","")
            })
        except Exception,e:
            print str(e)
    elif request.method == "POST":
        name = request.POST.get("name","")
        description = request.POST.get("description","")
        target = request.POST.get("target","")
        id = request.POST.get("id","")
        try:
            action = {
                "name":name,
                "target":target,
                "description":description,
                "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.update(index=target_index,
                         doc_type=target_type,
                         id=id,
                         body={
                             "doc":action
                         }
                         )
            time.sleep(1)
            content = {
                "success":True
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"配置入库失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))

def delete(request):
    if request.method == "POST":
        type = request.POST.get("type","")
        id_list = request.POST.getlist("id[]",[])
        if type == "all":
            try:
                client.delete_by_query(
                    index=target_index,
                    doc_type=target_type,
                    body={
                        "query":{
                            "match_all":{}
                        }
                    }
                )
                time.sleep(1)
                content = {
                    "success":True
                }
            except Exception,e:
                print str(e)
                content = {
                    "success":False,
                    "msg":"删除失败！"
                }
        else:
            if id_list == []:
                content = {
                    "success":False,
                    "msg":"请检查参数是否设正确！"
                }
            else:
                try:
                    client.delete_by_query(
                        index=target_index,
                        doc_type=target_type,
                        body={
                            "query":{
                                "terms":{
                                    "_id":id_list
                                }
                            }
                        }
                    )
                    time.sleep(1)
                    content = {
                        "success":True
                    }
                except Exception,e:
                    print str(e)
                    content = {
                        "success":False,
                        "msg":"删除失败！"
                    }
        return HttpResponse(json.dumps(content,ensure_ascii=False))
    else:
        try:
            id = request.GET.get("id","")
            client.delete(index=target_index,doc_type=target_type,id=id)
            time.sleep(1)
        except Exception,e:
            print str(e)
            return HttpResponse("删除数据失败")
        return http.HttpResponseRedirect("../target_management")
