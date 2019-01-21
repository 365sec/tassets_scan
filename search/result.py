# coding:utf-8

from django.shortcuts import render,HttpResponse
from django.http import StreamingHttpResponse
from .. import conf_list,query_dsl
import json
import codecs
import csv
import cgi
import re

client = conf_list.client
index = conf_list.ipv4_index
index_type = conf_list.ipv4_type
country_terms_num = conf_list.country_terms_num
province_terms_num = conf_list.province_terms_num
port_terms_num = conf_list.port_terms_num
protocol_terms_num = conf_list.protocol_terms_num
tag_terms_num = conf_list.tag_terms_num
ip_exp = conf_list.ip_exp
__query__ = query_dsl.Query()


def get_str_from_list(value_list,symbol=","):#列表值提取转字符串
    if value_list:
        pass
    else:
        value_list = []
    content = ""
    i = 0
    while i <len(value_list):
        content += value_list[i]
        i += 1
        if i <len(value_list):
            content += symbol
        else:
            pass
    return content


def get_aggs_count(query):
    res = client.search(index=index,
                        doc_type=index_type,
                        body={
                            "size":0,
                            "query":query,
                            "aggs":{
                                "port":{
                                    "terms":{
                                        "field":"port",
                                        "size":5,
                                        "shard_size":100
                                    }
                                },
                                "protocol":{
                                    "terms":{
                                        "field":"protocol.keyword",
                                        "size":5,
                                        "shard_size":100
                                    }
                                }
                            }
                        }
                        )
    port_list = []
    port_name_list = []
    for bucket in res["aggregations"]["port"]["buckets"]:
        port_dict = {}
        if bucket["key"] != "":
            port_dict["name"] = str(bucket["key"])
            port_dict["value"] = bucket["doc_count"]
        else:
            port_dict["name"] = "unknown"
            port_dict["value"] = bucket["doc_count"]
        port_list.append(port_dict)
        port_name_list.append(port_dict["name"])
    protocol_list = []
    protocol_name_list = []
    for bucket in res["aggregations"]["protocol"]["buckets"]:
        protocol_dict = {}
        if bucket["key"] != "":
            protocol_dict["name"] = bucket["key"]
            protocol_dict["value"] = bucket["doc_count"]
        else:
            protocol_dict["name"] = "unknown"
            protocol_dict["value"] = bucket["doc_count"]
        protocol_list.append(protocol_dict)
        protocol_name_list.append(protocol_dict["name"])
    count_dict = {
        "port_name_list":port_name_list,
        "port_list":port_list,
        "protocol_name_list":protocol_name_list,
        "protocol_list":protocol_list
    }
    return count_dict

def ip_check(func):
    def check(*args):
        request = args[0]
        if request.method =="POST":
            return func(*args)
        elif request.method =="GET":
            ip = request.GET.get("ip","")
            if ip != "":
                reg = re.match(ip_exp,ip)
                if reg:
                    return func(*args)
                else:
                    content = "ip段数据格式错误"
                    return HttpResponse(content)
            else:
                return func(*args)
    return check

