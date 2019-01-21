# -*- coding:utf-8 -*-

from elasticsearch import Elasticsearch
from django.shortcuts import HttpResponse
import os
import json
import re
import ConfigParser
# from pymongo import MongoClient
# import logging
#
# #
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
# fh = logging.FileHandler('../logs/conf.log',mode='a')
# fh.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
# fh.setFormatter(formatter)
# logger.addHandler(fh)

conf = ConfigParser.ConfigParser()
conf.read(os.path.join(os.path.dirname(__file__),"","conf"))
str_es_hosts = conf.get("elasticsearch", "hosts")
es_hosts = json.loads(str_es_hosts)
es_timeout = int(conf.get("elasticsearch", "timeout"))
ipv4_index = conf.get("elasticsearch", "ipv4_index")
ipv4_type = conf.get("elasticsearch", "ipv4_type")
panel_index = conf.get("elasticsearch", "panel_index")
panel_type = conf.get("elasticsearch", "panel_type")
asset_index = conf.get("elasticsearch", "asset_index")
asset_type = conf.get("elasticsearch", "asset_type")
vuln_index = conf.get("elasticsearch", "vuln_index")
vuln_type = conf.get("elasticsearch", "vuln_type")
target_index = conf.get("elasticsearch", "target_index")
target_type = conf.get("elasticsearch", "target_type")
port_index = conf.get("elasticsearch", "port_index")
port_type = conf.get("elasticsearch", "port_type")
port_group_index = conf.get("elasticsearch", "port_group_index")
port_group_type = conf.get("elasticsearch", "port_group_type")
asset_page_num = int(conf.get("search", "asset_page_num"))
poc_page_num = int(conf.get("search", "poc_page_num"))
threat_page_num = int(conf.get("search", "threat_page_num"))
country_terms_num = int(conf.get("search", "country_terms_num"))
province_terms_num = int(conf.get("search", "province_terms_num"))
port_terms_num = int(conf.get("search", "port_terms_num"))
protocol_terms_num = int(conf.get("search", "protocol_terms_num"))
tag_terms_num = int(conf.get("search", "tag_terms_num"))
client = Elasticsearch(hosts=es_hosts,timeout=es_timeout)
mongo_host = conf.get("mongodb", "host")
mongo_port = int(conf.get("mongodb", "port"))
mongo_db = conf.get("mongodb", "db")
mongo_collection = conf.get("mongodb", "collection")
conf_path = conf.get("scan_conf","path")
network_settings_path = conf.get("scan_conf","network_settings_path")
scan_settings_path = conf.get("scan_conf","scan_settings_path")
fgap_settings_path = conf.get("scan_conf","fgap_settings_path")
target_status_path = conf.get("scan_conf","target_status_path")
update_path = conf.get("scan_conf","update_path")
status_path = conf.get("scan_conf","status_path")
port_dict = {
    "1":[21,22,23,25,80,110,137,139,161,443,445,515,1433,1900,3306,3389,6379,7547,8080,9200,22105,37777],
    "2":[21,22,23,25,80,135,137,139,161,443,445,1433,3306,3389,5601],
    "3":[13,21,22,23,25,26,53,69,80,81,88,110,111,123,135,137,139,161,179,389,443,445,465,515,520,623,636,873,902,992,993,995,1433,1521,1604,1701,2181,3306,3307,3388,3389,4730,5060,5601,5672,5900,5984,6000,6379,8080,8081,8087,9200,27017,37777,50000,61613],
    "4":[7,1433,1521,3306,5432,5984,6379,8087,9042,9200,11211,27017,50000],
    "5":[21, 22, 23, 25, 53, 80, 81, 111, 135, 137, 139, 161, 264, 389, 443, 445, 465, 515, 623, 631, 636, 873, 902, 1234, 1241, 1433, 1701, 1900, 1967, 2181, 3000, 3128, 3260, 3306, 3389, 4000, 4730, 5000, 5001, 5353, 5357, 5400, 5555, 5672, 5900, 5938, 6379, 6665, 6666, 6667, 6668, 6669, 7474, 7777, 8000, 8080, 8081, 8089, 8834, 9200, 9999, 10000, 12345, 14000, 22105, 50100, 61613],
    "6":[102, 789, 1200, 1201, 1911, 1962, 2404, 2455, 5006, 5007, 5094, 9600, 18245, 20000, 20574, 30718, 44818, 47808],
    "7":[7,11,13,17,19,21,22,23,25,26,37,49,53,69,70,79,80,81,82,83,84,88,102,110,111,113,119,123,135,137,139,143,161,162,179,195,199,264,389,391,443,444,445,465,500,502,503,515,520,523,548,554,587,623,626,631,636,705,771,789,873,880,902,992,993,995,1025,1026,1027,1080,1099,1177,1200,1201,1234,1241,1311,1433,1471,1521,1604,1701,1723,1833,1883,1900,1911,1962,1967,1991,1993,2000,2080,2082,2083,2086,2087,2094,2121,2181,2222,2323,2332,2375,2376,2404,2455,2480,2628,3000,3128,3260,3306,3307,3359,3388,3389,3541,3542,3689,3749,3780,4000,4022,4040,4063,4064,4070,4369,4443,4534,4567,4730,4800,4848,4911,4949,5000,5001,5006,5007,5009,5060,5094,5222,5269,5353,5357,5400,5432,5434,5555,5560,5601,5602,5632,5672,5678,5683,5900,5901,5938,5984,5985,5986,6000,6001,6379,6664,6665,6666,6667,6668,6669,6982,7001,7071,7077,7288,7474,7547,7548,7777,7779,8000,8001,8008,8009,8010,8060,8069,8080,8081,8086,8087,8089,8090,8098,8099,8112,8139,8161,8200,8333,8334,8443,8554,8649,8834,8880,8888,8889,9000,9003,9010,9042,9080,9191,9200,9307,9418,9443,9595,9600,9944,9981,9999,10000,10243,11211,12345,13579,14000,14147,16010,16992,16993,18245,20000,20574,22105,23023,23424,25105,27015,27017,28017,30718,32400,32768,37777,44818,45554,47808,48899,49152,49153,50000,50070,50100,51106,55553,59110,61613,61616,62078,63389,64738],
    "8":[80,443,554,8554,37777,50100],
    "9":[21,22,23,80,81,137,161,443,445,554,1900,3306,3389,5601,8080,37777,49152],
    "10":[21, 22, 23, 25, 80, 81, 137, 161, 443, 445, 515, 554, 902, 1433, 1900, 3306, 3389, 6379, 8080, 22105, 37777, 49152]
}


