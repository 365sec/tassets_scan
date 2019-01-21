# -*- coding:utf-8 -*-

from django.shortcuts import render,HttpResponse
from django.http import StreamingHttpResponse
from .. import conf_list,query_dsl
import json
import csv
import codecs
import cgi #转义http、https端口的body内容
import sys
import os
import time
reload(sys)
sys.setdefaultencoding("utf-8")


client = conf_list.client
ipv4_index = conf_list.ipv4_index
index_type = conf_list.ipv4_type
asset_index = conf_list.asset_index
asset_type = conf_list.asset_type
asset_page_num = conf_list.asset_page_num
vuln_index = conf_list.vuln_index
vuln_type = conf_list.vuln_type
__query__ = query_dsl.Query()



def get_content(content):
    code = str(type(content))
    if code == "<type 'unicode'>":
        content = content.encode("utf-8")
    else:
        pass
    return content

def get_advanced_search_content(ip,domain,ports,protocols,os,components,province,city):
    search_content = ""
    if ip != "":
        search_content += "ip=\""+ip+"\""
    else:
        pass
    if domain != "":
        if search_content != "":
            search_content += " AND domain=\""+domain+"\""
        else:
            search_content += "domain=\""+domain+"\""
    else:
        pass
    if ports != "":
        if search_content != "":
            search_content += " AND ports=\""+ports+"\""
        else:
            search_content += "ports=\""+ports+"\""
    else:
        pass
    if protocols != "":
        if search_content != "":
            search_content += " AND protocols=\""+protocols+"\""
        else:
            search_content += "protocols=\""+protocols+"\""
    else:
        pass
    if os != "":
        if search_content != "":
            search_content += " AND asset_os=\""+os+"\""
        else:
            search_content += "asset_os=\""+os+"\""
    else:
        pass
    if components != "":
        if search_content != "":
            search_content += " AND components=\""+components+"\""
        else:
            search_content += "components=\""+components+"\""
    else:
        pass
    if province != "":
        if search_content != "":
            search_content += " AND asset_province=\""+province+"\""
        else:
            search_content += "asset_province=\""+province+"\""
    else:
        pass
    if city != "":
        if search_content != "":
            search_content += " AND asset_city=\""+city+"\""
        else:
            search_content += "asset_city=\""+city+"\""
    else:
        pass
    return search_content

def get_threats_num(ip):
    try:
        res = client.search(
            index=vuln_index,
            doc_type=vuln_type,
            body={
                "size":0,
                "query":{
                    "match_phrase":{
                        "ip":ip
                    }
                }
            }
        )
        num = res["hits"]["total"]
    except Exception as e:
        print str(e)
        num = 0
    return num



