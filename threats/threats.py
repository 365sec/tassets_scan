# -*- coding:utf-8 -*-

from django.shortcuts import render,HttpResponse
from django.http import StreamingHttpResponse
from .. import conf_list,query_dsl
import json
import datetime
import codecs
import csv
import os
import cgi
import time
import requests

__query__ = query_dsl.Query()
vuln_index = conf_list.vuln_index
vuln_type = conf_list.vuln_type
client = conf_list.client
ip_exp = conf_list.ip_exp
threat_page_num = conf_list.threat_page_num
level_dict = {
    "0":"低危",
    "1":"中危",
    "2":"高危",
    "3":"严重"
}


def get_days_dict():
    today = (datetime.date.today()).strftime("%Y-%m-%d")
    date_week_before = (datetime.date.today()-datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    date_month_before = (datetime.date.today()-datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    date_year_before = (datetime.date.today()-datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    days_dict = {
        "today":today,
        "date_week_before":date_week_before,
        "date_month_before":date_month_before,
        "date_year_before":date_year_before
    }
    print days_dict
    return days_dict

def get_date_query(time_select):
    if time_select != "":
        from_time = time_select+" 00:00:00"
        query = {
            "range":{
                "timestamp":{
                    "gte":from_time
                }
            }
        }
    else:
        query = {}
    return query

def get_search_content(name,ip,level,domain,province,city):
    search_content = ""
    level = level_dict.get(level,"")
    if name != "":
        search_content = "name = "+name
    else:
        pass
    if ip != "":
        if search_content!= "":
            search_content += " AND ip="+ip
        else:
            search_content += "ip="+ip
    else:
        pass
    if level != "":
        if search_content!= "":
            search_content += " AND risk="+level
        else:
            search_content += "risk="+level
    else:
        pass
    if domain != "":
        if search_content!= "":
            search_content += " AND domain="+domain
        else:
            search_content += "domain="+domain
    else:
        pass
    if province != "":
        if search_content!= "":
            search_content += " AND province="+province
        else:
            search_content += "province="+province
    else:
        pass
    if city != "":
        if search_content!= "":
            search_content += " AND city="+city
        else:
            search_content += "city="+city
    else:
        pass
    return search_content



@conf_list.ip_check
def threats(request):
    name = request.GET.get("name","")
    ip = request.GET.get("asset_ip","")
    discover_time = request.GET.get("discover_time","")
    level = request.GET.get("level","")
    domain = request.GET.get("domain","")
    province = request.GET.get("province","")
    city = request.GET.get("city","")
    time_query = get_date_query(discover_time)
    page = int(request.GET.get("page",1))
    from_num = (page-1)*threat_page_num
    search_content = get_search_content(name,ip,level,domain,province,city)
    query_dict = __query__.get_query(search_content)
    res = client.search(index=vuln_index,
                        doc_type=vuln_type,
                        body={
                            "from":from_num,
                            "size":threat_page_num,
                            "query":{
                                "bool":{
                                    "must":[
                                        query_dict,
                                        time_query
                                    ]
                                }
                            },
                            "sort":[
                                {
                                    "timestamp":{
                                        "order":"desc"
                                    }
                                }
                            ]
                        }
                        )
    total = res["hits"]["total"]
    page_nums = int(total/threat_page_num)+1 if (total%threat_page_num)>0 else int(total/threat_page_num)
    page_list = [
        i for i in range(page-4,page+5)if 0<i<=page_nums
    ]
    hits = []
    for hit in res["hits"]["hits"]:
        source = hit["_source"]
        hit_dict = {
            "id":hit["_id"],
            "name":source.get("name",""),
            "ip":source.get("ip",""),
            "url":source.get("URL",""),
            "vuln_type":source.get("vulType",""),
            "risk":source.get("risk",""),
            "protocol":source.get("protocol",""),
            "timestamp":source.get("timestamp",""),
            "domain":source.get("domain","")
        }
        hits.append(hit_dict)
    days_dict = get_days_dict()
    return render(request,'threats/threats.html',{
        "hits":hits,
        "total":total,
        "page_nums":page_nums,
        "page_list":page_list,
        "current_page":page,
        "next_page":page+1,
        "last_page":page-1,
        "asset_ip":ip,
        "name":name,
        "domain":domain,
        "province":province,
        "city":city,
        "days_dict":days_dict,
        "discover_time":discover_time,
        "level":level,
        "search_content":search_content
    })

def export(request):
    if request.method == "GET":
        search_content = request.GET.get("q","")
        discover_time = request.GET.get("discover_time","")
        return render(request,"threats/export.html",{
            "search_content":search_content,
            "discover_time":discover_time
        })
    elif request.method == "POST":
        search_content = request.POST.get("q","")
        discover_time = request.POST.get("discover_time","")
        time_query = get_date_query(discover_time)
        query_dict = __query__.get_query(search_content)
        fields_list = request.POST.getlist("export_fields",[])
        res = client.search(index=vuln_index,
                            doc_type=vuln_type,
                            body={
                                "size":10000,
                                "sort":[
                                    {
                                        "timestamp":{
                                            "order":"desc"
                                        }
                                    }
                                ],
                                "_source":fields_list,
                                "query":{
                                    "bool":{
                                        "must":[
                                            query_dict,
                                            time_query
                                        ]
                                    }
                                }
                            }
                            )
        filename = "threats.csv"
        the_file_name = "files\\"+filename
        f = codecs.open(the_file_name,"w",'utf-8-sig')
        writer = csv.writer(f)
        asset_list = []
        row_list = []
        i = 0
        for hit in res["hits"]["hits"]:
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
                if "port" in fields_list:
                    port = source.get("port","")
                    list1.append(port)
                    row_list.append("端口")
                if "protocol" in fields_list:
                    protocol = source.get("protocol","")
                    list1.append(protocol)
                    row_list.append("服务")
                if "name" in fields_list:
                    name = source.get("name","")
                    list1.append(name)
                    row_list.append("漏洞名称")
                if "cve" in fields_list:
                    cve = source.get("cve",[])
                    list1.append(__query__.get_str_from_list(cve))
                    row_list.append("CVE编号")
                if "vulType" in fields_list:
                    vulType = source.get("vulType","")
                    list1.append(vulType)
                    row_list.append("漏洞类型")
                if "risk" in fields_list:
                    risk = source.get("risk","")
                    list1.append(risk)
                    row_list.append("漏洞等级")
                if "URL" in fields_list:
                    URL = source.get("URL","")
                    list1.append(URL)
                    row_list.append("风险地址")
                if "timestamp" in fields_list:
                    timestamp = source.get("timestamp","")
                    list1.append(timestamp)
                    row_list.append("时间")
                if "describe" in fields_list:
                    describe = source.get("describe","")
                    list1.append(describe)
                    row_list.append("描述")
                if "harm" in fields_list:
                    harm = source.get("harm","")
                    list1.append(harm)
                    row_list.append("危害")
                if "solution" in fields_list:
                    solution = source.get("solution","")
                    list1.append(solution)
                    row_list.append("解决方案")
            else:
                if "ip" in fields_list:
                    ip = source.get("ip","")
                    list1.append(ip)
                if "domain" in fields_list:
                    domain = source.get("domain","")
                    list1.append(domain)
                if "port" in fields_list:
                    port = source.get("port","")
                    list1.append(port)
                if "protocol" in fields_list:
                    protocol = source.get("protocol","")
                    list1.append(protocol)
                if "name" in fields_list:
                    name = source.get("name","")
                    list1.append(name)
                if "cve" in fields_list:
                    cve = source.get("cve",[])
                    list1.append(__query__.get_str_from_list(cve))
                if "vulType" in fields_list:
                    vulType = source.get("vulType","")
                    list1.append(vulType)
                if "risk" in fields_list:
                    risk = source.get("risk","")
                    list1.append(risk)
                if "URL" in fields_list:
                    URL = source.get("URL","")
                    list1.append(URL)
                if "timestamp" in fields_list:
                    timestamp = source.get("timestamp","")
                    list1.append(timestamp)
                if "describe" in fields_list:
                    describe = source.get("describe","")
                    list1.append(describe)
                if "harm" in fields_list:
                    harm = source.get("harm","")
                    list1.append(harm)
                if "solution" in fields_list:
                    solution = source.get("solution","")
                    list1.append(solution)
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
        out_filename = "threats.csv"
        res['Content-Type'] = 'application/octet-stream'
        res['Content-Disposition'] = 'attachment;filename=%s' % out_filename
        return res
    else:
        return HttpResponse("请求方法错误！")


def detail(request):
    id = request.GET.get("id","")
    try:
        res = client.get(index=vuln_index,
                         doc_type = vuln_type,
                         id=id
                         )
        hit = res["_source"]
        solution = hit.get("solution","")
        cve_list = hit.get("cve",[])
        cve = ",".join(cve_list)
        hit["cve"] = cve
        line_list = solution.split("\n")
        status = 0
        solution_list = []
        for line in line_list:
            inner_code = 0
            if "</" in line:
                status = 0
                code_status = 1
            elif "<" in line:
                status = 1
                code_status = 1
            else:
                if status == 1:
                    code_status = 1
                    inner_code = 1
                    i = 0
                    while line[i].isspace():
                        i=i+1
                    else:
                        replace_str=line[0:i].replace(' ','&nbsp;')
                        line=replace_str+line[i:]
                else:
                    code_status = 0
            content_dict = {
                "code_status":code_status,
                "inner_code":inner_code,
                "line":line
            }
            solution_list.append(content_dict)
        return render(request,'threats/detail.html',{
            "hit":hit,
            "solution_list":solution_list
        })
    except Exception as e:
        print str(e)
        return HttpResponse("访问出错")

def get_vuls(request):
    try:
        q = request.GET.get("q","")
        search_content = "name.keyword:/.*%s.*/" % q
        res = client.search(index=vuln_index,
                            doc_type=vuln_type,
                            body={
                                "size":0,
                                "query":{
                                    "query_string":{
                                        "query":search_content
                                    }
                                },
                                "aggs": {
                                    "name": {
                                        "terms": {
                                            "field": "name.keyword",
                                            "size": 1000,
                                            "shard_size":1000
                                        }
                                    }
                                }
                            }
                            )
        hits = []
        for bucket in res["aggregations"]["name"]["buckets"]:
            name = bucket.get("key","")
            hits.append(name)
        content = {
            "success":True,
            "list": hits
        }
        return HttpResponse(json.dumps(content,ensure_ascii=False))
    except Exception,e:
        print str(e)
        content = {
            "success":False
        }
        return HttpResponse(json.dumps(content,ensure_ascii=False))


        # sql = "SELECT NAME FROM POC WHERE NAME LIKE '%s'" % content
        # result = __query__.run_sql(pool,sql,"result")
        # hits = []
        # for row in result:
        #     hits.append(row[0])
        # content = {
        #     "success":True,
        #     "list":hits
        # }
        # return HttpResponse(json.dumps(content,ensure_ascii=False))


def exp_info(request):
    try:
        id = request.GET.get("id","")
        res = client.get(index=vuln_index,
                         doc_type=vuln_type,
                         id=id
                         )
        source = res["_source"]
        return render(request,'threats/exp_info.html',{
            "hit":source,
            "id":id
        })
    except Exception,e:
        print str(e)
        return HttpResponse("查询出错，请检查数据库状态！")


def poc_exp(request):
    url = request.POST.get("url","")
    if url == "":
        content = {
            "success":False,
            "msg":"参数错误"
        }
    else:
        try:
            requests.get(url,timeout=10,verify=False)
            content = {
                "success":True
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"页面无法访问!"
            }
    return HttpResponse(json.dumps(content,ensure_ascii=False))

def poc_vertify_progress(request):
    url = request.POST.get("url","")
    if url == "":
        content = {
            "success":False,
            "fresh":True,
            "msg":"参数错误"
        }
    else:
        try:
            response = requests.get(url,timeout=10,verify=False)
            code = response.status_code
            html = cgi.escape(response.text)
            content = {
                "success":True,
                "output":html,
                "fresh":False,
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"页面无法访问"
            }
    return HttpResponse(json.dumps(content,ensure_ascii=False))


def clear(request):
    if request.method == "POST":
        try:
            clear_type = request.POST.get("type","")
            if clear_type == "batch":
                id_list = request.POST.getlist("ids[]",[])
                if id_list == []:
                    status = {
                        "success":False,
                        "msg":"id不能为空！"
                    }
                else:
                    client.delete_by_query(
                        index=vuln_index,
                        doc_type=vuln_type,
                        body={
                            "query":{
                                "terms":{
                                    "_id":id_list
                                }
                            }
                        }
                    )
                    time.sleep(1)
                    status = {
                        "success":True
                    }
            else:
                es_host = ",".join(conf_list.es_hosts)
                cmd = 'td01_vuln_clear -s \'%s\'' % es_host
                content = os.popen(cmd).read().rstrip()
                status_dict = json.loads(content)
                content = status_dict.get("td01_vuln_clear","")
                if content == "ok":
                    status = {
                        "success":True
                    }
                else:
                    status = {
                        "success":False,
                        "msg":content
                    }
        except Exception,e:
            print str(e)
            status = {
                "success":False,
                "msg":str(e)
            }
        return HttpResponse(json.dumps(status))


