#coding:utf-8

from django.shortcuts import render,HttpResponse
from .. import conf_list,query_dsl
from django import http
import datetime
import json
import time
import os
import re
import threading
import uuid
import requests
import cgi
from contextlib import closing

id = conf_list.system_id
status_path = conf_list.status_path
update_path = conf_list.update_path


def get_mac_address():
    mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])


class update():

    def __init__(self):
        self.progress = 0
        self.download_status = True
        self.install_progress = 0
        self.install_status = True

    def compare_versions(self,request):
        if request.method == "GET":
            f = open(status_path,'r')
            content = json.loads(f.read())
            f.close()
            upgrade_url = content.get("upgrade_url","")
            version = content.get("version","")
            url = "%s/version/compare?version=%s&id=%s" % (upgrade_url,version,id)
            res = requests.get(url,timeout=10,verify=False)
            html = cgi.escape(res.text)
            status = json.loads(html)
            is_update = status.get("is_update",0)
            success = status.get("success",False)
            try:
                content = os.popen('td01_status').read().rstrip()
                status_dict = json.loads(content.replace("'","\""))
                scan_status = status_dict.get("status","STOP")
            except:
                scan_status = "STOP"
            if scan_status == "RUNING":
                content = {
                    "success":True,
                    "state":0,
                    "msg":"正在扫描资产中，无法获取升级状态！",
                    "version":""
                }
            else:
                if success:
                    if is_update == 1:
                        version = status.get("version","")
                        content = {
                            "success":True,
                            "state":1,
                            "msg":"",
                            "version":version
                        }
                    elif is_update == 0 :
                        content = {
                            "success":True,
                            "state":0,
                            "msg":"版本还没有更新，请耐心等待！",
                            "version":""
                        }
                    else:
                        content = {
                            "success":False,
                            "state":0,
                            "msg":"更新状态获取失败！",
                            "version":""
                        }
                else:
                    content = {
                        "success":False,
                        "state":0,
                        "msg":status.get("msg",""),
                        "version":"1.1"
                    }
            return HttpResponse(json.dumps(content,ensure_ascii=False))

    def get_file(self,version,url,filename):
        """
        下载文件，并记录下载进度等内容
        :param url:
        :param filename:
        :return:
        """
        try:
            self.download_status = True
            with closing(requests.get(url,stream=True)) as response:
                chunk_size = 1024
                content_size = int(response.headers['Content-Length'])
                content_disposition = response.headers['Content-Disposition']
                reg = re.search('filename=(?P<filename>[^\s]*)',content_disposition)
                if reg:
                    filename = reg.group("filename")
                data_count = 0
                with open(update_path+filename,"wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        data_count = data_count + len(data)
                        self.progress = (data_count / content_size) * 100
            self.progress = 100
            time.sleep(1)
            try:
                self.install_progress = 0
                content = os.popen('td01_install_pkt -i '+update_path+filename).read().rstrip()
                print content
                status_dict = json.loads(content)
                td01_install_pkt = status_dict.get("td01_install_pkt","")
                if td01_install_pkt == "ok":
                    self.version = version
                    self.install_status = 2
                else:
                    self.install_status = 3
                    print td01_install_pkt
            except Exception,e:
                print "install failure!"
                print str(e)
                self.install_status = 3
        except Exception,e:
            print str(e)
            self.download_status = False


    def download_progress(self,request):
        content = {
            "success":self.download_status,
            "progress":str(self.progress)
        }
        return HttpResponse(json.dumps(content,ensure_ascii=False))





    def download_file(self,request):
        if request.method == "GET":
            version = request.GET.get("version","")
            try:
                f = open(status_path,"rb")
                statud_dict = json.loads(f.read())
                f.close()
                url = statud_dict.get("upgrade_url","")
                get_file_url = "%s/version/get_file?version=%s&id=%s" % (url,version,id)
                filename = "%s.zip" % version
                # r = requests.get(get_file_url)
                # with open(filename,"wb") as code:
                #     code.write(r.content)
                t = threading.Thread(target=self.get_file,args=(version,get_file_url,filename))
                t.start()
                content = {
                    "success":True
                }
            except Exception,e:
                print str(e)
                content = {
                    "success":False,
                    "msg":"下载失败！"
                }
            return HttpResponse(json.dumps(content,ensure_ascii=False))

    def get_upgrade_status(self,request):
        status = str(self.install_status)
        progress = "100" if self.install_status == 2 else "0"
        content = {
            "status": status,
            "progress": progress,
            "failure":""
        }
        if progress == "100":
            try:
                print self.version
                f = open(status_path,"rb")
                statud_dict = json.loads(f.read())
                f.close()
                statud_dict["version"] = self.version
                fw = open(status_path,"wb")
                fw.write(json.dumps(statud_dict,ensure_ascii=False))
                fw.close()
            except Exception,e:
                print str(e)
        return HttpResponse(json.dumps(content))