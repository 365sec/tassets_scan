# -*- coding:utf-8 -*-

import json
import re
import conf_list
import datetime
import time


class Query():

    def __init__(self):
        self.parentheses="()"
        self.field = "_all"
        self.field_dict = {
            "country" : "location.country",
            "province" : "location.province",
            "city" : "location.city",
            "asset_province":"province",
            "asset_city":"city",
            "title" : "data.title",
            "组件" : "component",
            "开发语言":"language",
            "Web应用":"cms",
            "端口协议":"protocols",
            "body":"data.body",
            "asset_os":"os"
        }
        self.field_dict = json.loads(json.dumps(self.field_dict))
        self.replace_dict = {}

    def get_time_stamp(self):
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%dT%H:%M:%S", local_time)
        data_secs = (ct - long(ct)) * 1000
        time_stamp = "%s.%03d" % (data_head, data_secs)
        return time_stamp

    def get_str_from_list(self,value_list,symbol=","):#列表值提取转字符串
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

    def group(self,n, sep = ','):   #对数字，进行千位分割
        s = str(abs(n))[::-1]
        groups = []
        i = 0
        while i < len(s):
            groups.append(s[i:i+3])
            i+=3
        retval = sep.join(groups)[::-1]
        if n < 0:
            return '-%s' % retval
        else:
            return retval

    def remove_mark(self,value):
        reg = re.match('\"(?P<content>.*)\"',value)
        if reg:
            return reg.group('content')
        else:
            return value

    def get_inner_query(self,content):
        content = content.replace("("," ")
        content = content.replace(")"," ")
        rep_dict = self.replace_dict.get("rep_dict",{})
        rep_value_list = rep_dict.keys()
        if "=" in content:
            reg2 = re.compile(r'\s*=\s*')
            content_list = reg2.split(content)
            field = content_list[0]
            value = content_list[1]
            if value in rep_value_list:
                value = rep_dict[value].get("inner_content","")
            else:
                value = self.remove_mark(value)
            if field == "language":
                query = {
                    "nested":{
                        "path":"language",
                        "query":{
                            "match_phrase":{
                                "language.product":value
                            }
                        }
                    }
                }
            elif field == "cms":
                query = {
                    "nested":{
                        "path":"cms",
                        "query":{
                            "match_phrase":{
                                "cms.name":value
                            }
                        }
                    }
                }
            elif field == "component":
                query = {
                    "nested":{
                        "path":"component",
                        "query":{
                            "exists":{
                                "field":"component."+value
                            }
                        }
                    }
                }
            elif field == "os":
                query = {
                    "nested":{
                        "path":"components",
                        "query":{
                            "match_phrase":{
                                "components.os":value
                            }
                        }
                    }
                }
            elif field == "server":
                query = {
                    "nested":{
                        "path":"components",
                        "query":{
                            "match_phrase":{
                                "components.description":value
                            }
                        }
                    }
                }
            elif field == "type":
                if value == "device":#domain不存在或者为空
                    query = {
                        "bool":{
                            "should":[
                                {
                                    "term":{
                                        "domain.keyword":""
                                    }
                                },
                                {
                                    "bool":{
                                        "must_not":[
                                            {
                                                "exists":{
                                                    "field":"domain"
                                                }
                                            }
                                        ],
                                    }
                                }
                            ]
                        }
                    }
                elif value == "website":#domain存在且不为空
                    query = {
                        "bool":{
                            "must":[
                                {
                                    "exists":{
                                        "field":"domain"
                                    }
                                }
                            ],
                            "must_not":[
                                {
                                    "term":{
                                        "domain.keyword":""
                                    }
                                }
                            ]
                        }
                    }
                else:
                    query = {
                        "match_phrase":{
                            field:value
                        }
                    }
            else:
                if field in self.field_dict:
                    field = self.field_dict[field]
                query = {
                    "match_phrase":{
                        field:value
                    }
                }
        elif content!="":
            if content in rep_value_list:
                content = rep_dict[content].get("inner_content","")
            else:
                pass
            query={
                "match_phrase":{
                    self.field:content
                }
            }
        else:
            query={
                "match_all":{}
            }
        return query

    def get_query_with_time(self, query,time_field,time_select,start_time="",end_time=""):
        if time_select == "today":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h/d"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_1m":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h-1m"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_15m":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h-15m"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_1h":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+7h"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_6h":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+2h"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_12h":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now-4h"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_1d":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h-1d"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_3d":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h-3d"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_7d":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h-7d"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "recent_1month":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:{
                                    "gt":"now+8h-1M"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "custom":
            if start_time == "":
                if end_time == "":
                    return query
                else:
                    time_dict = {
                        "lt":end_time
                    }
            elif end_time == "":
                time_dict = {
                    "gt":start_time
                }
            else:
                time_dict = {
                    "gt":start_time,
                    "lt":end_time
                }
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                time_field:time_dict
                            }
                        }
                    ]
                }
            }
        else:
            pass
        return query

    def get_query_with_time_past(self, query,time_select):
        if time_select == "anytime":
            pass
        elif time_select == "past_day":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                "save_time":{
                                    "gt":"now-1d+8h"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "past_week":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                "save_time":{
                                    "gt":"now-1w+8h"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "past_month":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                "save_time":{
                                    "gt":"now-1M+8h"
                                }
                            }
                        }
                    ]
                }
            }
        elif time_select == "past_year":
            query = {
                "bool":{
                    "must":[
                        query,
                        {
                            "range":{
                                "save_time":{
                                    "gt":"now-1y+8h"
                                }
                            }
                        }
                    ]
                }
            }
        else:
            pass
        return query

    def get_query_without_or_and(self,search_content):
        if "NOT" in search_content:
            reg = re.compile(r'\s*NOT\s*')
            search_list = reg.split(search_content)
            i = 1
            must_inner_query = self.get_inner_query(search_list[0])
            must_not_query = []
            while i<len(search_list):
                inner_query = self.get_inner_query(search_list[i])
                must_not_query.append(inner_query)
                i += 1
            query = {
                "bool": {
                    "must": [
                        must_inner_query
                    ],
                    "must_not": must_not_query
                }
            }
        else:
            query = self.get_inner_query(search_content)
        return query



    def get_query_without_or(self,search_content):
        if "AND" in search_content:
            reg = re.compile(r'\s*AND\s*')
            search_list = reg.split(search_content)
            must_query = []
            for content in search_list:
                inner_query = self.get_query_without_or_and(content)
                must_query.append(inner_query)
            query = {
                "bool": {
                    "must": must_query
                }
            }
        else:
            query = self.get_query_without_or_and(search_content)
        return query

    def replace_mark(self,content):
        start_status = 0
        index_dict = {}
        index_list = []
        for i in range(len(content)):
            si = content[i]
            if si == '"':
                if start_status == 0:
                    index_dict["left"] = i
                    start_status = 1
                else:
                    if content[i-1] == '\\':
                        continue
                    else:
                        index_dict["right"] = i
                        index_list.append(index_dict)
                        index_dict = {}
                        start_status =0
            else:
                pass
        rep_dict = {}
        re_content = content
        if len(index_list)>0:
            for j in range(len(index_list)):#判断
                rep_str = content[index_list[j]["left"]:index_list[j]["right"]+1]
                inner_rep_str = content[index_list[j]["left"]+1:index_list[j]["right"]]
                sub_str = "__mark"+str(j)+"__"
                rep_dict[sub_str] = {
                    "content":rep_str,
                    "inner_content":inner_rep_str
                }
                re_content = re_content.replace(rep_str,sub_str)
            dict = {
                "content":re_content,
                "rep_dict":rep_dict
            }
            self.replace_dict = dict
            return re_content
        else:
            return content

    def analysis_content(self,content):
        #通过堆栈解析搜索内容中的括号
        ls = []     #堆栈
        list1 = []  #解析括号的位置内容
        index_dict = {}
        for i in range(len(content)):
            si = content[i]
            if self.parentheses.find(si) == -1: #跳过不是括号的内容
                continue
            else:
                pass
            #左括号入栈
            if si =="(":
                ls.append(si)
                if len(ls)==1:#判断是否是第一个左括号入栈,是的话记录位置
                    index_dict["left"] = i
                continue
            else:
                pass
            try:
                ls.pop()#遇到右括号出栈
            except:
                continue
            if len(ls) == 0:#判断栈是否为空，为空则记录右括号位置,并将括号信息记录写入列表
                index_dict["right"] = i
                list1.append(index_dict)
                index_dict = {}
            else:
                pass
        rep_dict = {} #value存放两个内容，一个是去括号的，一个是包含括号的替换字符串
        re_content = content
        for j in range(len(list1)):#判断
            rep_str = content[list1[j]["left"]:list1[j]["right"]+1]#替换的内容，包括括号
            inner_rep_str = content[list1[j]["left"]+1:list1[j]["right"]]#括号中的内容
            sub_str = "__exp"+str(j)+"__"
            rep_dict[sub_str] = {
                "content":rep_str,
                "inner_content":inner_rep_str
            }
            re_content = re_content.replace(rep_str,sub_str)
        dict = {
            "content":re_content,
            "rep_dict":rep_dict
        }
        return dict

    def get_query(self,search_content):
        if "\"" in search_content:
            search_content = self.replace_mark(search_content)
        else:
            pass
        reg = re.search(r'\((.*)\)',search_content)
        if reg:
            #先对搜索内容进行解析，对外层的括号进行替换，返回替换的内容及替换详情的字典
            content_dict = self.analysis_content(search_content)
            search_content = content_dict["content"]
            print search_content
            rep_dict = content_dict["rep_dict"]
            if "OR" in search_content:
                reg1 = re.compile(r'\s*OR\s*')  # 分割查询语句
                search_list = reg1.split(search_content)
                should_query = []
                for content in search_list:
                    if content in rep_dict.keys():#除去提取的，剩下的内容已经没有括号需要提取了
                        inner_query = self.get_query(rep_dict[content]["inner_content"])
                    else:
                        status = 0
                        for key in rep_dict.keys():#这种方法也有一个问题，就是如果是__exp__1和__exp__11这种
                            if key in content:
                                status = 1
                                rep_key = key
                            else:
                                pass
                        if status ==1:#如果形如(A AND B) AND C OR D，会解析成__exp__1 AND C，需要返回原来的内容进行解析
                            rep_content = content.replace(rep_key,rep_dict[rep_key]["content"])
                            inner_query = self.get_query(rep_content)
                        else:
                            inner_query = self.get_query_without_or(content)
                    should_query.append(inner_query)
                query = {
                    "bool": {
                        "should": should_query
                    }
                }
            elif "AND" in search_content:
                reg1 = re.compile(r'\s*AND\s*')  # 分割查询语句
                search_list = reg1.split(search_content)
                must_query = []
                for content in search_list:
                    if content in rep_dict.keys():
                        inner_query = self.get_query(rep_dict[content]["inner_content"])
                    else:
                        status = 0
                        for key in rep_dict.keys():#这种方法也有一个问题，就是如果是__exp__1和__exp__11这种
                            if key in content:
                                status = 1
                                rep_key = key
                            else:
                                pass
                        if status ==1:#如果形如(A AND B) AND C OR D，会解析成__exp__1 AND C，需要返回原来的内容进行解析
                            rep_content = content.replace(rep_key,rep_dict[rep_key]["content"])
                            inner_query = self.get_query(rep_content)
                        else:
                            inner_query = self.get_query_without_or_and(content)
                    must_query.append(inner_query)
                query = {
                    "bool": {
                        "must": must_query
                    }
                }
            elif "NOT" in search_content:
                reg1 = re.compile(r'\s*NOT\s*')  # 分割查询语句
                search_list = reg1.split(search_content)
                i = 1
                if search_list[0] in rep_dict.keys():
                    must_inner_query = self.get_query(rep_dict[search_list[0]]["inner_content"])
                else:
                    status = 0
                    for key in rep_dict.keys():
                        if key in search_list[0]:
                            status = 1
                            rep_key = key
                        else:
                            pass
                    if status ==1:#如果形如(A AND B) AND C OR D，会解析成__exp__1 AND C，需要返回原来的内容进行解析
                        rep_content = (search_list[0]).replace(rep_key,rep_dict[rep_key]["content"])
                        must_inner_query = self.get_query(rep_content)
                    else:
                        must_inner_query = self.get_inner_query(search_list[0])
                must_not_query = []
                while i<len(search_list):
                    if search_list[i] in rep_dict.keys():
                        inner = self.get_query(rep_dict[search_list[i]]["inner_content"])
                    else:
                        status = 0
                        for key in rep_dict.keys():
                            if key in search_list[i]:
                                status = 1
                                rep_key = key
                            else:
                                pass
                        if status ==1:
                            rep_content = (search_list[i]).replace(rep_key,rep_dict[rep_key]["content"])
                            inner = self.get_query(rep_content)
                        else:
                            inner = self.get_inner_query(search_list[i])
                    must_not_query.append(inner)
                    i +=1
                query = {
                    "bool": {
                        "must": [
                            must_inner_query
                        ],
                        "must_not": must_not_query
                    }
                }
            else:
                if ":" in search_content:
                    reg2 = re.compile(r'\s*:+\s*')
                    content_list = reg2.split(search_content)
                    field = content_list[0]
                    self.field = field
                else:
                    pass
                print rep_dict["__exp0__"]["inner_content"]
                query = self.get_query(rep_dict["__exp0__"]["inner_content"])
        else:
            if "OR" in search_content:
                reg1 = re.compile(r'\s*OR\s*')  # 分割查询语句
                search_list = reg1.split(search_content)
                should_query = []
                for content in search_list:
                    inner_query = self.get_query_without_or(content)
                    should_query.append(inner_query)
                query = {
                    "bool": {
                        "should": should_query
                    }
                }
            else:
                query = self.get_query_without_or(search_content)
        return query