@ip_check
def result(request):
    try:
        search_type = request.GET.get("search_type","")
        search_content = request.GET.get("q","")
        page = int(request.GET.get("page",1))
        if search_type !="advanced":
            query = __query__.get_query(search_content.strip(" "))
            try:
                res = client.search(index=index,
                                    doc_type=index_type,
                                    body={
                                        "from":(page-1)*10,
                                        "size":10,
                                        "sort":[
                                            {
                                                "timestamp":{
                                                    "order":"desc"
                                                }
                                            }
                                        ],
                                        "query":query
                                    }
                                    )
                aggs_dict = get_aggs_count(query)
                total = res["hits"]["total"]
                took_time = res["took"]
                page_nums = int(total / 10) + 1 if (total % 10) > 0 else int(total / 10)
                page_list = [
                    i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
                ]
                hits = []
                for hit in res["hits"]["hits"]:
                    source = hit["_source"]
                    data = source.get("data",{})
                    if data:
                        pass
                    else:
                        data = {}
                    title = cgi.escape(data.get("title",""))
                    location = source.get("location",{})
                    country = location.get("country","")
                    country_code = (location.get("country_code","")).lower()
                    city = location.get("city","")
                    headers = data.get("headers",{})
                    banner = data.get("banner",{})
                    icp = cgi.escape(data.get("icp",""))
                    timestamp = source.get("timestamp","")
                    if timestamp != "":
                        timestamp = timestamp.split(" ")[0]
                    if headers != {}:
                        data = json.dumps(headers,indent=4)
                    elif banner != {}:
                        data = json.dumps(banner,indent=4)
                    else:
                        data = json.dumps(data,indent=4)
                    if data == "{}":
                        data = ""
                    domain = source.get("domain","")
                    hit_dict={
                        "id":hit["_id"],
                        "ip":source.get("ip",""),
                        "port":source.get("port",""),
                        "protocol":source.get("protocol",""),
                        "tags":source.get("tags",[]),
                        "title":title,
                        "icp":icp,
                        "domain":domain,
                        "data":data,
                        "timestamp":timestamp,
                        "country":country,
                        "country_code":country_code,
                        "city":city
                    }
                    hits.append(hit_dict)
                return render(request,'search/result.html',{
                    "hits":hits,
                    "count":__query__.group(total),
                    "search_content":search_content,
                    "page_nums":page_nums,
                    "page_list":page_list,
                    "current_page":page,
                    "last_page":page-1,
                    "next_page":page+1,
                    "took_time":took_time,
                    "search_type":"normal",
                    "asset_ip":"",
                    "asset_port":"",
                    "asset_protocol":"",
                    "asset_os":"",
                    "asset_domain":"",
                    "port_name_list":json.dumps(aggs_dict["port_name_list"]),
                    "port_list":json.dumps(aggs_dict["port_list"]),
                    "protocol_name_list":json.dumps(aggs_dict["protocol_name_list"]),
                    "protocol_list":json.dumps(aggs_dict["protocol_list"])
                })
            except Exception as e:
                print str(e)
                return render(request,'search/result.html',{
                    "hits":[],
                    "count":0,
                    "search_content":search_content,
                    "page_nums":0,
                    "page_list":[],
                    "current_page":page,
                    "last_page":page-1,
                    "next_page":page+1,
                    "took_time":"0",
                    "search_type":"normal",
                    "asset_ip":"",
                    "asset_port":"",
                    "asset_protocol":"",
                    "asset_os":"",
                    "asset_domain":"",
                    "port_name_list":"[]",
                    "port_list":"[]",
                    "protocol_name_list":"[]",
                    "protocol_list":"[]"
                })
        else:
            ip = request.GET.get("ip","")
            port = request.GET.get("port","")
            protocol = request.GET.get("protocol","")
            os = request.GET.get("os","")
            tags = request.GET.get("tags","")
            domain = request.GET.get("domain","")
            search_content = ""
            if ip != "":
                search_content += "ip=\""+ip+"\""
            else:
                pass
            if port != "":
                if search_content != "":
                    search_content += " AND port=\""+port+"\""
                else:
                    search_content += "port=\""+port+"\""
            else:
                pass
            if protocol != "":
                if search_content != "":
                    search_content += " AND protocol=\""+protocol+"\""
                else:
                    search_content += "protocol=\""+protocol+"\""
            else:
                pass
            if os != "":
                if search_content != "":
                    search_content += " AND os=\""+os+"\""
                else:
                    search_content += "os=\""+os+"\""
            else:
                pass
            if tags != "":
                if search_content != "":
                    search_content += " AND tags=\""+tags+"\""
                else:
                    search_content += "tags=\""+tags+"\""
            else:
                pass
            if domain != "":
                if search_content != "":
                    search_content += " AND domain=\""+domain+"\""
                else:
                    search_content += "domain=\""+domain+"\""
            else:
                pass
            query = __query__.get_query(search_content)
            try:
                res = client.search(index=index,
                                    doc_type=index_type,
                                    body={
                                        "from":(page-1)*10,
                                        "size":10,
                                        "sort":[
                                            {
                                                "timestamp":{
                                                    "order":"desc"
                                                }
                                            }
                                        ],
                                        "query":query
                                    }
                                    )
                aggs_dict = get_aggs_count(query)
                total = res["hits"]["total"]
                took_time = res["took"]
                page_nums = int(total / 10) + 1 if (total % 10) > 0 else int(total / 10)
                page_list = [
                    i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
                ]
                hits = []
                for hit in res["hits"]["hits"]:
                    source = hit["_source"]
                    # protocol = source.get("protocol","")
                    data = source.get("data",{})
                    if data:
                        pass
                    else:
                        data = {}
                    location = source.get("location",{})
                    country = location.get("country","")
                    country_code = (location.get("country_code","")).lower()
                    city = location.get("city","")
                    icp = cgi.escape(data.get("icp",""))
                    title = cgi.escape(data.get("title",""))
                    headers = data.get("headers",{})
                    banner = data.get("banner",{})
                    timestamp = source.get("timestamp","")
                    if country:
                        pass
                    else:
                        country = ""
                    if city:
                        pass
                    else:
                        city = ""
                    if title:
                        pass
                    else:
                        title = ""
                    if timestamp != "":
                        timestamp = timestamp.split(" ")[0]
                    if headers != {}:
                        data = json.dumps(headers,indent=4)
                    elif banner != {}:
                        data = json.dumps(banner,indent=4)
                    else:
                        data = json.dumps(data,indent=4)
                    if data == "{}":
                        data = ""
                    inner_domain = source.get("domain","")
                    hit_dict={
                        "id":hit["_id"],
                        "ip":source.get("ip",""),
                        "port":source.get("port",""),
                        "protocol":source.get("protocol",""),
                        "tags":source.get("tags",[]),
                        "title":title,
                        "icp":icp,
                        "domain":inner_domain,
                        "data":data,
                        "timestamp":timestamp,
                        "country":country,
                        "country_code":country_code,
                        "city":city
                    }
                    hits.append(hit_dict)
                return render(request,'search/result.html',{
                    "search_type":search_type,
                    "ip":ip,
                    "port":port,
                    "protocol":protocol,
                    "os":os,
                    "domain":domain,
                    "hits":hits,
                    "count":__query__.group(total),
                    "search_content":search_content,
                    "page_nums":page_nums,
                    "page_list":page_list,
                    "current_page":page,
                    "last_page":page-1,
                    "next_page":page+1,
                    "took_time":took_time,
                    "asset_ip":"",
                    "asset_port":"",
                    "asset_protocol":"",
                    "asset_os":"",
                    "asset_domain":"",
                    "port_name_list":json.dumps(aggs_dict["port_name_list"]),
                    "port_list":json.dumps(aggs_dict["port_list"]),
                    "protocol_name_list":json.dumps(aggs_dict["protocol_name_list"]),
                    "protocol_list":json.dumps(aggs_dict["protocol_list"])
                })
            except Exception as e:
                print str(e)
                return render(request,'search/result.html',{
                    "search_type":search_type,
                    "ip":ip,
                    "port":port,
                    "protocol":protocol,
                    "os":os,
                    "domain":domain,
                    "hits":[],
                    "count":0,
                    "search_content":search_content,
                    "page_nums":0,
                    "page_list":[],
                    "current_page":page,
                    "last_page":page-1,
                    "next_page":page+1,
                    "took_time":'0',
                    "asset_ip":"",
                    "asset_port":"",
                    "asset_protocol":"",
                    "asset_os":"",
                    "asset_domain":"",
                    "port_name_list":"[]",
                    "port_list":"[]",
                    "protocol_name_list":"[]",
                    "protocol_list":"[]"
                })
    except Exception as e:
        print str(e)
        return HttpResponse("参数格式错误")


