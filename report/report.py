# -*- coding:utf-8 -*-

from django.shortcuts import render,HttpResponse,HttpResponseRedirect
from django import http
from .. import conf_list,query_dsl
import json
import datetime
import time
import re
# from reportlab.pdfgen import canvas

client = conf_list.client
chart_index = "chart"
chart_type = "chart"
report_index = "report"
report_type = "report"
report_list_index = "report_list"
report_list_type = "report"
ipv4_index = conf_list.ipv4_index
ipv4_type = conf_list.ipv4_type
asset_index = conf_list.asset_index
asset_type = conf_list.asset_type
vuln_index = conf_list.vuln_index
vuln_type = conf_list.vuln_type
province_dict = conf_list.province_dict
province_pinyin_dict = conf_list.province_pinyin_dict
pool = "1"
__query__ = query_dsl.Query()


def report(request):
    if request.method == "GET":
        hits = []
        total = 0
        try:
            res = client.search(index=report_index,
                                doc_type=report_type,
                                body={
                                    "size":100
                                }
                                )
            i = 1
            total = res["hits"]["total"]
            for hit in res["hits"]["hits"]:
                source = hit.get("_source",{})
                data_res = client.search(index=report_list_index,
                                         doc_type=report_list_type,
                                         body={
                                             "size":100,
                                             "query":{
                                                 "term":{
                                                     "report_id.keyword":hit["_id"]
                                                 }
                                             },
                                             "sort":{
                                                 "datetime":{
                                                     "order":"desc"
                                                 }
                                             }
                                         }
                                         )
                report_list = []
                for data_hit in data_res["hits"]["hits"]:
                    data_source = data_hit["_source"]
                    report_dict = {
                        "id":data_hit["_id"],
                        "name":data_source.get("name",""),
                        "datetime":data_source.get("datetime","")
                    }
                    report_list.append(report_dict)
                print source.get("title","")
                hit_dict = {
                    "num":i,
                    "id":hit["_id"],
                    "title":source.get("title",""),
                    "category":source.get("category",""),
                    "datetime":source.get("datetime",""),
                    "report_list":report_list
                }
                i += 1
                hits.append(hit_dict)
        except Exception,e:
            print str(e)
        return render(request,'report/report.html',{
            "total":total,
            "hits":hits
        })
        sql = "SELECT ID,category,TITLE,DATETIME FROM REPORT"
        count_sql = "SELECT count(*) FROM REPORT"
        count_result = __query__.run_sql(pool,count_sql,"result")
        total=count_result[0][0]
        result = __query__.run_sql(pool,sql,"result")
        hits = []
        i = 1
        for row in result:
            report_sql = "SELECT ID,DATETIME FROM REPORT_LIST WHERE REPORT_ID = '%d'" % row[0]
            report_result = __query__.run_sql(pool,report_sql,"result")
            report_list = []
            for row1 in report_result:
                report_dict = {
                    "id":row1[0],
                    "datetime":row1[1].strftime("%Y-%m-%d %H:%M:%S"),
                    "name":row[2]+" "+row1[1].strftime("%Y-%m-%d")
                }
                report_list.append(report_dict)
            hit = {
                "num":i,
                "id":row[0],
                "category":row[1],
                "title":row[2],
                "datetime":row[3].strftime("%Y-%m-%d %H:%M:%S"),
                "report_list":report_list
            }
            i += 1
            hits.append(hit)
        return render(request,'report/report.html',{
            "total":total,
            "hits":hits
        })
    elif request.method == "POST":
        try:
            chart_id_list = request.POST.getlist("report[chart_ids][]",[])
            category = request.POST.get("category","")
            title = request.POST.get("title","")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if title =="":
                content = {
                    "success":False,
                    "msg":"标题不能为空"
                }
            else:
                if category == "custom_report":
                    id_list = []
                    for chart_id in chart_id_list:
                        id_list.append(chart_id)
                    id_list = sorted(id_list)
                    source = {
                        "title":title,
                        "category":category,
                        "datetime":timestamp,
                        "id_list":id_list
                    }
                    client.index(index=report_index,
                                 doc_type=report_type,
                                 body=source
                                 )
                    time.sleep(1)
                    return HttpResponseRedirect("../report")
                elif category == "scan_report":
                    time_select = request.POST.get("time_select")
                    start_time = request.POST.get("start_time","")
                    end_time = request.POST.get("end_time","")
                    rule = request.POST.get("rule","")
                    query_dict = __query__.get_query(rule)
                    time_field = "timestamp"
                    query_dict = __query__.get_query_with_time(query_dict,time_field,time_select,start_time,end_time)
                    query = {
                        "size":1000,
                        "_source":["location","ip","port","protocol"],
                        "query":query_dict,
                        "sort":{
                            "ip.keyword":{
                                "order":"desc"
                            }
                        },
                        "aggs":{
                            "ip_num":{
                                "cardinality":{
                                    "field":"ip.keyword"
                                }
                            },
                            "port_num":{
                                "cardinality":{
                                    "field":"port"
                                }
                            },
                            "os":{
                                "nested":{
                                  "path":"components"
                                },
                                "aggs":{
                                    "num":{
                                        "terms":{
                                            "field":"components.os.keyword",
                                            "size":100
                                        }
                                    }
                                }
                            },
                            "location":{
                                "terms":{
                                    "field":"location.province.keyword",
                                    "size":1000,
                                    "shard_size":1000
                                },
                                "aggs":{
                                    "ip_num":{
                                        "cardinality":{
                                            "field":"ip.keyword"
                                        }
                                    },
                                    "port_num":{
                                        "cardinality":{
                                            "field":"port"
                                        }
                                    }
                                }
                            }
                        }
                    }
                    source = {
                        "title": title,
                        "category":category,
                        "datetime":timestamp,
                        "rule":rule,
                        "time_select":time_select,
                        "start_time":start_time,
                        "end_time":end_time,
                        "query":json.dumps(query,ensure_ascii=False)
                    }
                    client.index(index=report_index,
                                 doc_type=report_type,
                                 body=source
                                 )
                    time.sleep(1)
                    return HttpResponseRedirect("../report")
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"操作执行失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))