class Asset():
    def __init__(self):
        self.__query__ = Query()
        self.pool = conf_list.pool
        self.ipv4_index = conf_list.ipv4_index
        self.ipv4_type = conf_list.ipv4_type
        self.asset_index = conf_list.asset_index
        self.asset_type = conf_list.asset_type
        self.client = conf_list.client

    def get_asset_count(self):
        res = self.client.search(
            index=self.asset_index,
            doc_type=self.asset_type,
            body={
                "size": 0,
                "aggs": {
                    "new_asset_num": {
                        "date_range": {
                            "field": "datetime",
                            "ranges": [
                                {
                                    "from": "now+8h/d",
                                    "to": "now+8h"
                                }
                            ]
                        }
                    }
                }
            }
        )
        total = res["hits"]["total"]
        new_num = res["aggregations"]["new_asset_num"]["buckets"][0]["doc_count"]
        port_count_sql = "SELECT COUNT(*) FROM SCAN_PORTS"
        port_count_res = self.__query__.run_sql(self.pool,port_count_sql,"result")
        port_count = port_count_res[0][0]
        hit = {
            "total":total,
            "new_num":new_num,
            "port_num":port_count
        }
        return hit

    def get_risk_asset_count(self):
        new_risk_asset_sql = "SELECT COUNT(DISTINCT(ip)) FROM asset_vulnerability WHERE TO_DAYS(DISCOVER_TIME) = TO_DAYS(NOW())"
        new_risk_asset_result = self.__query__.run_sql(self.pool,new_risk_asset_sql,"result")
        new_risk_asset_num = new_risk_asset_result[0][0]
        new_risk_asset_total_sql = "SELECT COUNT(DISTINCT(ip)) FROM asset_vulnerability"
        new_risk_asset_total_result = self.__query__.run_sql(self.pool,new_risk_asset_total_sql,"result")
        new_risk_asset_total = new_risk_asset_total_result[0][0]
        threats_risk_list_sql =  "select p.name,p.level,p.threats_count from poc p where p.threats_count > 0 ORDER BY p.threats_count DESC LIMIT 0,10"
        threats_risk_list_result = self.__query__.run_sql(self.pool,threats_risk_list_sql,"result")
        threats_risk_list = []
        for row in threats_risk_list_result:
            threats_risk_dict = {
                "name":row[0],
                "level":row[1],
                "threats_count":row[2]
            }
            threats_risk_list.append(threats_risk_dict)
        new_risk_asset_list_sql = "SELECT a.ip,a.province,a.city,p.name,a.url FROM asset_vulnerability a,poc p WHERE a.poc_id = p.id order by a.discover_time desc LIMIT 0,10"
        new_risk_asset_list_result = self.__query__.run_sql(self.pool,new_risk_asset_list_sql,"result")
        new_risk_asset_list = []
        for row in new_risk_asset_list_result:
            province = row[1]
            city = row[2]
            if province == None:
                province = ""
            else:
                pass
            if city == None:
                city = ""
            else:
                pass
            new_risk_asset_dict = {
                "ip":row[0],
                "province":province,
                "city":city,
                "name":row[3],
                "url":row[4]
            }
            new_risk_asset_list.append(new_risk_asset_dict)
        risk_asset_area_count_sql = "select city,count(ip) FROM asset_vulnerability GROUP BY city"
        risk_asset_area_count_result = self.__query__.run_sql(self.pool,risk_asset_area_count_sql,"result")
        risk_asset_area_count_name_list = []
        risk_asset_area_count_value_list = []
        for row in risk_asset_area_count_result:
            risk_asset_area_count_name_list.append(row[0])
            risk_asset_area_count_value_list.append(row[1])
        content = {
            "new_risk_asset_num": new_risk_asset_num,
            "new_risk_asset_total": new_risk_asset_total,
            "threats_risk_list": threats_risk_list,
            "new_risk_asset_list":new_risk_asset_list,
            "risk_asset_area_count_name_list":risk_asset_area_count_name_list,
            "risk_asset_area_count_value_list":risk_asset_area_count_value_list
        }
        return content
    def get_str_from_list(self,list,symbol):
        i = 0
        str1 = ""
        while i < len(list):
            str1 += str(list[i])
            i += 1
            if i < len(list):
                str1 += symbol
            else:
                pass
        return str1

    def get_new_asset_list(self):
        res = self.client.search(
            index=self.asset_index,
            doc_type=self.asset_type,
            body={
                "query":{
                    "range":{
                        "datetime":{
                            "from":"now+8h/d",
                            "to":"now+8h"
                        }
                    }
                }
            }
        )
        # new_asset_sql = "SELECT a.IP,a.protocols,a.ports,s.province,s.city FROM ASSET a,SCAN_TASK s WHERE TO_DAYS(a.DATETIME) = TO_DAYS(NOW()) AND a.scan_task = s.id limit 0,10"
        # new_asset_result = self.__query__.run_sql(self.pool,new_asset_sql,"result")
        asset_list = []
        for hit in res["hits"]["hits"]:
            source = hit["_source"]
            ip = source.get("ip","")
            protocols = self.get_str_from_list(source.get("protocols",[]),"/")
            ports = self.get_str_from_list(source.get("ports",[]),"/")
            if source.get("province","") == "" and source.get("province","") == "":
                location = ""
            else:
                location = source.get("province","")+"/"+source.get("city","")
            asset_dict = {
                "ip":ip,
                "protocols":protocols,
                "ports":ports,
                "location":location
            }
            asset_list.append(asset_dict)
        return asset_list

    def get_ports_os_count(self):
        res = self.client.search(index=self.ipv4_index,
                            doc_type=self.ipv4_type,
                            body={
                                "size":0,
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
                                    "components":{
                                        "nested":{
                                            "path":"components"
                                        },
                                        "aggs":{
                                            "os":{
                                                "terms":{
                                                    "field":"components.os.keyword",
                                                    "size":15,
                                                    "shard_size":100
                                                }
                                            }
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
        os_list = []
        for bucket in res["aggregations"]["components"]["os"]["buckets"]:
            os_dict = {
                "name":bucket["key"],
                "value":bucket["doc_count"]
            }
            os_list.append(os_dict)
        count_dict = {
            "port_name_list":port_name_list,
            "port_list":port_list,
            "protocol_name_list":protocol_name_list,
            "protocol_list":protocol_list,
            "os_list":os_list
        }
        return count_dict

    def get_company_location_count(self):
        res = self.client.search(index=self.asset_index,
                                 doc_type=self.asset_type,
                                 body={
                                     "size":0,
                                     "aggs":{
                                         "location":{
                                             "terms":{
                                                 "field":"province.keyword",
                                                 "size":10,
                                                 "shard_size":1000
                                             },
                                             "aggs":{
                                                 "company":{
                                                     "terms":{
                                                         "field":"company.keyword",
                                                         "size":10,
                                                         "shard_size":1000
                                                     }
                                                 }
                                             }
                                         }
                                     }
                                 }
                                 )
        location_list = []
        location_company_list = []
        for bucket in res["aggregations"]["location"]["buckets"]:
            name = bucket["key"]
            if name == "":
                name = "其它"
            else:
                pass
            location_dict = {
                "name":name,
                "value":bucket["doc_count"]
            }
            location_list.append(location_dict)
            for bucket1 in bucket["company"]["buckets"]:
                name1 = bucket1["key"]
                if name1 == "":
                    name1 = "其它"
                else:
                    pass
                location_company_dict = {
                    "name":name1,
                    "value":bucket1["doc_count"]
                }
                location_company_list.append(location_company_dict)
        content = {
            "location_list":location_list,
            "location_company_list":location_company_list
        }
        return content


    def get_count_info(self):
        asset_dict = self.get_asset_count()
        new_asset_list = self.get_new_asset_list()
        ports_os_dict = self.get_ports_os_count()
        count_dict = dict(asset_dict,**ports_os_dict)
        count_dict["new_asset_list"] = new_asset_list
        return count_dict

    def get_nday_list(self,n): #获取最近n天日期
        recent_n_days = []
        for i in range(0, n + 1)[::-1]:
            recent_n_days.append((datetime.date.today() - datetime.timedelta(days=i)).strftime('%m-%d'))
        return recent_n_days



    def get_asset_5day_count(self):
        res = self.client.search(index=self.asset_index,
                                 doc_type=self.asset_type,
                                 body={
                                     "size":0,
                                     "aggs":{
                                         "asset_total_num":{
                                             "date_range": {
                                                 "field": "datetime",
                                                 "format": "MM-dd HH:mm:ss",
                                                 "ranges": [
                                                     {
                                                         "to": "now-4d+8h/s"
                                                     },
                                                     {
                                                         "to": "now-3d+8h/s"
                                                     },
                                                     {
                                                         "to": "now-2d+8h/s"
                                                     },
                                                     {
                                                         "to": "now-1d+8h/s"
                                                     },
                                                     {
                                                         "to": "now+8h/s"
                                                     }
                                                 ]
                                             }
                                         },
                                         "asset_change_num":{
                                             "date_range":{
                                                 "field": "datetime",
                                                 "format": "MM-dd HH:mm:ss",
                                                 "ranges": [
                                                     {
                                                         "from":"now-5d+8h/s",
                                                         "to": "now-4d+8h/s"
                                                     },
                                                     {
                                                         "from":"now-4d+8h/s",
                                                         "to": "now-3d+8h/s"
                                                     },
                                                     {
                                                         "from":"now-3d+8h/s",
                                                         "to": "now-2d+8h/s"
                                                     },
                                                     {
                                                         "from":"now-2d+8h/s",
                                                         "to": "now-1d+8h/s"
                                                     },
                                                     {
                                                         "from":"now-1d+8h/s",
                                                         "to": "now+8h/s"
                                                     }
                                                 ]
                                             }
                                         }
                                     }
                                 }
                                 )
        asset_total_num_list = []
        asset_total_time_list = []
        asset_change_num_list = []
        asset_change_time_list = []
        for bucket in res["aggregations"]["asset_total_num"]["buckets"]:
            asset_total_num_list.append(bucket["doc_count"])
            asset_total_time_list.append(bucket["to_as_string"])
        for bucket1 in res["aggregations"]["asset_change_num"]["buckets"]:
            asset_change_num_list.append(bucket1["doc_count"])
            asset_change_time_list.append(bucket1["to_as_string"])
        content = {
            "asset_total_num_list": asset_total_num_list,
            "asset_total_time_list": asset_total_time_list,
            "asset_change_num_list": asset_change_num_list,
            "asset_change_time_list": asset_change_time_list
        }
        return content