def count(request):
    search_content = request.GET.get("q","")
    search_type = request.GET.get("search_type","")
    try:
        if search_type !="advanced":
            query = __query__.get_query(search_content.strip(" "))
            aggs = client.search(index=index,
                                 doc_type=index_type,
                                 body={
                                     "size":0,
                                     "query":query,
                                     "aggs":{
                                         "port":{
                                             "terms":{
                                                 "field":"port",
                                                 "size":port_terms_num,
                                                 "shard_size":100
                                             }
                                         },
                                         "protocol":{
                                             "terms":{
                                                 "field":"protocol.keyword",
                                                 "size":protocol_terms_num,
                                                 "shard_size":100
                                             }
                                         },
                                         "tags":{
                                             "terms":{
                                                 "field":"tags.keyword",
                                                 "size":tag_terms_num,
                                                 "shard_size":100
                                             }
                                         },
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
                                         "location":{
                                            "terms":{
                                                "field":"location.country.keyword",
                                                "size":country_terms_num,
                                                "shard_size":100
                                            },
                                             "aggs":{
                                                 "country_code":{
                                                     "terms":{
                                                         "field":"location.country_code.keyword"
                                                     }
                                                 },
                                                 "province":{
                                                     "terms":{
                                                         "field":"location.province.keyword",
                                                         "size":province_terms_num,
                                                         "shard_size":100
                                                     }
                                                 }
                                             }
                                         },
                                         "components":{
                                             "nested":{
                                                 "path":"components"
                                             },
                                             "aggs":{
                                                 "server":{
                                                     "terms":{
                                                         "field":"components.description.keyword",
                                                         "size":5,
                                                         "shard_size":100
                                                     }
                                                 },
                                                 "os":{
                                                     "terms":{
                                                         "field":"components.os.keyword",
                                                         "size":5,
                                                         "shard_size":100
                                                     }
                                                 }
                                             }
                                         }
                                     }
                                 }
                                 )
            took = aggs["took"]
            country_list = []
            total = aggs.get("hits",{}).get("total",0)
            domain_exist = aggs.get("aggregations",{}).get("domain_exist",{}).get("doc_count",0)
            empty_domain = aggs.get("aggregations",{}).get("empty_domain",{}).get("doc_count",0)
            website = domain_exist - empty_domain
            device = total - website
            for bucket in aggs["aggregations"]["location"]["buckets"]:
                country_code_list = bucket.get("country_code",{}).get("buckets",[])
                if len(country_code_list)>0:
                    country_code = (country_code_list[0].get("key","")).lower()
                else:
                    country_code = ""
                province_list = []
                for province_bucket in bucket.get("province",{}).get("buckets",[]):
                    province_dict = {
                        "name":province_bucket.get("key",""),
                        "value":__query__.group(province_bucket.get("doc_count",0)),
                    }
                    province_list.append(province_dict)
                country_dict = {
                    "name":bucket.get("key",""),
                    "value":__query__.group(bucket.get("doc_count",0)),
                    "country_code":country_code,
                    "province_list":province_list
                }
                country_list.append(country_dict)
            port_list = []
            for bucket in aggs["aggregations"]["port"]["buckets"]:
                port_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                port_list.append(port_dict)
            protocol_list = []
            for bucket in aggs["aggregations"]["protocol"]["buckets"]:
                protocol_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                protocol_list.append(protocol_dict)
            tag_list = []
            for bucket in aggs["aggregations"]["tags"]["buckets"]:
                tag_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                tag_list.append(tag_dict)
            server_list = []
            for bucket in aggs["aggregations"]["components"]["server"]["buckets"]:
                server_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                server_list.append(server_dict)
            os_list = []
            for bucket in aggs["aggregations"]["components"]["os"]["buckets"]:
                os_dict = {
                    "name":bucket["key"],
                    "value":bucket["doc_count"]
                }
                os_list.append(os_dict)
            content = {
                "took":took,
                "port_list":port_list,
                "protocol_list":protocol_list,
                "server_list":server_list,
                "os_list":os_list,
                "tag_list":tag_list,
                "country_list":country_list,
                "website":__query__.group(website),
                "device":__query__.group(device)
            }
            return HttpResponse(json.dumps(content))
        else:
            ip = request.GET.get("ip","")
            port = request.GET.get("port","")
            protocol = request.GET.get("protocol","")
            os = request.GET.get("os","")
            domain = request.GET.get("domain","")
            tags = request.GET.get("tags","")
            search_content = ""
            if ip != "":
                search_content += "ip=\""+ip+"\""
            else:
                pass
            if port != "":
                if search_content != "":
                    search_content += " AND port=\""+port+"\""
                else:
                    search_content += "port=\""+port+"\""
            else:
                pass
            if protocol != "":
                if search_content != "":
                    search_content += " AND protocol=\""+protocol+"\""
                else:
                    search_content += "protocol=\""+protocol+"\""
            else:
                pass
            if os != "":
                if search_content != "":
                    search_content += " AND os=\""+os+"\""
                else:
                    search_content += "os=\""+os+"\""
            else:
                pass
            if tags != "":
                if search_content != "":
                    search_content += " AND tags=\""+tags+"\""
                else:
                    search_content += "tags=\""+tags+"\""
            else:
                pass
            if domain != "":
                if search_content != "":
                    search_content += " AND domain=\""+domain+"\""
                else:
                    search_content += "domain=\""+domain+"\""
            else:
                pass
            query = __query__.get_query(search_content)
            aggs = client.search(index=index,
                                 doc_type=index_type,
                                 body={
                                     "size":0,
                                     "query":query,
                                     "aggs":{
                                         "port":{
                                             "terms":{
                                                 "field":"port",
                                                 "size":5,
                                                 "shard_size":100
                                             }
                                         },
                                         "protocol":{
                                             "terms":{
                                                 "field":"protocol.keyword",
                                                 "size":5,
                                                 "shard_size":100
                                             }
                                         },
                                         "tags":{
                                             "terms":{
                                                 "field":"tags.keyword",
                                                 "size":tag_terms_num,
                                                 "shard_size":100
                                             }
                                         },
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
                                         "location":{
                                             "terms":{
                                                 "field":"location.country.keyword",
                                                 "size":5,
                                                 "shard_size":100
                                             },
                                             "aggs":{
                                                 "country_code":{
                                                     "terms":{
                                                         "field":"location.country_code.keyword"
                                                     }
                                                 },
                                                 "province":{
                                                     "terms":{
                                                         "field":"location.province.keyword"
                                                     }
                                                 }
                                             }
                                         },
                                         "components":{
                                             "nested":{
                                                 "path":"components"
                                             },
                                             "aggs":{
                                                 "server":{
                                                     "terms":{
                                                         "field":"components.description.keyword",
                                                         "size":5,
                                                         "shard_size":100
                                                     }
                                                 },
                                                 "os":{
                                                     "terms":{
                                                         "field":"components.os.keyword",
                                                         "size":5,
                                                         "shard_size":100
                                                     }
                                                 }
                                             }
                                         }
                                     }
                                 }
                                 )
            took = aggs["took"]
            country_list = []
            total = aggs.get("hits",{}).get("total",0)
            domain_exist = aggs.get("aggregations",{}).get("domain_exist",{}).get("doc_count",0)
            empty_domain = aggs.get("aggregations",{}).get("empty_domain",{}).get("doc_count",0)
            website = domain_exist - empty_domain
            device = total - website
            for bucket in aggs["aggregations"]["location"]["buckets"]:
                country_code_list = bucket.get("country_code",{}).get("buckets",[])
                if len(country_code_list)>0:
                    country_code = (country_code_list[0].get("key","")).lower()
                else:
                    country_code = ""
                province_list = []
                for province_bucket in bucket.get("province",{}).get("buckets",[]):
                    province_dict = {
                        "name":province_bucket.get("key",""),
                        "value":__query__.group(province_bucket.get("doc_count",0)),
                    }
                    province_list.append(province_dict)
                country_dict = {
                    "name":bucket.get("key",""),
                    "value":__query__.group(bucket.get("doc_count",0)),
                    "country_code":country_code,
                    "province_list":province_list
                }
                country_list.append(country_dict)
            port_list = []
            for bucket in aggs["aggregations"]["port"]["buckets"]:
                port_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                port_list.append(port_dict)
            protocol_list = []
            for bucket in aggs["aggregations"]["protocol"]["buckets"]:
                protocol_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                protocol_list.append(protocol_dict)
            tag_list = []
            for bucket in aggs["aggregations"]["tags"]["buckets"]:
                tag_dict = {
                    "name":bucket["key"],
                    "value":bucket["doc_count"]
                }
                tag_list.append(tag_dict)
            server_list = []
            for bucket in aggs["aggregations"]["components"]["server"]["buckets"]:
                server_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                server_list.append(server_dict)
            os_list = []
            for bucket in aggs["aggregations"]["components"]["os"]["buckets"]:
                os_dict = {
                    "name":bucket["key"],
                    "value":__query__.group(bucket["doc_count"])
                }
                os_list.append(os_dict)
            content = {
                "took":took,
                "port_list":port_list,
                "protocol_list":protocol_list,
                "tag_list":tag_list,
                "server_list":server_list,
                "os_list":os_list,
                "country_list":country_list,
                "website":__query__.group(website),
                "device":__query__.group(device)
            }
            return HttpResponse(json.dumps(content))
    except:
        content = {
            "took":'',
            "port_list":[],
            "protocol_list":[],
            "server_list":[],
            "os_list":[],
            "country_list":[],
            "website":0,
            "device":0
        }
        return HttpResponse(json.dumps(content))