def delete(request):
    if request.method == "GET":
        id = request.GET.get("id","")
        try:
            #删除报告
            client.delete_by_query(index=report_list_index,
                                   doc_type=report_list_type,
                                   body={
                                       "query":{
                                           "term":{
                                               "report_id.keyword":id
                                           }
                                       }
                                   }
                                   )
            #删除报告模板
            client.delete(index=report_index,
                          doc_type=report_type,
                          id=id
                          )
            time.sleep(1)
            return HttpResponseRedirect("../report")
        except Exception,e:
            print str(e)
            return HttpResponse("删除失败！")
    else:
        return HttpResponse("zzz")

def get_chart_data(source):
    category = source.get("category","")
    query = json.loads(source.get("query","{}"))
    resource_type = source.get("resource_type","")
    data_type = source.get("data_type","")
    if resource_type == "threats":
        index = vuln_index
        index_type = vuln_type
    else:
        index = asset_index
        index_type = asset_type
    aggs = client.search(index = index,
                         doc_type = index_type,
                         body = query
                         )
    name_list = []
    data_list = []
    value_list = []
    if category in ["short_pie","short_column","short_china_map"]:
        if category != "short_china_map" and resource_type in ["threats","assets"] and data_type == "number" :
            name = "资产" if resource_type == "assets" else "漏洞"
            value = aggs["hits"]["total"]
            name_list.append(name)
            data_dict = {
                "name":name,
                "value":value
            }
            data_list.append(data_dict)
        else:
            for bucket in aggs["aggregations"]["count"]["buckets"]:
                name = bucket.get("key","")
                if category == "short_china_map":
                    #名称符合中文的保留
                    reg = re.match(u"[\u4E00-\u9FA5]+",name)
                    if reg:
                        pass
                    else:
                        continue
                    if source.get("map_type") == "china":
                        name = province_dict.get(name,name)
                    else:
                        if "市".decode("utf8") in name:
                            pass
                        else:
                            name += "市".decode("utf-8")
                if name == "":
                    continue
                else:
                    name_list.append(str(name))
                    value = bucket.get("doc_count",0)
                    data_dict = {
                        "name":str(name),
                        "value":value
                    }
                    data_list.append(data_dict)
    elif category == "short_curve":
        for bucket in aggs["aggregations"]["count"]["buckets"]:
            name = bucket.get("key_as_string","")
            if name == "":
                continue
            else:
                name_list.append(str(name))
                value = bucket.get("doc_count",0)
                value_list.append(value)
                data_dict = {
                    "name":str(name),
                    "value":value
                }
                data_list.append(data_dict)
    chart_data = {
        "data_list":data_list,
        "name_list":name_list,
        "value_list":value_list
    }
    return chart_data