ip_exp = "^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(25[0-5]|2[0-4]\d|1\d\d|\d{1,2})(/[0,32])?$"

protocol_list = ["","echo", "systat", "daytime", "qotd", "chargen", "ftp", "ssh", "telnet", "smtp", "rdate", "tacacsplus", "dns", "tftp", "gopher", "finger", "http", "s7", "pop3", "portmap", "nntp", "ntp", "imap", "snmp", "bgp", "ldap", "https", "smtps", "isakmp", "modbus", "lpd", "rip", "rtsp", "serialnumbered", "rsync", "vmware_authentication_daemon", "imaps", "pop3s", "javarmi", "codesys", "mssql", "oracle", "citrixapps", "mqtt", "fox", "pcworx", "ikettle", "proconos", "mysql", "rdp", "moxa", "secure-fox", "melsecq-udp", "melsecq-tcp", "sip", "hartip", "xmpp", "postgres", "amqp", "coap", "vnc", "x11", "redis", "riak", "bitcoin", "gangliaxml", "cassandra", "git", "omron", "memcache", "gesrtp", "dnp3", "mongodb", "lantronixudp", "dahuadvr", "ethernetip", "db2", "idevice", "mumble", "iec-104", "pcanywhere-status", "telnets", "ipmi", "ibm_db2_das", "steam_a2s", "ldaps", "realport", "bacnet", "redlion", "yahoo!smarttv", "vertx-edge", "apple-airport-admin", "mdns", "dictionary", "hifly", "netbios", "vrv", "decrpc", "nbss", "smux", "smb", "ipp", "socks5", "afp", "iscsi", "upnp", "teamviewer", "stomp", "gearman", "zookeeper", "l2tp", "vss", "chat", "directconnect", "shoutcast", "irc", "vtun", "netbus", "rifadvr", "zmtp", "app", "ciscoslaresponder", "fw1topology", "ndmp", "exacqvision", "lexlm", "svnserve", "pptp", "munin", "spark", "insight-manager", "ActiveMQ"]

linux_disk_path = conf.get("system","linux_disk_path")
win_disk_path = conf.get("system","win_disk_path")
system_id = conf.get("system","id")

province_dict = {
    "浙江省": "浙江",
    "北京市": "北京",
    "江苏省": "江苏",
    "山东省": "山东",
    "福建省": "福建",
    "河北省": "河北",
    "湖北省": "湖北",
    "四川省": "四川",
    "黑龙江省": "黑龙江",
    "台湾省": "台湾",
    "广西壮族自治区": "广西",
    "天津市": "天津",
    "内蒙古自治区": "内蒙古",
    "宁夏回族自治区":"宁夏",
    "青海省": "青海",
    "西藏自治区":"西藏"
}
province_dict = json.loads(json.dumps(province_dict,ensure_ascii=False))
#前端省份转换为es中的省份
province_dict_1 = {
    "浙江": "浙江省",
    "北京": "北京市",
    "江苏": "江苏省",
    "山东": "山东省",
    "福建": "福建省",
    "河北": "河北省",
    "湖北": "湖北省",
    "四川": "四川省",
    "黑龙江": "黑龙江省",
    "台湾": "台湾省",
    "广西": "广西壮族自治区",
    "天津": "天津市",
    "内蒙古": "内蒙古自治区",
    "宁夏":"宁夏回族自治区",
    "青海": "青海省",
    "西藏":"西藏自治区"
}
province_dict_1 = json.loads(json.dumps(province_dict_1,ensure_ascii=False))

province_pinyin_dict = {
    "浙江": "zhejiang",
    "北京": "beijing",
    "江苏": "jiangsu",
    "山东": "shandong",
    "福建": "fujian",
    "河北": "hebei",
    "湖北": "hubei",
    "四川": "sichuan",
    "黑龙江": "heilongjiang",
    "台湾": "taiwan",
    "广西": "guangxi",
    "天津": "tianjin",
    "内蒙古": "neimenggu",
    "宁夏":"ningxia",
    "青海": "qinghai",
    "西藏": "xizang",
    "广东": "guangdong",
    "河南": "henan",
    "上海": "shanghai",
    "陕西": "shanxi1",
    "吉林": "jilin",
    "辽宁": "liaoning",
    "山西": "shanxi",
    "重庆": "chongqing",
    "安徽": "anhui",
    "湖南": "hunan",
    "香港": "xianggang",
    "江西": "jiangxi",
    "云南": "yunnan",
    "贵州": "guizhou",
    "新疆": "xinjiang",
    "甘肃": "gansu",
    "海南": "hainan",
    "澳门": "aomen"
}
province_pinyin_dict = json.loads(json.dumps(province_pinyin_dict,ensure_ascii=False))



def ip_check(func):
    def check(*args):
        request = args[0]
        if request.method =="POST":
            return func(*args)
        elif request.method =="GET":
            ip = request.GET.get("asset_ip","")
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