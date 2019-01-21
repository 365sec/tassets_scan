# coding:utf-8

from django.shortcuts import render,HttpResponse
from django import http
import os
from .. import conf_list
import codecs
import json

scan_settings_path = conf_list.scan_settings_path
network_settings_path = conf_list.network_settings_path
fgap_settings_path = conf_list.fgap_settings_path
port_dict = conf_list.port_dict
client = conf_list.client
port_group_index = conf_list.port_group_index
port_group_type = conf_list.port_group_type

def settings(request):
    if request.method == "GET":
        try:
            scan_f = codecs.open(scan_settings_path,"r",encoding="utf-8")#扫描配置
            scan_content = scan_f.read()
            scan_f.close()
            conf_json = json.loads(scan_content)
            network_f = codecs.open(network_settings_path,"r",encoding="utf-8")#网络设置
            network_content = network_f.read()
            network_f.close()
            network_conf = json.loads(network_content)
            nic1_name = network_conf.get("NIC1","")#获取网卡1的名称
            content = os.popen('td01_netconfig_query -i '+nic1_name).read().rstrip()
            network_dict = json.loads(content.replace("'","\""))
            network_query_status = network_dict.get("td01_netconfig_query","error")
            nic2_dict = network_conf.get("NIC2",{})
            if network_query_status == "ok":
                network_conf_dict = network_dict.get("info",{})
                conf_json = dict(conf_json,**network_conf_dict)
                conf_json["nic2_conf"] = nic2_dict
                conf_json["network_status"] = "true"
            else:
                conf_json["nic2_conf"] = nic2_dict
                conf_json["network_status"] = "true"
            status = "true"
        except Exception as e:
            print str(e)
            conf_json = {}
            conf_json["network_status"] = "false"
            status = "false"
        return render(request,'scan/settings.html',{
            "conf":conf_json,
            "status":status
        })
    elif request.method == "POST":
        return HttpResponse("")