def asset(request):
    if request.method == "GET":
        try:
            page = int(request.GET.get("page",1))
            search_type = request.GET.get("search_type","normal")
            if page <= 500:
                if search_type != "advanced":
                    keyword = request.GET.get("keyword","")
                    try:
                        from_num = (page-1)*asset_page_num
                        query = __query__.get_query(keyword)
                        res = client.search(index=asset_index,
                                            doc_type=asset_type,
                                            body={
                                                "from":from_num,
                                                "size":asset_page_num,
                                                "sort":[
                                                    {
                                                        "updated_at":{
                                                            "order":"desc"
                                                        }
                                                    }
                                                ],
                                                "query":query
                                            }
                                            )
                        total = res["hits"]["total"]
                        page_nums = int(total / asset_page_num) + 1 if (total % asset_page_num) > 0 else int(total / asset_page_num)
                        page_list = [
                            i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
                        ]
                        hits = []
                        j = from_num +1
                        for hit in res["hits"]["hits"]:
                            hit_dict = hit["_source"]
                            hit_dict["id"] = hit["_id"]
                            hit_dict["num"] = j
                            j += 1
                            components = hit_dict.get("components",[])
                            hit_dict["components"] = components
                            hits.append(hit_dict)
                        for hit in hits:
                            ip = hit["ip"]
                            port_content_list = []
                            threats_num = 0
                            if ip == "":
                                pass
                            else:
                                threats_num = get_threats_num(ip)
                                res = client.search(index=ipv4_index,
                                                    doc_type=index_type,
                                                    body={
                                                        "query":{
                                                            "match_phrase":{
                                                                "ip":ip
                                                            }
                                                        }
                                                    }
                                                    )
                                for dict1 in res["hits"]["hits"]:
                                    source = dict1["_source"]
                                    data = source.get("data",{})
                                    if data:
                                        pass
                                    else:
                                        data = {}
                                    headers = data.get("headers",{})
                                    banner = data.get("banner",{})
                                    title = data.get("title","")
                                    protocol = source.get("protocol","")
                                    if protocol in ["http","https"]:
                                        status = 1
                                    else:
                                        status = 0
                                    if headers != {}:
                                        data = json.dumps(headers,indent=4)
                                    elif banner != {}:
                                        data = json.dumps(banner,indent=4)
                                    else:
                                        data = json.dumps(data,indent=4)
                                    ip = source.get("domain","") if source.get("domain","") != "" else source.get("ip","")
                                    hit_dict = {
                                        "ip":ip,
                                        "port":source.get("port",""),
                                        "protocol":source.get("protocol",""),
                                        "title":title,
                                        "data":data,
                                        "status":status
                                    }
                                    port_content_list.append(hit_dict)
                            hit["hit_list"] = port_content_list
                            hit["threats_num"] = threats_num
                        return render(request,'asset/asset.html',{
                            "total":total,
                            "hits":hits,
                            "page_nums":page_nums,
                            "current_page":page,
                            "last_page":page-1,
                            "next_page":page+1,
                            "page_list":page_list,
                            "keyword":keyword
                        })
                    except Exception as e:
                        print str(e)
                        return render(request,'asset/asset.html',{
                            "total":0,
                            "hits":[],
                            "page_nums":0,
                            "current_page":page,
                            "last_page":page-1,
                            "next_page":page+1,
                            "page_list":[],
                            "keyword":keyword
                        })
                else:
                    ip = request.GET.get("ip","")
                    domain = request.GET.get("domain","")
                    ports = request.GET.get("ports","")
                    protocols = request.GET.get("protocol","")
                    os = request.GET.get("os","")
                    components = request.GET.get("component","")
                    province = request.GET.get("province","")
                    city = request.GET.get("city","")
                    search_content = get_advanced_search_content(ip,domain,ports,protocols,os,components,province,city)
                    try:
                        from_num = (page-1)*asset_page_num
                        query = __query__.get_query(search_content)
                        res = client.search(index=asset_index,
                                            doc_type=asset_type,
                                            body={
                                                "from":from_num,
                                                "size":asset_page_num,
                                                "query":query
                                            }
                                            )
                        total = res["hits"]["total"]
                        page_nums = int(total / asset_page_num) + 1 if (total % asset_page_num) > 0 else int(total / asset_page_num)
                        page_list = [
                            i for i in range(page - 4, page + 5) if 0 < i <= page_nums  # 分页页码列表
                        ]
                        hits = []
                        j = from_num +1
                        for hit in res["hits"]["hits"]:
                            hit_dict = hit["_source"]
                            hit_dict["id"] = hit["_id"]
                            hit_dict["num"] = j
                            j += 1
                            components = hit_dict.get("components",[])
                            hit_dict["components"] = components
                            hits.append(hit_dict)
                        for hit in hits:
                            ip = hit["ip"]
                            port_content_list = []
                            threats_num = 0
                            if ip == "":
                                pass
                            else:
                                threats_num = get_threats_num(ip)
                                res = client.search(index=ipv4_index,
                                                    doc_type=index_type,
                                                    body={
                                                        "query":{
                                                            "match_phrase":{
                                                                "ip":ip
                                                            }
                                                        }
                                                    }
                                                    )
                                for dict1 in res["hits"]["hits"]:
                                    source = dict1["_source"]
                                    data = source.get("data",{})
                                    if data:
                                        pass
                                    else:
                                        data = {}
                                    headers = data.get("headers",{})
                                    banner = data.get("banner",{})
                                    title = data.get("title","")
                                    protocol = source.get("protocol","")
                                    if protocol in ["http","https"]:
                                        status = 1
                                    else:
                                        status = 0
                                    if headers != {}:
                                        data = json.dumps(headers,indent=4)
                                    elif banner != {}:
                                        data = json.dumps(banner,indent=4)
                                    else:
                                        data = json.dumps(data,indent=4)
                                    hit_dict = {
                                        "ip":source.get("ip",""),
                                        "port":source.get("port",""),
                                        "protocol":source.get("protocol",""),
                                        "title":title,
                                        "data":data,
                                        "status":status
                                    }
                                    port_content_list.append(hit_dict)
                            hit["threats_num"] = threats_num
                            hit["hit_list"] = port_content_list
                        return render(request,'asset/asset.html',{
                            "total":total,
                            "hits":hits,
                            "page_nums":page_nums,
                            "current_page":page,
                            "last_page":page-1,
                            "next_page":page+1,
                            "page_list":page_list,
                            "keyword":search_content
                        })
                    except Exception as e:
                        print str(e)
                        return render(request,'asset/asset.html',{
                            "total":0,
                            "hits":[],
                            "page_nums":0,
                            "current_page":page,
                            "last_page":page-1,
                            "next_page":page+1,
                            "page_list":[],
                            "keyword":search_content
                        })
            else:
                return HttpResponse("当前模式只能查看前1w条数据，如需查看更多数据，请联系开发人员！")
        except Exception as e:
            print str(e)
            return HttpResponse("页码格式错误")
    else:
        pass