def manual_report(request):
    try:
        id = request.GET.get("id",0)
        res = client.get(index=report_index,
                         doc_type=report_type,
                         id=id
                         )
        category = res.get("_source",{}).get("category","custom_report")
        report_title = res.get("_source",{}).get("title","")
        if category == "custom_report":
            id_list = res.get("_source",{}).get("id_list",[])
            chart_data_list = []
            chart_res = client.search(index=chart_index,
                                      doc_type=chart_type,
                                      body={
                                          "size":100,
                                          "query":{
                                              "terms":{
                                                  "_id":id_list
                                              }
                                          }
                                      }
                                      )
            for hit in chart_res["hits"]["hits"]:
                source = hit["_source"]
                title = source.get("title","")
                chart_category = source.get("category","")
                chart_data = get_chart_data(source)
                if chart_category == "short_china_map":
                    map_type = source.get("map_type","")
                    chart_data["map_type"] = map_type
                chart_data["category"] = chart_category
                chart_data["title"] = title
                chart_data_list.append(chart_data)
            source = {
                "report_id":id,
                "chart_list":chart_data_list,
                "category":category,
                "title":report_title,
                "name":report_title+" "+datetime.datetime.now().strftime("%Y-%m-%d"),
                "datetime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.index(index=report_list_index,
                         doc_type=report_list_type,
                         body=source
                         )
            time.sleep(1)
            return HttpResponseRedirect("../report")
        elif category == "scan_report":
            query = json.loads(res.get("_source",{}).get("query","{}"))
            res = client.search(index=ipv4_index,
                                doc_type=ipv4_type,
                                body=query
                                )
            hits = []
            for hit in res["hits"]["hits"]:
                source = hit["_source"]
                location = source.get("location",{})
                hit_dict = {
                    "ip": source.get("ip",""),
                    "province": location.get("province",""),
                    "port": source.get("port",0),
                    "protocol": source.get("protocol","")
                }
                hits.append(hit_dict)
            asset_count = res["hits"]["total"]
            ip_count = res["aggregations"].get("ip_num",{}).get("value",0)
            port_count = res["aggregations"].get("port_num",{}).get("value",0)
            province_list = []
            # province_name_list = []
            # province_data_list = []
            for buckect in res["aggregations"]["location"]["buckets"]:
                name = buckect.get("key","")
                reg = re.match(u"[\u4E00-\u9FA5]+",name)
                if reg:
                    pass
                else:
                    continue
                data_dict = {
                    "name":name,
                    "asset_num" : buckect.get("doc_count",0),
                    "port_num" : buckect.get("port_num",{}).get("value",0),
                    "ip_num" : buckect.get("ip_num",{}).get("value",0)
                }
                province_list.append(data_dict)
            os_list = []
            data = {
                "asset_count" : asset_count,
                "ip_count" : ip_count,
                "port_count" : port_count,
                "province_list" : province_list,
                "os_list" : os_list
            }
            source = {
                "report_id":id,
                "title":report_title,
                "category":category,
                "data":data,
                "name":report_title+" "+datetime.datetime.now().strftime("%Y-%m-%d"),
                "datetime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.index(index=report_list_index,
                         doc_type=report_list_type,
                         body=source
                         )
            time.sleep(1)
            return HttpResponseRedirect("../report")
        else:
            print "参数错误"
            content = {
                "success":False,
                "msg":"报表类型错误，仅支持自定义报告及扫描报告两种！"
            }
            return HttpResponse(json.dumps(content))
    except Exception,e:
        print str(e)
        content = {
            "success":False
        }
        return HttpResponse(json.dumps(content))

    sql = "SELECT * FROM REPORT WHERE ID = '%d'" % id
    result = __query__.run_sql(pool,sql,"result")
    report_id = result[0][0]
    ids = result[0][3]
    chart_id_list = json.loads(ids)
    i= 0
    str_id = ""
    while i<len(chart_id_list):#为空的话不能过滤，一般为空都是默认就一个内容，不构建的话，下面的in查询会报错
        str_id += "'"+ str(chart_id_list[i])+"'"
        i += 1
        if i<len(chart_id_list):
            str_id += ","
        else:
            pass
    chart_sql = "SELECT TITLE,CATEGORY,RESOURCE_TYPE FROM CHART WHERE ID IN (%s)" % str_id
    chart_result = __query__.run_sql(pool,chart_sql,"result")
    chart_list = []
    for row in chart_result:
        chart_dict = {
            "title":row[0],
            "category":row[1],
            "resource_type":row[2]
        }
        chart_list.append(chart_dict)
    chart_value_list = []
    for chart_dict in chart_list:
        chart_category = chart_dict["category"]
        chart_value_dict = {
            "title":chart_dict["title"],
            "chart_category":chart_category
        }
        resource_type = chart_dict["resource_type"]
        if chart_category == "short_curve":
            print "数据中暂时无时间，折线图先略过"
            continue
        elif chart_category == "short_column":
            if resource_type == "number":
                print "资产暂无分类，无法生成报表"
                continue
            elif resource_type == "ip":
                query = {
                    "size":0,
                    "aggs":{
                        "resource_type":{
                            "terms":{
                                "field":"ip.keyword",
                                "size":5,
                                "shard_size":5
                            }
                        }
                    }
                }
                res = client.search(index=ipv4_index,
                                    doc_type=ipv4_type,
                                    body=query
                                    )
                name_list = []
                value_list = []
                for buckect in res["aggregations"]["resource_type"]["buckets"]:
                    name_list.append(buckect["key"])
                    value_list.append(buckect["doc_count"])
                chart_value_dict["name_list"] = name_list
                chart_value_dict["value_list"] = value_list
                chart_value_list.append(chart_value_dict)
            else:
                print "暂时无数据"
                continue
        elif chart_category == "short_pie":
            if resource_type == "number":
                print "资产暂无分类，无法生成报表"
                continue
            elif resource_type == "ip":
                query = {
                    "size":0,
                    "aggs":{
                        "resource_type":{
                            "terms":{
                                "field":"ip.keyword",
                                "size":5,
                                "shard_size":5
                            }
                        }
                    }
                }
                res = client.search(index=ipv4_index,
                                    doc_type=ipv4_type,
                                    body=query
                                    )
                data_list = []
                for buckect in res["aggregations"]["resource_type"]["buckets"]:
                    data_dict = {
                        "name":buckect["key"],
                        "value":buckect["doc_count"]
                    }
                    data_list.append(data_dict)
                chart_value_dict["data_list"] = data_list
                chart_value_list.append(chart_value_dict)
            elif resource_type == "protocol":
                query = {
                    "size":0,
                    "aggs":{
                        "resource_type":{
                            "terms":{
                                "field":"protocol.keyword",
                                "size":5,
                                "shard_size":500
                            }
                        }
                    }
                }
                res = client.search(index=ipv4_index,
                                    doc_type=ipv4_type,
                                    body=query
                                    )
                data_list = []
                for buckect in res["aggregations"]["resource_type"]["buckets"]:
                    data_dict = {
                        "name":buckect["key"],
                        "value":buckect["doc_count"]
                    }
                    data_list.append(data_dict)
                chart_value_dict["data_list"] = data_list
                chart_value_list.append(chart_value_dict)
            else:
                continue
        else:
            continue
    str_chart_list = json.dumps(chart_value_list,ensure_ascii=False)
    insert_sql = "INSERT INTO REPORT_LIST (REPORT_ID,CHART_LIST) VALUES('%d','%s')"% (report_id,str_chart_list)
    __query__.update_sql(pool,insert_sql)
    return http.HttpResponseRedirect("../report")






