# coding:utf-8


from django.shortcuts import render,HttpResponse,HttpResponseRedirect
import json
import datetime
import time
import codecs
from .. import conf_list,query_dsl

__query__ = query_dsl.Query()
client = conf_list.client
port_index = conf_list.port_index
port_type = conf_list.port_type
port_group_index = conf_list.port_group_index
port_group_type = conf_list.port_group_type
protocol_list = conf_list.protocol_list
scan_settings_path = conf_list.scan_settings_path
page_size = 15



def get_group_max_id():
    try:
        res = client.search(index=port_group_index,
                            doc_type=port_group_type,
                            body={
                                "size":0,
                                "aggs":{
                                    "max_id":{
                                        "max":{
                                            "field": "id"
                                        }
                                    }
                                }
                            }
                            )
        max_id = res["aggregations"]["max_id"]["value"]
        content = {
            "success":True,
            "max_id":max_id
        }
    except Exception,e:
        print str(e)
        content = {
            "success":False
        }
    return content

def get_group_status(name,id=""):#判断端口名是否冲突
    try:
        if id == "":
            query = {
                "term":{
                    "name.keyword":name
                }
            }
        else:
            query = {
                "bool":{
                    "must":[
                        {
                            "term":{
                                "name.keyword":name
                            }
                        }
                    ],
                    "must_not":[
                        {
                            "term":{
                                "_id":id
                            }
                        }
                    ]
                }
            }
        res = client.search(index=port_group_index,
                            doc_type=port_group_type,
                            body={
                                "size":0,
                                "query":query
                            }
                            )
        total = res["hits"]["total"]
        if total >0:
            return False
        else:
            return True
    except Exception,e:
        print "获取端口组状态失败"
        print str(e)
        return True


def update_scan_settings():
    """
    更新端口组内容至配置文件，
    暂时重新加载配置命令内容未加
    :return:
    """
    try:
        scan_f = codecs.open(scan_settings_path,"r",encoding="utf-8")#扫描配置
        scan_content = scan_f.read()
        scan_f.close()
        conf_json = json.loads(scan_content)
        port_group_id = conf_json.get("port_template")
        res = client.get(index=port_group_index,
                         doc_type=port_group_type,
                         id= port_group_id
                         )
        port_list = res["_source"].get("ports",[])
        new_port_list = []
        for port in port_list:#端口去重后写入配置文件
            if port not in new_port_list:
                new_port_list.append(port)
        conf_json["port_list"] = new_port_list
        f = codecs.open(scan_settings_path,"w",encoding="utf-8")
        f.write(json.dumps(conf_json))
        f.close()
    except Exception,e:
        print "端口配置写入失败"

