# -*- coding:utf-8 -*-

from django.shortcuts import render,HttpResponse
from .. import conf_list,query_dsl
import json
import uuid
import time
import datetime

client = conf_list.client
province_dict_1 = conf_list.province_dict_1
chart_index = "chart"
chart_type = "chart"
__query__ = query_dsl.Query()
field_dict= {
    "port":"ports",
    "protocol":"protocols.keyword",
    "os":"os.keyword",
    "component":"components.keyword"
}
format_dict = {
    "1d":"yyyy-MM-dd",
    "1h":"yyyy-MM-dd HH"
}

#获取聚合的dsl语句
def get_query(resource_type,data_type,category,query_dict,map_type,interval):
    if category in ["short_pie","short_column","short_china_map"]:
        #地图的查询需要额外处理。
        if resource_type in ["assets","threats"]:
            if data_type == "number":
                if category == "short_china_map":
                    if map_type == "china":
                        field = "province.keyword" if resource_type == "assets" else "location.province.keyword"
                        query = {
                            "size":0,
                            "query":query_dict,
                            "aggs":{
                                "count":{
                                    "terms":{
                                        "field":field,
                                        "size":50
                                    }
                                }
                            }
                        }
                    else:
                        #这里的城市过滤待转换
                        field = "city.keyword" if resource_type == "assets" else "location.city.keyword"
                        province = province_dict_1.get(map_type,map_type)
                        province_field = "province.keyword" if resource_type == "assets" else "location.province.keyword"
                        query = {
                            "size":0,
                            "query":{
                                "bool":{
                                    "must":[
                                        map_type,
                                        {
                                            "term":{
                                                province_field:province
                                            }
                                        }
                                    ]
                                }
                            },
                            "aggs":{
                                "count":{
                                    "terms":{
                                        "field":field,
                                        "size":50
                                    }
                                }
                            }
                        }
                else:
                    query = {
                        "size":0,
                        "query":query_dict
                    }
                return query
            else:
                if resource_type == "threats":
                    term_field = "location.province.keyword" if data_type == "province" else "location.city.keyword"
                else:
                    term_field = "province.keyword" if data_type == "province" else "city.keyword"
                size = 100
        elif resource_type in ["port","protocol","os","component"]:
            term_field = field_dict[resource_type]
            size = 20
        else:
            return None
        query = {
            "size":0,
            "query":query_dict,
            "aggs":{
                "count":{
                    "terms":{
                        "field":term_field,
                        "size":size,
                        "shard_size":size
                    }
                }
            }
        }
        return query
    elif category == "short_curve":
        #时间线的图表统计语句DSL使用date_histogram方法
        if resource_type in ["assets","threats"]:
            if data_type == "number":
                time_format = format_dict.get(interval,"yyyy-MM-dd")
                time_field = "datetime" if resource_type == "assets" else "timestamp"
                query = {
                    "size":0,
                    "query":query_dict,
                    "aggs":{
                        "count":{
                            "date_histogram": {
                                "field": time_field,
                                "interval": interval,
                                "format": time_format
                            }
                        }
                    }
                }
                return query
            else:
                print "时间线参数错误，分析维度只能为数量分布"
                return None
        else:
            print "时间线参数错误，图表类型只能为资产分析或漏洞分析"
            return None
    else:
        print "错误的参数，图标类型不正确"
        return None


def get_interval(time_select,start_time,end_time):
    if time_select in ["recent_12h","recent_3d"]:
        interval = "1h"
    elif time_select in ["recent_7d","recent_1month","all_time"]:
        interval = "1d"
    elif time_select == "custom":
        if start_time == "":
            interval = "1d"
        else:
            start_time = datetime.datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(end_time,"%Y-%m-%d %H:%M:%S") if end_time != "" else datetime.datetime.now()
            time1 = start_time + datetime.timedelta(days=3)
            if time1 > end_time:
                interval = "1h"
            else:
                interval = "1d"
    else:
        interval = "1d"
    return interval


def add_chart(request):
    if request.method == "POST":
        try:
            title = request.POST.get("title","")
            category = request.POST.get("category","")
            data_type = request.POST.get("data_type","")
            resource_type = request.POST.get("resource_type","")
            time_select = request.POST.get("time_select","")
            sjgz = request.POST.get("sjgz","")
            map_type = request.POST.get("map_type","china")
            start_time = request.POST.get("start_time","")
            end_time = request.POST.get("end_time","")
            query_dict = __query__.get_query(sjgz)
            if resource_type == "threats":
                time_field = "timestamp"
            else:
                time_field = "datetime"
            query_dict = __query__.get_query_with_time(query_dict,time_field,time_select,start_time,end_time)
            interval = get_interval(time_select,start_time,end_time)
            query = get_query(resource_type,data_type,category,query_dict,map_type,interval)
            if query:
                source = {
                    "title":title,
                    "category":category,
                    "data_type":data_type,
                    "resource_type":resource_type,
                    "time_select":time_select,
                    "start_time":start_time,
                    "end_time":end_time,
                    "map_type":map_type,
                    "query":json.dumps(query,ensure_ascii=False)
                }
                id = str(uuid.uuid4())
                client.index(index=chart_index,
                             doc_type=chart_type,
                             id=id,
                             body=source
                             )
                content = {
                    "success":True,
                    "id":id,
                    "title":title
                }
                time.sleep(1)
            else:
                content = {
                    "success":False,
                    "msg":"该模块待完成"
                }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"程序执行出错，请检查控制台输出"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))


def chart_delete(request):
    if request.method == "GET":
        try:
            id = request.GET.get("id","")
            client.delete(index=chart_index,
                          doc_type=chart_type,
                          id=id
                          )
            content = {
                "success":True
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"删除操作失败！"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))