def edit(request):
    id = request.GET.get("id","")
    try:
        res = client.get(index=asset_index,
                         doc_type=asset_type,
                         id=id
                         )
        hit = res["_source"]
        protocols = hit.get("protocols",[])
        ports = hit.get("ports",[])
        hit["protocols"] = __query__.get_str_from_list(protocols,",")
        hit["ports"] = __query__.get_str_from_list(ports,",")
        components = hit.get("components",[])
        hit["components"] = components
        ip = hit.get("ip","")
        hits = []
        if ip == "":
            pass
        else:
            res = client.search(index=ipv4_index,
                                doc_type=index_type,
                                body={
                                    "size":100,
                                    "query":{
                                        "match_phrase":{
                                            "ip":ip
                                        }
                                    }
                                }
                                )
            for dict1 in res["hits"]["hits"]:
                source = dict1["_source"]
                data = source.get("data",{})
                if data:
                    pass
                else:
                    data = {}
                headers = data.get("headers",{})
                title = data.get("title","")
                banner = data.get("banner",{})
                protocol = source.get("protocol","")
                if protocol in ["http","https"]:
                    status = 1
                else:
                    status = 0
                if headers != {}:
                    data = json.dumps(headers,indent=4)
                elif banner != {}:
                    data = json.dumps(banner,indent=4)
                else:
                    data = json.dumps(data,indent=4)
                domain = source.get("domain","")
                if domain == "":
                    ip_show = source.get("ip","")
                else:
                    ip_show = domain
                hit_dict = {
                    "ip":ip_show,
                    "port":source.get("port",""),
                    "protocol":source.get("protocol",""),
                    "data":data,
                    "title":title,
                    "status":status
                }
                hits.append(hit_dict)
        return render(request,'asset/edit.html',{
            "hit":hit,
            "hits":hits
        })
    except Exception as e:
        print str(e)
        return render(request,'asset/edit.html',{
            "hit":{},
            "hits":[]
        })