class Port():
    def port_management(self,request):
        if request.method == "GET":
            try:
                keyword = request.GET.get("keyword","")
                page = int(request.GET.get("page",1))
                query_dict = __query__.get_query(keyword)
                from_num = (page - 1)*page_size
                res = client.search(index=port_index,
                                    doc_type=port_type,
                                    body={
                                        "from":from_num,
                                        "size":page_size,
                                        "query":query_dict,
                                        "sort":{
                                            "id":{
                                                "order":"desc"
                                            }
                                        }
                                    }
                                    )
                total = res["hits"]["total"]
                page_num = int(total/page_size) if total % page_size == 0 else int(total/page_size)+1
                page_list = [
                    i for i in range(page-4,page+5) if 0< i <=page_num
                ]
                hits = []
                for hit in res["hits"]["hits"]:
                    source = hit["_source"]
                    port_group = source.get("port_group",[])
                    if "全部端口" in port_group:
                        port_group.remove("全部端口")
                    hit_dict = {
                        "id" : source.get("id",""),
                        "port" : source.get("port",""),
                        "protocol" : source.get("protocol",""),
                        "way": source.get("way",""),
                        "datetime": source.get("datetime",""),
                        "port_id":hit["_id"],
                        "port_group": ",".join(port_group)
                    }
                    hits.append(hit_dict)
                return render(request,"scan/port/port_management.html",{
                    "keyword":keyword,
                    "total": total,
                    "page_num": page_num,
                    "current_page":page,
                    "last_page":page-1,
                    "next_page":page+1,
                    "page_list":page_list,
                    "hits":hits
                })
            except Exception,e:
                print str(e)
                return render(request,"scan/port/port_management.html",{
                    "keyword":"",
                    "total": 0,
                    "page_num": 0,
                    "current_page":0,
                    "last_page":-1,
                    "next_page":1,
                    "page_list":[],
                    "hits":[]
                })

    def get_port_status(self,port,protocol,id=""):
        try:
            query = {
                "bool":{
                    "must":[
                        {
                            "term":{
                                "port":port
                            }
                        },
                        {
                            "term":{
                                "protocol.keyword":protocol
                            }
                        }
                    ]
                }
            }
            if id == "":
                pass
            else:
                query["bool"]["must_not"] = [
                    {
                        "term":{
                            "_id": id
                        }
                    }
                ]
            res = client.search(
                index=port_index,
                doc_type=port_type,
                body={
                    "query":query
                }
            )
            total = res["hits"]["total"]
            if total >0:
                status = False
            else:
                status = True
        except:
            status = True
        return status

    def get_max_id(self):
        try:
            res = client.search(index=port_index,
                                doc_type=port_type,
                                body={
                                    "size":0,
                                    "aggs":{
                                        "max_id":{
                                            "max":{
                                                "field": "id"
                                            }
                                        }
                                    }
                                }
                                )
            max_id = res["aggregations"]["max_id"]["value"]
            content = {
                "success":True,
                "max_id":max_id
            }
        except Exception,e:
            print str(e)
            content = {
                "success":False
            }
        return content







    def handle_port_group(self,port,port_group,method="add"):
        try:
            if method == "add":
                res = client.search(index=port_group_index,
                                    doc_type=port_group_type,
                                    body={
                                        "size":1,
                                        "query":{
                                            "term":{
                                                "name.keyword":port_group
                                            }
                                        }
                                    }
                                    )
                total = res["hits"]["total"]
                if total>0:#在端口分组ports中新增相应的端口
                    ports = res["hits"]["hits"][0]["_source"].get("ports",[])
                    id = res["hits"]["hits"][0]["_id"]
                    ports.append(int(port))
                    doc = {
                        "ports":sorted(ports)
                    }
                    client.update(index=port_group_index,
                                  doc_type=port_group_type,
                                  id=id,
                                  body={
                                      "doc":doc
                                  }
                                  )
                else:#如果端口分组不存在则新建端口分组
                    content = get_group_max_id()
                    ports = [int(port)]
                    if content.get("success",False):
                        action = {
                                "name":port_group,
                                "ports":ports,
                                "id":int(content.get("max_id",0))+1
                        }
                    else:
                        action = {
                                "name":port_group,
                                "ports":ports
                        }
                    client.index(index=port_group_index,
                                 doc_type=port_group_type,
                                 body=action
                                 )
            else:#删除
                res = client.search(index=port_group_index,
                                    doc_type=port_group_type,
                                    body={
                                        "size":1,
                                        "query":{
                                            "term":{
                                                "name.keyword":port_group
                                            }
                                        }
                                    }
                                    )
                total = res["hits"]["total"]
                if total>0:#在端口分组ports中删除相应的端口
                    ports = res["hits"]["hits"][0]["_source"].get("ports",[])
                    id = res["hits"]["hits"][0]["_id"]
                    ports.remove(int(port))
                    doc = {
                        "ports":sorted(ports)
                    }
                    client.update(index=port_group_index,
                                  doc_type=port_group_type,
                                  id=id,
                                  body={
                                      "doc":doc
                                  }
                                  )
                else:
                    pass
        except Exception,e:
            print str(e)

    def change_port_group_by_port(self,id,port,port_group):
        """
        修改端口的同时修改端口分组内容
        :param id:
        :param port:
        :param port_group:
        :return:
        """
        try:
            res = client.get(index=port_index,
                                doc_type=port_type,
                                id=id
                                )
            source = res["_source"]
            original_port = int(source.get("port",0))
            original_port_group = source.get("port_group",[])
            if original_port == 0 or port == 0:
                content = {
                    "port":port,
                    "success":False,
                    "msg":"端口格式错误"
                }
            else:
                if original_port == int(port):
                    for inner_port_group in port_group:
                        if inner_port_group in original_port_group or inner_port_group == "":
                            pass
                        else:#新增的端口分组
                            self.handle_port_group(port,inner_port_group)
                    for inner_port_group in original_port_group:
                        if inner_port_group in port_group:
                            pass
                        else:#原有的分组被移除，需移除相应端口分组里的端口
                            self.handle_port_group(port,inner_port_group,method="delete")
                else:#端口修改的话，原有端口分组里都需移除该端口
                    for inner_original_port_group in original_port_group:
                        self.handle_port_group(port,inner_original_port_group,method="delete")
                    for inner_port_group in original_port_group:
                        self.handle_port_group(port,inner_port_group,method="add")
        except Exception,e:
            print str(e)

    def handle_port(self,port,protocol,port_group_list,id=""):
        port_status = self.get_port_status(port,protocol,id)
        if port_status:
            if id == "":#新增端口
                max_content = self.get_max_id()
                if max_content.get("success",False):
                    try:
                        id = int(max_content.get("max_id",0)) +1
                        action = {
                            "id":id,
                            "port":port,
                            "protocol":protocol,
                            "port_group":port_group_list,
                            "way":"自定义添加",
                            "all_protocol":0,
                            "datetime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        client.index(index=port_index,
                                     doc_type=port_type,
                                     body=action
                                     )
                        for port_group in port_group_list:#修改相应的端口分组信息
                            if port_group == "":
                                continue
                            self.handle_port_group(port,port_group)
                            self.handle_port_group(port,"全部端口")
                        port_content = {
                            "port": port,
                            "success":True
                        }
                    except Exception,e:
                        port_content = {
                            "port": port,
                            "success":False,
                            "msg":"端口%s添加失败，端口数据入库失败！"%port
                        }
                else:
                    port_content = {
                        "port": port,
                        "success":False,
                        "msg":"端口%s添加失败，获取最大id失败"%port
                    }
            else:#修改端口，同时也要修改相应的端口组的内容
                try:
                    self.change_port_group_by_port(id,port,port_group_list)
                    doc = {
                        "port":port,
                        "protocol":protocol,
                        "port_group":port_group_list,
                        "datetime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    client.update(index=port_index,
                                  doc_type=port_type,
                                  id=id,
                                  body={
                                      "doc":doc
                                  }
                                  )
                    port_content = {
                        "port": port,
                        "success":True
                    }
                except Exception,e:
                    print str(e)
                    port_content = {
                        "port": port,
                        "success":False,
                        "msg":"端口%s修改失败，端口数据入库失败！"%port
                    }
        else:
            port_content = {
                "port": port,
                "success":False,
                "msg":"端口%s添加失败，端口%s已存在"% (port,port)
            }
        return port_content

    def edit_port(self,request):
        if request.method == "GET":
            id = request.GET.get("id","")
            try:
                res = client.get(index=port_index,
                                 doc_type=port_type,
                                 id=id
                                 )
                source = res["_source"]
                port_group = source.get("port_group",[])
                if "" in port_group:
                    port_group.remove("")
                if "全部端口" in port_group:
                    port_group.remove("全部端口")
                hit = {
                    "port" : source.get("port",0),
                    "protocol_list" : protocol_list,
                    "protocol" : source.get("protocol",0),
                    "id": id,
                    "port_group" : ",".join(port_group)
                }
                time.sleep(0.5)
                return render(request,"scan/port/edit_port.html",{
                    "hit": hit
                })
            except Exception,e:
                pass
        elif request.method == "POST":
            try:
                id = request.POST.get("id","")
                port = request.POST.get("port","")
                protocol = request.POST.get("protocol","")
                port_group = request.POST.get("port_group","")
                port_group_list = port_group.split(",")
                status = False
                msg = ""
                port_content = self.handle_port(port,protocol,port_group_list,id=id)
                if port_content.get("success",False):
                    status = True
                else:
                    msg += port_content.get("msg","")+""
                content = {
                    "success":status,
                    "msg":msg
                }
                time.sleep(1)
                update_scan_settings()
                return HttpResponse(json.dumps(content,ensure_ascii=False))
            except Exception,e:
                pass


    def delete_port(self,request):
        """
        删除相应的端口，并移除相应的端口分组中的数据
        :param request:
        :return:
        """
        if request.method == "GET":
            id = request.GET.get("id","")
            try:
                res = client.get(index=port_index,
                                 doc_type=port_type,
                                 id=id
                                 )
                source = res["_source"]
                port = source.get("port",0)
                port_group_list = source.get("port_group",[])
                for port_group in port_group_list:
                    self.handle_port_group(port,port_group,method="delete")
                client.delete(index=port_index,
                              doc_type=port_type,
                              id=id
                              )
                time.sleep(1)
                update_scan_settings()
                return HttpResponseRedirect("../port_management")
            except:
                print "端口删除失败！"
                return HttpResponseRedirect("../port_management")

    def add_port(self,request):
        if request.method == "GET":
            return render(request,"scan/port/new_port.html")
        elif request.method == "POST":
            try:
                str_port = request.POST.get("port","")
                protocol = request.POST.get("protocol","")
                port_group = request.POST.get("port_group","")
                port_group_list = port_group.split(",")
                port_list = str_port.split(",")
                status = False
                msg = ""
                for port in port_list:
                    port_content = self.handle_port(port,protocol,port_group_list)
                    if port_content.get("success",False):
                        status = True
                    else:
                        msg += port_content.get("msg","")+";\n"
                time.sleep(1)
                update_scan_settings() #更新端口组信息至扫描配置
                content = {
                    "success":status,
                    "msg":msg
                }
            except Exception,e:
                print str(e)
                content = {
                    "success":False,
                    "msg":"数据写入失败！"
                }
            return HttpResponse(json.dumps(content,ensure_ascii=False))

    def get_port_group_query(self,q):
        if q == "":
            query = {
                "match_all":{}
            }
        else:
            query = {
                "match":{
                    "name":q
                }
            }
        return query

    def get_port_group(self,request):
        if request.method == "GET":
            q = request.GET.get("q","")
            query_dict = self.get_port_group_query(q)
            res = client.search(
                index=port_group_index,
                doc_type=port_group_type,
                body={
                    "size":1000,
                    "_source":["name"],
                    "query":{
                        "bool":{
                            "must":query_dict,
                            "must_not":{
                                "term":{
                                    "name.keyword":"全部端口"
                                }
                            }
                        }
                    }
                }
            )
            hits = []
            for hit in res["hits"]["hits"]:
                hits.append(hit["_source"].get("name",""))
            content = {
                "list":hits
            }
            return HttpResponse(json.dumps(content,ensure_ascii=False))