def new(request):
    try:
        res = client.search(index=chart_index,
                            doc_type=chart_type,
                            body={
                                "size":100,
                                "_source":["title","built_in"]
                            }
                            )
        scan_chart_list = []
        for hit in res["hits"]["hits"]:
            source = hit.get("_source",{})
            hit_dict = {
                "id":hit["_id"],
                "title":source.get("title",""),
                "built_in":source.get("built_in","")
            }
            scan_chart_list.append(hit_dict)
        return render(request,'report/new_report.html',{
            "scan_chart_list":scan_chart_list,
            "compare_chart_list":[]
        })
    except Exception,e:
        print str(e)
    return render(request,'report/new_report.html',{
        "scan_chart_list":[],
        "compare_chart_list":[]
    })
    chart_sql = "SELECT ID,TYPE,TITLE,BUILT_IN FROM CHART"
    result = __query__.run_sql(pool,chart_sql,"result")
    scan_chart_list = []
    compare_chart_list = []
    for row in result:
        hit_dict = {
            "id":row[0],
            "title":row[2],
            "built_in":row[3]
        }
        if row[1] == 1:
            scan_chart_list.append(hit_dict)
        else:
            compare_chart_list.append(hit_dict)
    # res = client.search(index=chart_index,
    #                     doc_type=chart_type,
    #                     body={
    #                         "query":{
    #                             "match_all":{}
    #                         }
    #                     }
    #                     )
    #
    # for hit in res["hits"]["hits"]:
    #     source = hit.get("_source",{})
    #     hit_dict = {
    #         "id":hit["_id"],
    #         "title":source.get("title",""),
    #         "built_in":source.get("built_in",0)
    #     }
    #     if source.get("type","") == "scan_chart":
    #         scan_chart_list.append(hit_dict)
    #     else:
    #         compare_chart_list.append(hit_dict)
    # #内容待完成
    return render(request,'report/new_report.html',{
        "scan_chart_list":scan_chart_list,
        "compare_chart_list":compare_chart_list
    })