def scan_settings(request):
    if request.method == "GET":
        try:
            scan_f = codecs.open(scan_settings_path,"r",encoding="utf-8")#扫描配置
            scan_content = scan_f.read()
            scan_f.close()
            conf_json = json.loads(scan_content)
            selected_id = conf_json.get("port_template","")
            res = client.search(index=port_group_index,
                                doc_type=port_group_type,
                                body={
                                    "_source":["id","name"],
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
            hits = []
            for hit in res["hits"]["hits"]:
                source = hit["_source"]
                id = hit["_id"]
                hit_dict = {
                    "id":id,
                    "name":source.get("name","")
                }
                if id == selected_id:
                    hit_dict["selected"] = "1"
                hits.append(hit_dict)
        except Exception as e:
            print str(e)
            conf_json = {}
            hits = []
        return render(request,'scan/scan_settings.html',{
            "conf":conf_json,
            "hits":hits
        })
    elif request.method == "POST":
        try:
            port_template = request.POST.get("port_template","")
            packet_frequency = request.POST.get("packet_frequency","6000")
            assetscantimes = request.POST.get("assetscantimes","7")
            scan_vuln = request.POST.get("scan_vuln","true")
            res = client.get(index=port_group_index,
                             doc_type=port_group_type,
                             id=port_template
                             )
            port_list = res["_source"].get("ports",[])
            conf_json = {
                "port_template":port_template,
                "port_list" :port_list,
                "packet_frequency" :packet_frequency,
                "assetscantimes": assetscantimes,
                "scan_vuln":scan_vuln
            }
            f = codecs.open(scan_settings_path,"w",encoding="utf-8")
            f.write(json.dumps(conf_json))
            f.close()
            content = os.popen("td01_reconfig -c '/td01/scan_settings.json'").read().rstrip()
            status_dict = json.loads(content)
            td01_reconfig = status_dict.get("td01_reconfig","")
            if td01_reconfig == "ok":
                content = {
                    "success":True,
                    "msg":"扫描设置保存成功"
                }
            else:
                content = {
                    "success":False,
                    "msg":td01_reconfig
                }
        except Exception as e:
            print str(e)
            content = {
                "success":False,
                "msg":"扫描设置保存失败"
            }
        return HttpResponse(json.dumps(content))
    else:
        return HttpResponse("")

def network_settings(request):
    if request.method == "GET":
        try:
            network_f = codecs.open(network_settings_path,"r",encoding="utf-8")#网络设置
            network_content = network_f.read()
            network_f.close()
            network_conf = json.loads(network_content)
            nic1_name = network_conf.get("NIC1","")#获取网卡1的名称
            content = os.popen('td01_netconfig_query -i '+nic1_name).read().rstrip()
            network_dict = json.loads(content.replace("'","\""))
            network_query_status = network_dict.get("td01_netconfig_query","error")
            nic2_dict = network_conf.get("NIC2",{})
            if network_query_status == "ok":
                conf_json = network_dict.get("info",{})
                conf_json["nic2_conf"] = nic2_dict
                conf_json["network_status"] = "true"
            else:
                conf_json = {}
                conf_json["nic2_conf"] = nic2_dict
                conf_json["network_status"] = "true"
            status = "true"
        except Exception as e:
            print str(e)
            conf_json = {}
            conf_json["network_status"] = "false"
            status = "false"
        return render(request,'scan/network_settings.html',{
            "conf":conf_json,
            "status":status
        })
    elif request.method == "POST":
        try:
            addr = request.POST.get("addr","")
            mask = request.POST.get("mask","")
            getway = request.POST.get("getway","")
            dns1 = request.POST.get("dns1","")
            dns2 = request.POST.get("dns2","")
            network_f = codecs.open(network_settings_path,"r",encoding="utf-8")#网络设置
            network_content = network_f.read()
            network_f.close()
            network_conf = json.loads(network_content)
            nic1_name = network_conf.get("NIC1","")
            cmd = "td01_netconfig_set -i %s -a %s -m %s -g %s -d %s -b %s"%(nic1_name,addr,mask,getway,dns1,dns2)
            content = os.popen(cmd).read().strip()
            status_dict = json.loads(content.replace("'","\""))
            status = status_dict.get("td01_netconfig_set","error")
            if status == "ok":
                content = {
                    "success":True,
                    "msg":"网络设置保存成功"
                }
            else:
                content = {
                    "success":False,
                    "msg":status
                }
        except Exception as e:
            print str(e)
            content = {
                "success":False,
                "msg":"网络设置保存失败"
            }
        return HttpResponse(json.dumps(content))
    else:
        return HttpResponse("")



def fgap_settings(request):
    if request.method == "GET":
        try:
            fgap_f = codecs.open(fgap_settings_path,"r",encoding="utf-8")
            fgap_content = fgap_f.read()
            fgap_f.close()
            conf_json = json.loads(fgap_content)
        except Exception,e:
            print str(e)
            conf_json = {}
        return render(request,"scan/fgap_settings.html",{
            "conf":conf_json
        })
    elif request.method == "POST":
        try:
            ftp_ip = request.POST.get("ftp_ip","")
            ftp_port = int(request.POST.get("ftp_port",""))
            ftp_username = request.POST.get("ftp_username","")
            ftp_pwd = request.POST.get("ftp_pwd","")
            enable = request.POST.get("enable",False)
            if enable == "false":
                enable = False
            elif enable == "true":
                enable = True
            conf_dict = {
                "ftp_ip":ftp_ip,
                "ftp_port":ftp_port,
                "ftp_username":ftp_username,
                "ftp_pwd":ftp_pwd,
                "enable":enable,
            }
            f = codecs.open(fgap_settings_path,"w",encoding="utf-8")
            f.write(json.dumps(conf_dict))
            f.close()
            cmd = "td01_reset_out_ftp"
            content = os.popen(cmd).read().strip()
            status_dict = json.loads(content.replace("'","\""))
            status = status_dict.get("td01_reset_out_ftp","")
            if status == "ok":
                content = {
                    "success":True
                }
            else:
                content = {
                    "success":False,
                    "msg":status
                }
        except Exception,e:
            print str(e)
            content = {
                "success":False,
                "msg":"光闸设置保存失败"
            }
        return HttpResponse(json.dumps(content,ensure_ascii=False))




