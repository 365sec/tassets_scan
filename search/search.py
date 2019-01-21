# coding:utf-8

from django.shortcuts import render,HttpResponse
from .. import conf_list,query_dsl

client = conf_list.client
d01_index = conf_list.ipv4_index
d01_type = conf_list.ipv4_type
__query__ = query_dsl.Query()

def search(request):
    try:
        res = client.search(index=d01_index,
                            doc_type=d01_type,
                            body={
                                "size": 0,
                                "aggs": {
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
                                    "max_time":{
                                        "max": {
                                            "field": "timestamp"
                                        }
                                    }
                                }
                            }
                            )
    except Exception as e:
        print str(e)
    datetime = res.get("aggregations",{}).get("max_time",{}).get("value_as_string","")
    total = res.get("hits",{}).get("total",0)
    domain_exist = res.get("aggregations",{}).get("domain_exist",{}).get("doc_count",0)
    empty_domain = res.get("aggregations",{}).get("empty_domain",{}).get("doc_count",0)
    website = domain_exist - empty_domain
    device = total - website
    return render(request,'search/search.html',{
        "website":__query__.group(website),
        "device":__query__.group(device),
        "datetime":datetime
    })





