def page(request):
    try:
        search_type = request.GET.get("search_type","")
        search_content = request.GET.get("q","")
        page = int(request.GET.get("page",1))
        if page <= 1000:
            if search_type !="advanced":
                query = __query__.get_query(search_content.strip(" "))
                try:
                    res = client.search(index=index,
                                        doc_type=index_type,
                                        body={
                                            "from":(page-1)*10,
                                            "size":10,
                                            "sort":[
                                                {
                                                    "timestamp":{
                                                        "order":"desc"
                                                    }
                                                }
                                            ],
                                            "query":query
                                        }
                                        )
                    total = res["hits"]["total"]
                    took_time = res["took"]
                    page_nums = int(total / 10) + 1 if (total % 10) > 0 else int(total / 10)
                    page_list = [
                        i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
                    ]
                    hits = []
                    for hit in res["hits"]["hits"]:
                        source = hit["_source"]
                        data = source.get("data",{})
                        if data:
                            pass
                        else:
                            data = {}
                        title = cgi.escape(data.get("title",""))
                        location = source.get("location",{})
                        country = location.get("country","")
                        country_code = (location.get("country_code","")).lower()
                        city = location.get("city","")
                        icp = cgi.escape(data.get("icp",""))
                        headers = data.get("headers",{})
                        banner = data.get("banner",{})
                        domain = source.get("domain","")
                        data_content = data
                        if country:
                            pass
                        else:
                            country = ""
                        if city:
                            pass
                        else:
                            city = ""
                        if title:
                            pass
                        else:
                            title = ""
                        timestamp = source.get("timestamp","")
                        if timestamp != "":
                            timestamp = timestamp.split(" ")[0]
                        if headers != {}:
                            data = json.dumps(headers,indent=4)
                        elif banner != {}:
                            data = json.dumps(banner,indent=4)
                        else:
                            data = json.dumps(data_content,indent=4)
                        if data == "{}":
                            data = ""
                        hit_dict={
                            "id":hit["_id"],
                            "ip":source.get("ip",""),
                            "title":title,
                            "icp":icp,
                            "port":source.get("port",""),
                            "protocol":source.get("protocol",""),
                            "tags":source.get("tags",[]),
                            "data":data,
                            "domain":domain,
                            "timestamp":timestamp,
                            "country":country,
                            "country_code":country_code,
                            "city":city
                        }
                        hits.append(hit_dict)
                    content = {
                        "hits":hits,
                        "count":__query__.group(total),
                        "search_content":search_content,
                        "page_nums":page_nums,
                        "page_list":page_list,
                        "current_page":page,
                        "last_page":page-1,
                        "next_page":page+1,
                        "took_time":took_time,
                        "search_type":search_type,
                        "success":True
                    }
                    return HttpResponse(json.dumps(content))
                except Exception as e:
                    print str(e)
                    content = {
                        "msg":"查询失败，请检查参数是否正确！",
                        "success":False
                    }
                    return HttpResponse(json.dumps(content))
            else:
                ip = request.GET.get("ip","")
                port = request.GET.get("port","")
                protocol = request.GET.get("protocol","")
                os = request.GET.get("os","")
                tags = request.GET.get("tags","")
                domain = request.GET.get("domain","")
                search_content = ""
                if ip != "":
                    search_content += "ip=\""+ip+"\""
                else:
                    pass
                if port != "":
                    if search_content != "":
                        search_content += " AND port=\""+port+"\""
                    else:
                        search_content += "port=\""+port+"\""
                else:
                    pass
                if protocol != "":
                    if search_content != "":
                        search_content += " AND protocol=\""+protocol+"\""
                    else:
                        search_content += "protocol=\""+protocol+"\""
                else:
                    pass
                if os != "":
                    if search_content != "":
                        search_content += " AND os=\""+os+"\""
                    else:
                        search_content += "os=\""+os+"\""
                else:
                    pass
                if tags != "":
                    if search_content != "":
                        search_content += " AND tags=\""+tags+"\""
                    else:
                        search_content += "tags=\""+tags+"\""
                else:
                    pass
                if domain != "":
                    if search_content != "":
                        search_content += " AND domain=\""+domain+"\""
                    else:
                        search_content += "domain=\""+domain+"\""
                else:
                    pass
                query = __query__.get_query(search_content)
                try:
                    res = client.search(index=index,
                                        doc_type=index_type,
                                        body={
                                            "from":(page-1)*10,
                                            "size":10,
                                            "query":query
                                        }
                                        )
                    total = res["hits"]["total"]
                    took_time = res["took"]
                    page_nums = int(total / 10) + 1 if (total % 10) > 0 else int(total / 10)
                    page_list = [
                        i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
                    ]
                    hits = []
                    for hit in res["hits"]["hits"]:
                        source = hit["_source"]
                        data = source.get("data",{})
                        if data:
                            pass
                        else:
                            data = {}
                        title = cgi.escape(data.get("title",""))
                        icp = cgi.escape(data.get("icp",""))
                        location = source.get("location",{})
                        country = location.get("country","")
                        country_code = (location.get("country_code","")).lower()
                        city = location.get("city","")
                        headers = data.get("headers",{})
                        banner = data.get("banner",{})
                        data_content = data
                        timestamp = source.get("timestamp","")
                        if timestamp != "":
                            timestamp = timestamp.split(" ")[0]
                        if headers != {}:
                            data = json.dumps(headers,indent=4)
                        elif banner != {}:
                            data = json.dumps(banner,indent=4)
                        else:
                            data = json.dumps(data_content,indent=4)
                        if data == "{}":
                            data = ""
                        domain = source.get("domain","")
                        hit_dict={
                            "id":hit["_id"],
                            "ip":source.get("ip",""),
                            "title":title,
                            "icp":icp,
                            "port":source.get("port",""),
                            "protocol":source.get("protocol",""),
                            "data":data,
                            "domain":domain,
                            "timestamp":timestamp,
                            "country":country,
                            "country_code":country_code,
                            "city":city
                        }
                        hits.append(hit_dict)
                    content = {
                        "hits":hits,
                        "count":__query__.group(total),
                        "search_content":search_content,
                        "page_nums":page_nums,
                        "page_list":page_list,
                        "current_page":page,
                        "last_page":page-1,
                        "next_page":page+1,
                        "took_time":took_time,
                        "search_type":search_type,
                        "success":True
                    }
                    return HttpResponse(json.dumps(content))
                except Exception as e:
                    content = {
                        "msg":"查询失败，请检查参数是否正确！",
                        "success":False
                    }
                    return HttpResponse(json.dumps(content))
        else:
            content = {
                "success":False,
                "msg":"当前模式只能显示前1w条数据，如需查看更多数据，请联系开发人员！"
            }
            return HttpResponse(json.dumps(content,ensure_ascii=False))
    except Exception as e:
        print str(e)
        return HttpResponse("参数格式错误！")