def get_subdomain_body(request):
    if request.method == "GET":
        try:
            ip = request.GET.get("ip","")
            port = request.GET.get("port","")
            type = request.GET.get("type","")
            res = client.search(index=ipv4_index,
                                doc_type=index_type,
                                body={
                                    "query":{
                                        "bool":{
                                            "must":[
                                                {
                                                    "term":{
                                                        "ip.keyword":ip
                                                    }
                                                },
                                                {
                                                    "term":{
                                                        "port":port
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                                )
            data = ""
            for hit in res["hits"]["hits"]:
                data = hit["_source"].get("data",{})
                if data:
                    pass
                else:
                    data = {}
                data = cgi.escape(data.get("body",""))
                break
            content = {
                "body":data
            }
            return HttpResponse(json.dumps(content,ensure_ascii=False))
        except Exception as e:
            print str(e)
            content = {
                "body":""
            }
            return HttpResponse(json.dumps(content,ensure_ascii=False))
    else:
        return HttpResponse("")



def export(request):
    if request.method == "GET":
        keyword = request.GET.get("keyword")
        return render(request,"asset/export.html",{
            "keyword":keyword
        })
    elif request.method == "POST":
        keyword = request.POST.get("keyword","")
        fields_list = request.POST.getlist("export_fields",[])
        query = __query__.get_query(keyword)
        response = client.search(index=asset_index,
                                 doc_type=asset_type,
                                 body={
                                     "size": 10000,
                                     "sort":[
                                         {
                                             "updated_at":{
                                                 "order":"desc"
                                             }
                                         }
                                     ],
                                     "_source":fields_list,
                                     "query":query
                                 }
                                 )
        filename = "asset.csv"
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
                if "ports" in fields_list:
                    ports = source.get("ports","")
                    list1.append(__query__.get_str_from_list(ports))
                    row_list.append("端口")
                if "protocols" in fields_list:
                    protocols = source.get("protocols","")
                    list1.append(__query__.get_str_from_list(protocols))
                    row_list.append("服务")
                if "components" in fields_list:
                    components = source.get("components","")
                    list1.append(__query__.get_str_from_list(components))
                    row_list.append("组件")
                if "os" in fields_list:
                    os = source.get("os","")
                    list1.append(os)
                    row_list.append("操作系统")
                if "province" in fields_list:
                    province = source.get("province","")
                    list1.append(province)
                    row_list.append("省份/地区")
                if "city" in fields_list:
                    city = source.get("city","")
                    list1.append(city)
                    row_list.append("城市")
                if "updated_at" in fields_list:
                    updated_at = source.get("updated_at","")
                    list1.append(updated_at)
                    row_list.append("服务")
            else:
                if "ip" in fields_list:
                    ip = source.get("ip","")
                    list1.append(ip)
                if "domain" in fields_list:
                    domain = source.get("domain","")
                    list1.append(domain)
                if "ports" in fields_list:
                    ports = source.get("ports","")
                    list1.append(__query__.get_str_from_list(ports))
                if "protocols" in fields_list:
                    protocols = source.get("protocols","")
                    list1.append(__query__.get_str_from_list(protocols))
                if "components" in fields_list:
                    components = source.get("components","")
                    list1.append(__query__.get_str_from_list(components))
                if "os" in fields_list:
                    os = source.get("os","")
                    list1.append(os)
                if "province" in fields_list:
                    province = source.get("province","")
                    list1.append(province)
                if "city" in fields_list:
                    city = source.get("city","")
                    list1.append(city)
                if "updated_at" in fields_list:
                    updated_at = source.get("updated_at","")
                    list1.append(updated_at)
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
        out_filename = "asset.csv"
        res['Content-Type'] = 'application/octet-stream'
        res['Content-Disposition'] = 'attachment;filename=%s' % out_filename
        return res
    else:
        return HttpResponse("请求方法错误！")


def download(request):
    if request.method == "GET":
        try:
            search_content = request.GET.get('q', '')
            query = __query__.get_query(search_content)
            response = client.search(index=asset_index,
                                     doc_type=asset_type,
                                     body={
                                         "size": 10000,
                                         "sort":[
                                             {
                                                 "updated_at":{
                                                     "order":"desc"
                                                 }
                                             }
                                         ],
                                         "_source":["ip","domain","province","city","os","ports","protocols","components","updated_at"],
                                         "query":query
                                     }
                                     )
            filename = "asset.csv"
            the_file_name = "files\\"+filename
            f = codecs.open(the_file_name,"w",'utf-8-sig')
            writer = csv.writer(f)
            asset_list = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                ip = source.get("ip","")
                domain = source.get("domain","")
                os = source.get("os","")
                province = source.get("province","")
                city = source.get("city","")
                ports = source.get("ports",[])
                protocols = source.get("protocols",[])
                components = source.get("components",[])
                updated_at = source.get("updated_at","")
                list1 = [ip,domain,__query__.get_str_from_list(ports),__query__.get_str_from_list(protocols),__query__.get_str_from_list(components),os,province,city,updated_at]
                asset_list.append(list1)
            writer.writerow(["主机","域名","端口","服务","组件","系统","省份/区域","城市","更新时间"])
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
            out_filename = "asset.csv"
            res['Content-Type'] = 'application/octet-stream'
            res['Content-Disposition'] = 'attachment;filename=%s' % out_filename
            return res
        except Exception as e:
            print str(e)
            return HttpResponse("下载失败")
    else:
        return HttpResponse("")


def delete_index(request):
    try:
        str_es_hosts = conf_list.str_es_hosts
        str_es_hosts = str_es_hosts.replace("[","\"")
        str_es_hosts = str_es_hosts.replace("]","\"")
        os.popen('td01_clear -s '+str_es_hosts)
        content = {
            "success":True
        }
    except Exception as e:
        content = {
            "success":False,
            "msg":"删除失败"
        }
    return HttpResponse(json.dumps(content,ensure_ascii=False))



