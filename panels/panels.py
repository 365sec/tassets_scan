# coding:utf-8

from django.shortcuts import render,HttpResponse
from .. import conf_list,query_dsl
import random
import json
import logging

logger = logging.getLogger('access_ip')

client = conf_list.client
vul_index = conf_list.vuln_index
vul_type = conf_list.vuln_type
ipv4_index = conf_list.ipv4_index
ipv4_type = conf_list.ipv4_type
asset_index = conf_list.asset_index
asset_type = conf_list.asset_type
__query__ = query_dsl.Query()



def get_color(value):
    if value < 4:
        color = "maroon"
    elif 4<=value< 7:
        color = "purple"
    elif 7<=value< 10:
        color = "red"
    elif 10<=value< 13:
        color = "orange"
    elif 13<=value< 16:
        color = "yellow"
    else:
        color = "lightgreen"
    return color



def get_city_asset_num(city_list,vul_scatter_point_list):#获取城市资产数
    city_asset_list = []
    aggs_dict = {}
    for city in city_list:
        aggs_dict[city] = {
            "filter":{
                "term":{
                    "city.keyword":city
                }
            }
        }
    res = client.search(index=asset_index,
                        doc_type=asset_type,
                        body={
                            "size":0,
                            "aggs":aggs_dict
                        }
                        )
    city_asset_num_dict = {}
    for city in city_list:
        city_asset_num_dict[city] = res["aggregations"][city].get("doc_count",0 )
        city_asset_list.append(city_asset_num_dict[city])
    for vul_scatter_point_dict in vul_scatter_point_list:
        city = vul_scatter_point_dict["name"]
        vul_scatter_point_dict["asset_num"] = city_asset_num_dict[city]
    dict = {
        "vul_scatter_point_list":vul_scatter_point_list,
        "city_asset_list":city_asset_list
    }
    return dict

