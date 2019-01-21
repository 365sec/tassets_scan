# -*- coding:utf-8 -*-

import sys
sys.path.append("../")
import conf_list

client = conf_list.client

res = client.get(index="d01_vuln",
           doc_type="d01_vuln",
           id="aeeb12638de982e28de5f02bc1a4250f"
           )
content = res["_source"].get("solution")
print content
line_list = content.split("\n")
status = 0
content_list = []
for line in line_list:
    if "</" in line:
        status = 0
        code_status = 1
    elif "<" in line:
        status = 1
        code_status = 1
    else:
        if status == 1:
            code_status = 1
        else:
            code_status = 0
    content_dict = {
        "code_status":code_status,
        "line":line
    }
    content_list.append(content_dict)