def get_host_content(request):
    id = request.GET.get("id","")
    try:
        res = client.get(index=index,
                         doc_type=index_type,
                         id=id
                         )
        data = res.get("_source",{}).get("data",{})
        if data:
            pass
        else:
            data = {}
        body = data.get("body","")
        content = {
            "body":body,
            "success":True
        }
        return HttpResponse(json.dumps(content))
    except Exception as e:
        print str(e)
        content = {
            "body":"数据查询失败"
        }
        return HttpResponse(json.dumps(content))


def download(request):
    if request.method == "GET":
        search_content = request.GET.get('q', '')
        return render(request,"search/export.html",{
            "search_content":search_content
        })
    elif request.method == "POST":
        search_content = request.POST.get("q","")
        fields_list = request.POST.getlist("export_fields",[])
        query = __query__.get_query(search_content)
        response = client.search(index=index,
                                 doc_type=index_type,
                                 body={
                                     "size": 10000,
                                     "sort":[
                                         {
                                             "timestamp":{
                                                 "order":"desc"
                                             }
                                         }
                                     ],
                                     "_source":fields_list,
                                     "query":query
                                 }
                                 )
        filename = "result.csv"
        the_file_name = "files\\"+filename
        f = codecs.open(the_file_name,"w",'utf-8-sig')
        writer = csv.writer(f)
        asset_list = []
        row_list = []
        i = 0
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            list1 = []
            i += 1
            if i == 1:
                if "ip" in fields_list:
                    ip = source.get("ip","")
                    list1.append(ip)
                    row_list.append("主机")
                if "domain" in fields_list:
                    domain = source.get("domain","")
                    list1.append(domain)
                    row_list.append("域名")
                if "data.title" in fields_list:
                    title = source.get("data",{}).get("title","")
                    list1.append(title)
                    row_list.append("标题")
                if "port" in fields_list:
                    port = source.get("port","")
                    list1.append(port)
                    row_list.append("端口")
                if "protocol" in fields_list:
                    protocol = source.get("protocol","")
                    list1.append(protocol)
                    row_list.append("服务")
                if "tags" in fields_list:
                    tags = source.get("tags","")
                    list1.append(__query__.get_str_from_list(tags))
                    row_list.append("组件")
                if "location.country" in fields_list:
                    country = source.get("location",{}).get("country","")
                    list1.append(country)
                    row_list.append("国家")
                if "location.province" in fields_list:
                    province = source.get("location",{}).get("province","")
                    list1.append(province)
                    row_list.append("省份/地区")
                if "location.city" in fields_list:
                    city = source.get("location",{}).get("city","")
                    list1.append(city)
                    row_list.append("城市")
                if "timestamp" in fields_list:
                    timestamp = source.get("timestamp","")
                    list1.append(timestamp)
                    row_list.append("更新时间")
                if "data.icp" in fields_list:
                    icp = source.get("data",{}).get("icp","")
                    if icp != "":
                        list1.append("是")
                        list1.append(icp)
                    else:
                        list1.append("否")
                        list1.append(icp)
                    row_list.append("是否备案")
                    row_list.append("备案信息")
            else:
                if "ip" in fields_list:
                    ip = source.get("ip","")
                    list1.append(ip)
                if "domain" in fields_list:
                    domain = source.get("domain","")
                    list1.append(domain)
                if "data.title" in fields_list:
                    title = source.get("data",{}).get("title","")
                    list1.append(title)
                if "port" in fields_list:
                    port = source.get("port","")
                    list1.append(port)
                if "protocol" in fields_list:
                    protocol = source.get("protocol","")
                    list1.append(protocol)
                if "tags" in fields_list:
                    tags = source.get("tags","")
                    list1.append(__query__.get_str_from_list(tags))
                if "location.country" in fields_list:
                    country = source.get("location",{}).get("country","")
                    list1.append(country)
                if "location.province" in fields_list:
                    province = source.get("location",{}).get("province","")
                    list1.append(province)
                if "location.city" in fields_list:
                    city = source.get("location",{}).get("city","")
                    list1.append(city)
                if "timestamp" in fields_list:
                    timestamp = source.get("timestamp","")
                    list1.append(timestamp)
                if "data.icp" in fields_list:
                    icp = source.get("data",{}).get("icp","")
                    if icp != "":
                        list1.append("是")
                        list1.append(icp)
                    else:
                        list1.append("否")
                        list1.append(icp)
            asset_list.append(list1)
        writer.writerow(row_list)
        writer.writerows(asset_list)
        f.close()
        def file_iterator(file_name, chunk_size=512):
            with open(file_name) as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        break
        res = StreamingHttpResponse(file_iterator(the_file_name))
        out_filename = "result.csv"
        res['Content-Type'] = 'application/octet-stream'
        res['Content-Disposition'] = 'attachment;filename=%s' % out_filename
        return res
    else:
        return HttpResponse("请求方法错误！")








