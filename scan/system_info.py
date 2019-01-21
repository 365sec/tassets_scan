# coding:utf-8

from django.shortcuts import render,HttpResponse
import json
import psutil
import socket
import datetime
import math
import os
import platform
from .. import conf_list

system = platform.system()
if system == "Windows":
    disk_path = conf_list.win_disk_path
else:
    disk_path = conf_list.linux_disk_path

def get_rotate_value(num):
    if num > 50:
        return (num-50)/100 *360 -135
    else:
        return num/100 *360 -135

def info(request):
    #一键巡检
    try:
        content = os.popen('td01_inspection').read().rstrip()
        status_dict = json.loads(content.replace("'","\""))
        status_dict["ttag"] = status_dict.get("ttag","")
        status_dict["masscan"] = status_dict.get("masscan","")
        status_dict["tscantarget"] = status_dict.get("tscantarget","")
        status_dict["tgrab"] = status_dict.get("tgrab","")
        status_dict["td01_loader"] = status_dict.get("td01_loader","")
        status_dict["redis_server"] = status_dict.get("redis-server","")
        status_dict["td01_outgoing"] = status_dict.get("td01_outgoing","")
        status_dict["td01_merge"] = status_dict.get("td01_merge","")
        status = 'true'
    except Exception as e:
        print str(e)
        status = 'false'
        status_dict={}
    mem_total = round(float(psutil.virtual_memory().total)/(1024*1024*1024),1)
    mem_used = round(float(psutil.virtual_memory().used)/(1024*1024*1024),1)
    mem_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(0.5)
    disk_total = 0
    disk_used = 0
    disk_dict = {}
    for i in psutil.disk_partitions():
        try:
            device = i.device
            total = int(math.ceil(psutil.disk_usage(i.mountpoint).total/(1024*1024*1024)))
            used = int(math.ceil(psutil.disk_usage(i.mountpoint).used/(1024*1024*1024)))
            percent = psutil.disk_usage(i.mountpoint).percent
            disk_dict[device] = {
                "total":total,
                "used":used,
                "percent":percent
            }
            disk_total += total
            disk_used += used
        except Exception,e:
            print str(e)
    if disk_total != 0:
        disk_percent = float(disk_used*100)/float(disk_total)
    else:
        disk_percent = 0
    myname = socket.getfqdn(socket.gethostname(  ))
    ip = socket.gethostbyname(myname)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if mem_percent>50:
        mem_status = 1
    else:
        mem_status = 0
    if cpu_percent>50:
        cpu_status = 1
    else:
        cpu_status = 0
    if disk_percent>50:
        disk_status = 1
    else:
        disk_status = 0
    return render(request,"scan/system_info.html",{
        "ip":ip,
        "mem":{
            "percent":mem_percent,
            "rotate":get_rotate_value(mem_percent),
            "status":mem_status,
            "used":mem_used,
            "total":mem_total
        },
        "cpu":{
            "percent":cpu_percent,
            "rotate":get_rotate_value(cpu_percent),
            "status":cpu_status
        },
        "disk":{
            "percent":round(disk_percent,1),
            "rotate":get_rotate_value(disk_percent),
            "status":disk_status,
            "total":disk_total,
            "used":disk_used,
            "free":disk_total-disk_used
        },
        "timestamp":timestamp,
        "status":status,
        "result":status_dict
    })


def get_systems(request):
    mem_total = round(float(psutil.virtual_memory().total)/(1024*1024*1024),1)
    mem_used = round(float(psutil.virtual_memory().used)/(1024*1024*1024),1)
    mem_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(0.5)
    disk_total = 0
    disk_used = 0
    disk_dict = {}
    for i in psutil.disk_partitions():
        try:
            device = i.device
            total = int(math.ceil(psutil.disk_usage(i.mountpoint).total/(1024*1024*1024)))
            used = int(math.ceil(psutil.disk_usage(i.mountpoint).used/(1024*1024*1024)))
            percent = psutil.disk_usage(i.mountpoint).percent
            disk_dict[device] = {
                "total":total,
                "used":used,
                "percent":percent
            }
            disk_total += total
            disk_used += used
        except Exception,e:
            print str(e)
    if disk_total != 0:
        disk_percent = float(disk_used*100)/float(disk_total)
    else:
        disk_percent = 0
    sys_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = {
        "mem":mem_percent,
        "cpu":cpu_percent,
        "disk":round(disk_percent,1),
        "sys_time":sys_time,
        "disk_total":disk_total,
        "disk_used":disk_used,
        "mem_total":mem_total,
        "mem_used":mem_used
    }
    return HttpResponse(json.dumps(content,ensure_ascii=False))