class PortGroup():

    def port_group_management(self,request):
        if request.method == "GET":
            try:
                res = client.search(index=port_group_index,
                                    doc_type=port_group_type,
                                    body={
                                        "size":1000,
                                        "sort":[
                                            {
                                                "id":{
                                                    "order":"asc"
                                                }
                                            }
                                        ]
                                    }
                                    )
                total = res["hits"]["total"]
                hits = []
                for hit in res["hits"]["hits"]:
                    source = hit["_source"]
                    ports = source.get("ports",[])
                    new_ports = [str(i) for i in ports]
                    hit_dict = {
                        "port_group_id":hit["_id"],
                        "id":source.get("id",0),
                        "name":source.get("name",""),
                        "ports":",".join(new_ports)
                    }
                    hits.append(hit_dict)
            except Exception,e:
                total = 0
                hits = []
                print str(e)
            return render(request,"scan/port/port_group_management.html",{
                "total":total,
                "hits":hits
            })
    def add_port_group(self,request):
        if request.method == "GET":
            return render(request,"scan/port/new_port_group.html")
        elif request.method == "POST":
            try:
                name = request.POST.get("name","")
                port_group_status = get_group_status(name)
                if port_group_status:
                    ports = request.POST.get("ports","")
                    str_port_list = ports.split(",")
                    port_list = []
                    for str_port in str_port_list:
                        if str_port != "":
                            port_list.append(int(str_port))
                    max_id_content = get_group_max_id()
                    if max_id_content.get("success",False):
                        action = {
                                "name":name,
                                "ports":sorted(port_list),
                                "id":int(max_id_content.get("max_id",0))+1
                        }
                        client.index(index=port_group_index,
                                     doc_type=port_group_type,
                                     body=action
                                     )
                        content = {
                            "success":True
                        }
                    else:
                        content = {
                            "success":False,
                            "msg":"获取端口id失败！"
                        }
                else:
                    content = {
                        "success":False,
                        "msg":"分组名称已被占用！"
                    }
            except Exception,e:
                print str(e)
                content = {
                    "success":False,
                    "msg":"新增端口组失败！"
                }
            return HttpResponse(json.dumps(content,ensure_ascii=False))


    def get_port(self,request):
        if request.method == "GET":
            res = client.search(index=port_index,
                                doc_type=port_type,
                                body={
                                    "size":0,
                                    "aggs":{
                                        "port":{
                                            "terms":{
                                                "field":"port",
                                                "size":100000,
                                                "order": {
                                                    "_term": "asc"
                                                }
                                            }
                                        }
                                    }
                                }
                                )
            port_list = []
            for bucket in res["aggregations"]["port"]["buckets"]:
                port_list.append(bucket["key"])
            content = {
                "list":port_list
            }
            return HttpResponse(json.dumps(content,ensure_ascii=False))

    def delete(self,request):
        if request.method == "GET":
            id = request.GET.get("id","")
            try:
                client.delete(index=port_group_index,
                              doc_type=port_group_type,
                              id= id
                              )
                time.sleep(1)
                return HttpResponseRedirect("../port_group_management")
            except Exception,e:
                print str(e)
                return HttpResponseRedirect("../port_group_management")


    def edit(self,request):
        if request.method == "GET":
            try:
                id = request.GET.get("id","")
                res = client.get(index=port_group_index,
                                 doc_type=port_group_type,
                                 id=id
                                 )
                name = res["_source"].get("name","")
                port_list = res["_source"].get("ports",[])
                str_port_list = []
                for port in port_list:
                    str_port_list.append(str(port))
                str_ports = ",".join(str_port_list)
                return render(request,"scan/port/edit_port_group.html",{
                    "id":id,
                    "name":name,
                    "ports":str_ports
                })
            except Exception,e:
                print str(e)
        elif request.method == "POST":
            id = request.POST.get("id","")
            name = request.POST.get("name","")
            str_ports = request.POST.get("ports","")
            try:
                port_group_status = get_group_status(name,id)
                if port_group_status:
                    str_port_list = str_ports.split(",")
                    port_list = []
                    for str_port in str_port_list:
                        if str_port != "":
                            port_list.append(int(str_port))
                    doc = {
                        "name":name,
                        "ports":sorted(port_list)
                    }
                    client.update(index=port_group_index,
                                  doc_type=port_group_type,
                                  id=id,
                                  body={
                                      "doc":doc
                                  }
                                  )
                    time.sleep(1)
                    update_scan_settings() #更新端口组信息至扫描配置
                    content = {
                        "success":True
                    }
                else:
                    content = {
                        "success":False,
                        "msg":"端口分组名称已存在"
                    }
            except Exception,e:
                print str(e)
                content = {
                    "success":False,
                    "msg":"端口分组编辑失败！"
                }
            return HttpResponse(json.dumps(content,ensure_ascii=False))