def edit(request):
    #修改保存内容待完成
    if request.method == "GET":
        id = request.GET.get("id","")
        try:
            chart_id_res = client.get(index=report_index,
                                   doc_type=report_type,
                                   id = id
                                      )
            chart_id_list = chart_id_res["_source"].get("id_list",[])
            title = chart_id_res["_source"].get("title","")
            category = chart_id_res["_source"].get("category","")
            res = client.search(index=chart_index,
                                doc_type=chart_type,
                                body={
                                    "size":100,
                                    "_source":["title","built_in"]
                                }
                                )
            scan_chart_list = []
            for hit in res["hits"]["hits"]:
                source = hit.get("_source",{})
                selected = 0
                if hit["_id"] in chart_id_list:
                    selected = 1
                hit_dict = {
                    "id":hit["_id"],
                    "selected":selected,
                    "title":source.get("title",""),
                    "built_in":source.get("built_in","")
                }
                scan_chart_list.append(hit_dict)
            return render(request,'report/edit_report.html',{
                "scan_chart_list":scan_chart_list,
                "title":title,
                "id":id,
                "category":category,
                "compare_chart_list":[]
            })
        except Exception,e:
            print str(e)
        return HttpResponse("编辑执行错误")
    elif request.method == "POST":
        try:
            chart_id_list = request.POST.getlist("report[chart_ids][]",[])
            category = request.POST.get("category","")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            id = request.POST.get("report_id","")
            id_list = []
            for chart_id in chart_id_list:
                id_list.append(chart_id)
            id_list = sorted(id_list)
            title = request.POST.get("title","")
            if title =="" or id == "":
                content = {
                    "success":False,
                    "msg":"标题不能为空"
                }
            else:
                source = {
                    "title":title,
                    "category":category,
                    "datetime":timestamp,
                    "id_list":id_list
                }
                client.update(index=report_index,
                             doc_type=report_type,
                             id=id,
                             body={
                                 "doc":source
                             }
                             )
                time.sleep(1)
                return HttpResponseRedirect("../report")
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"操作执行失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))


def detail(request):
    try:
        id = request.GET.get("id","")
        res = client.get(index=report_list_index,
                         doc_type=report_list_type,
                         id=id
                         )
        source = res["_source"]
        category = source.get("category","custom_report")
        if category == "custom_report":
            chart_list = source.get("chart_list",[])
            i = 1
            for chart in chart_list:
                chart["id"] = "chart_"+str(i)
                map_type = chart.get("map_type","")
                js_name = province_pinyin_dict.get(map_type,map_type)
                chart["js_name"] = js_name
                chart["data_list"] = json.dumps(chart.get("data_list",[]),ensure_ascii=False)
                chart["name_list"] = json.dumps(chart.get("name_list",[]),ensure_ascii=False)
                i += 1
            hit = {
                "success":True,
                "chart_list":chart_list,
                "datetime":source.get("datetime",""),
                "title":source.get("title","")
            }
        elif category == "scan_report":
            data = source.get("data",{})
            hit = {
                "success":True,
                "data":data,
                "datetime":source.get("datetime",""),
                "title":source.get("title","")
            }
            return render(request,"report/report_detail.html",{
                "hit":hit
            })
    except:
        hit = {
            "success":False
        }
    return render(request,'report/detail.html',{
        "hit":hit
    })
    sql = "SELECT CHART_LIST,DATETIME FROM REPORT_LIST WHERE ID = '%s'" % id
    result = __query__.run_sql(pool,sql,"result")
    if len(result)>0:
        row = result[0]
    else:
        content = {
            "success":False,
            "msg":"id format wrong"
        }
        return HttpResponse(json.dumps(content))
    hit = {
        "chart_list":json.loads(row[0]),
        "datetime":row[1].strftime("%Y-%m-%d %H:%M:%S")
    }
    return render(request,'report/report_template.html',{
        "hit":hit
    })


def get_pdf(request):
    pass


def report_detail(request):
    return render(request,"report/report_detail.html",{})