def get_vul_dict():
    res = client.search(index=vul_index,
                        doc_type=vul_type,
                        body={
                            "size":0,
                            "aggs":{
                                "asset":{
                                    "terms":{
                                        "field":"ip",
                                        "size":100,
                                        "shard_size":100
                                    },
                                    "aggs":{
                                        "top":{
                                            "top_hits":{
                                                "size":1,
                                                "_source":["domain","location.city","location.province"]
                                            }
                                        }
                                    }
                                },
                                "risk_asset":{
                                    "cardinality":{
                                        "field":"ip"
                                    }
                                },
                                "level":{
                                    "terms":{
                                        "field":"risk.keyword",
                                        "size":100,
                                        "shard_size":100
                                    }
                                },
                                "vul":{
                                    "terms":{
                                        "field":"name.keyword",
                                        "size":100,
                                        "shard_size":100
                                    },
                                    "aggs":{
                                        "top":{
                                            "top_hits":{
                                                "size":1,
                                                "_source":["risk"]
                                            }
                                        }
                                    }
                                },
                                "scatter":{
                                    "terms":{
                                        "field":"location.city.keyword",
                                        "size":15,
                                        "shard_size":1000
                                    },
                                    "aggs":{
                                        "top":{
                                            "top_hits":{
                                                "size":1,
                                                "_source":["location"]
                                            }
                                        },
                                        "risk_num":{
                                            "cardinality":{
                                                "field":"ip"
                                            }
                                        },
                                        "level_scatter":{
                                            "terms":{
                                                "field":"risk.keyword"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        )
    vul_num = res["hits"]["total"]
    risk_asset_num = res["aggregations"]["risk_asset"]["value"]
    # 获取漏洞分布情况
    vul_scatter_point_list = []
    vul_effect_scatter_list = []
    city_list = []
    i = 1
    vul_num_max = 500
    city_serious_vul_num_list = []
    city_high_vul_num_list = []
    city_middle_vul_num_list = []
    city_low_vul_num_list = []
    if len(res["aggregations"]["scatter"]["buckets"])>0:
        vul_num_max = res["aggregations"]["scatter"]["buckets"][0].get("doc_count",0)
    else:
        pass
    city_name_list = [] #左上角统计报表用
    city_vul_num_list = [] #左上角统计报表用
    pie_city_vul_list = [] #左下角饼图城市漏洞数用，取TOP5
    vul_risk_name_list = [] #获取左侧中间漏洞等级分布
    vul_risk_num_list = []
    for vul_risk_name in ["严重","高危","中危","低危"]:
        vul_risk_count = 0
        for bucket in res["aggregations"]["level"]["buckets"]:
            inner_vul_risk_name = bucket.get("key","")
            if vul_risk_name == inner_vul_risk_name:
                vul_risk_count = bucket.get("doc_count",0)
                break
            else:
                pass
        vul_risk_name_list.append(vul_risk_name)
        vul_risk_num_list.append(vul_risk_count)


    for bucket in res["aggregations"]["scatter"]["buckets"]:
        city = bucket.get("key","")
        city_list.append(city)
        city_vul_num = bucket.get("doc_count",0)
        city_name_list.append(city)
        city_vul_num_list.append(city_vul_num)
        color = get_color(i)
        if i < 6:
            pie_city_vul_dict = {
                "name":city,
                "value":city_vul_num
            }
            pie_city_vul_list.append(pie_city_vul_dict)
        else:
            pass
        i += 1
        city_risk_asset_num = bucket.get("risk_num",{}).get("value",0)
        source = bucket.get("top",{})["hits"]["hits"][0]["_source"]
        province = source.get("location",{}).get("province","")
        latitude = source.get("location",{}).get("latitude","")
        longitude = source.get("location",{}).get("longitude","")
        vul_scatter_point_dict = {
            "name":city,
            "value":city_vul_num,
            "seriesName":"point",
            "risk_asset":city_risk_asset_num,
            "coord":[longitude,latitude],
            "province":province,
            "itemStyle":{
                "emphasis":{
                    "borderColor":color
                }
            }
        }
        vul_effect_scatter_dict = {
            "name":city,
            "value":[longitude,latitude,city_vul_num],
            "itemStyle":{
                "normal":{
                    "color":color
                }
            }
        }
        vul_scatter_point_list.append(vul_scatter_point_dict)
        vul_effect_scatter_list.append(vul_effect_scatter_dict)
        serious_vul_num = 0
        high_vul_num = 0
        middle_vul_num = 0
        low_vul_num = 0
        for level_bucket in bucket["level_scatter"]["buckets"]:
            vul_level = level_bucket.get("key","")
            if vul_level == "严重":
                serious_vul_num = level_bucket.get("doc_count","")
            elif vul_level == "高危":
                high_vul_num = level_bucket.get("doc_count","")
            elif vul_level == "中危":
                middle_vul_num = level_bucket.get("doc_count","")
            else:
                low_vul_num = level_bucket.get("doc_count","")
        city_serious_vul_num_list.append(serious_vul_num)
        city_high_vul_num_list.append(high_vul_num)
        city_middle_vul_num_list.append(middle_vul_num)
        city_low_vul_num_list.append(low_vul_num)

    #生成查询城市资产数的语句并获取相关内容
    city_asset_dict = get_city_asset_num(city_list,vul_scatter_point_list)
    vul_scatter_point_list = city_asset_dict.get("vul_scatter_point_list",[])
    city_asset_list = city_asset_dict.get("city_asset_list",[]) #左上角统计报表用
    # 获取资产漏洞数信息
    asset_list = []
    for bucket in res["aggregations"]["asset"]["buckets"]:
        search_field = "ip"
        domain = bucket["top"]["hits"]["hits"][0]["_source"].get("domain","")
        city = bucket["top"]["hits"]["hits"][0]["_source"].get("location",{}).get("city","")
        province = bucket["top"]["hits"]["hits"][0]["_source"].get("location",{}).get("province","")
        if domain!= "":
            key = domain
            search_field = "domain"
        else:
            key = bucket.get("key","")
        asset_dict = {
            "key":key,
            "city":city,
            "province":province,
            "search_field":search_field,
            "num":bucket.get("doc_count",0)
        }
        asset_list.append(asset_dict)
    asset_vul_hits = []
    length = len(asset_list)
    if length>0:
        if length>7:
            for i in range(0,7):
                r = random.randint(0,len(asset_list)-1)
                asset_vul_hits.append(asset_list[r])
        else:
            for i in range(0,length):
                r = random.randint(0,len(asset_list)-1)
                asset_vul_hits.append(asset_list[r])
    #获取漏洞相关资产数
    vul_hits = []
    top_vul_list = []
    i = 0
    for bucket in res["aggregations"]["vul"]["buckets"]:
        risk = bucket["top"]["hits"]["hits"][0]["_source"].get("risk","")
        key = bucket.get("key","")
        if i < 10:
            top_vul_dict = {
                "name":key,
                "value":bucket.get("doc_count",0)
            }
            top_vul_list.append(top_vul_dict)
            i += 1
        vul_dict = {
            "key":key,
            "risk":risk,
            "num":bucket.get("doc_count",0)
        }
        vul_hits.append(vul_dict)
    vul_list = []
    vul_length = len(vul_hits)
    if len(vul_hits)>0:
        if len(vul_hits)>7:
            for i in range(0,7):
                r = random.randint(0,len(vul_hits)-1)
                vul_list.append(vul_hits[r])
        else:
            for i in range(0,vul_length):
                r = random.randint(0,len(vul_hits)-1)
                vul_list.append(vul_hits[r])
    vul_dict = {
        "asset_vul_hits":asset_vul_hits,
        "vul_num":vul_num,
        "risk_asset_num":risk_asset_num,
        "vul_num_max":vul_num_max,
        "vul_list":vul_list,
        "vul_risk_name_list":vul_risk_name_list,
        "vul_risk_num_list":vul_risk_num_list,
        "top_vul_list":top_vul_list,
        "vul_effect_scatter_list":vul_effect_scatter_list,
        "vul_scatter_point_list":vul_scatter_point_list,
        "city_name_list":city_name_list,
        "city_vul_num_list":city_vul_num_list,
        "city_asset_list":city_asset_list,
        "city_serious_vul_num_list":city_serious_vul_num_list,
        "city_high_vul_num_list":city_high_vul_num_list,
        "city_middle_vul_num_list":city_middle_vul_num_list,
        "city_low_vul_num_list":city_low_vul_num_list,
        "pie_city_vul_list":pie_city_vul_list
    }
    return vul_dict

def get_asset_info():
    aggs = client.search(index=ipv4_index,
                         doc_type=ipv4_type,
                         body={
                             "size":0,
                             "aggs":{
                                 "domain_exist": {
                                     "filter": {
                                         "exists": {
                                             "field": "domain"
                                         }
                                     }
                                 },
                                 "empty_domain":{
                                     "filter":{
                                         "term":{
                                             "domain.keyword":""
                                         }
                                     }
                                 },
                                 "port":{
                                     "terms":{
                                         "field":"port",
                                         "size":10,
                                         "shard_size":1000
                                     }
                                 },
                                 "protocol":{
                                     "terms":{
                                         "field":"protocol.keyword",
                                         "size":10,
                                         "shard_size":1000
                                     }
                                 }
                             }
                         })
    total = aggs.get("hits",{}).get("total",0)
    domain_exist = aggs.get("aggregations",{}).get("domain_exist",{}).get("doc_count",0)
    empty_domain = aggs.get("aggregations",{}).get("empty_domain",{}).get("doc_count",0)
    website = domain_exist - empty_domain
    device = total - website
    port_name_list = []
    port_value_list = []
    protocol_name_list = []
    protocol_value_list = []
    for bucket in aggs.get("aggregations",{}).get("port",{}).get("buckets",[]):
        port_name_list.append(bucket.get("key",""))
        port_value_list.append(bucket.get("doc_count",0))
    for bucket in aggs.get("aggregations",{}).get("protocol",{}).get("buckets",[]):
        protocol_name_list.append(bucket.get("key",""))
        protocol_value_list.append(bucket.get("doc_count",0))
    asset_dict = {
        "total":total,
        "website":website,
        "device":device,
        "port_name_list":port_name_list,
        "port_value_list":port_value_list,
        "protocol_name_list":protocol_name_list,
        "protocol_value_list":protocol_value_list
    }
    return asset_dict


def panels(request):
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        ip =  request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    message = "["+__query__.get_time_stamp()+"+0800]: "+ip+" \"panels\""
    logger.info(message)
    vul_dict = get_vul_dict()
    asset_vul_hits = vul_dict.get("asset_vul_hits",[])
    vul_num = vul_dict.get("vul_num",0)
    risk_asset_num = vul_dict.get("risk_asset_num",0)
    vul_num_max = vul_dict.get("vul_num_max",0)
    vul_list = vul_dict.get("vul_list",[])
    vul_risk_name_list = vul_dict.get("vul_risk_name_list",[])
    vul_risk_num_list = vul_dict.get("vul_risk_num_list",[])
    asset_info_dict = get_asset_info()
    return render(request,"panels/panels.html",{
        "asset_vul_hits":asset_vul_hits,
        "vul_list":vul_list,
        "vul_num":__query__.group(vul_num),
        "risk_asset_num":__query__.group(risk_asset_num),
        "vul_num_max":vul_num_max,
        "vul_risk_name_list":json.dumps(vul_risk_name_list),
        "vul_risk_num_list":json.dumps(vul_risk_num_list),
        "port_name_list":json.dumps(asset_info_dict.get("port_name_list",[])),
        "port_value_list":json.dumps(asset_info_dict.get("port_value_list",[])),
        "protocol_name_list":json.dumps(asset_info_dict.get("protocol_name_list",[])),
        "protocol_value_list":json.dumps(asset_info_dict.get("protocol_value_list",[])),
        "vul_effect_scatter_list":json.dumps(vul_dict.get("vul_effect_scatter_list",[])),
        "vul_scatter_point_list":json.dumps(vul_dict.get("vul_scatter_point_list",[])),
        "top_vul_list":json.dumps(vul_dict.get("top_vul_list",[])),
        "city_name_list":json.dumps(vul_dict.get("city_name_list",[])),
        "city_vul_num_list":json.dumps(vul_dict.get("city_vul_num_list",[])),
        "city_asset_list":json.dumps(vul_dict.get("city_asset_list",[])),
        "pie_city_vul_list":json.dumps(vul_dict.get("pie_city_vul_list",[])),
        "city_serious_vul_num_list":json.dumps(vul_dict.get("city_serious_vul_num_list",[])),
        "city_high_vul_num_list":json.dumps(vul_dict.get("city_high_vul_num_list",[])),
        "city_middle_vul_num_list":json.dumps(vul_dict.get("city_middle_vul_num_list",[])),
        "city_low_vul_num_list":json.dumps(vul_dict.get("city_low_vul_num_list",[])),
        "total":__query__.group(asset_info_dict.get("total",0)),
        "website":__query__.group(asset_info_dict.get("website",0)),
        "device":__query__.group(asset_info_dict.get("device",0))
    })

def get_vul_info(): #漏洞数目信息
    res = client.search(index=vul_index,
                        doc_type=vul_type,
                        body={
                            "size":0,
                            "aggs":{
                                "vul":{
                                    "cardinality":{
                                        "field":"ip"
                                    }
                                }
                            }
                        }
                        )
    threats_num = res["hits"]["total"]
    risk_asset_num = res["aggregations"]["vul"]["value"]
    dict = {
        "threats_num":threats_num,
        "risk_asset_num":risk_asset_num
    }
    return dict

def get_count_info(request):
    try:
        asset_info_dict = get_asset_info()
        vul_info_dict = get_vul_info()
        content = dict(asset_info_dict,**vul_info_dict)
        for key in content:
            content[key] = __query__.group(content[key])
        content["success"] = True
    except Exception,e:
        print str(e)
        content = {
            "success":False,
            "msg":"获取信息失败"
        }
    return HttpResponse(json.dumps(content,ensure_ascii=False))


