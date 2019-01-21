"""assets_discovery URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from search import search,result
from asset import asset
from threats import threats,pocs
from scan import scan_management,scan_settings,system_info,target,update,system,port
from panels import panels
from report import chart,report

__scan__ = scan_management.Scan()
__update__ = system.update()
__port__ = port.Port()
__portgroup__ = port.PortGroup()

urlpatterns = [
    url(r'^panels$', panels.panels),
    url(r'^panels/get_count_info$', panels.get_count_info),
    url(r'^asset$', asset.asset),
    url(r'^asset/edit$', asset.edit),
    url(r'^asset/delete_index$', asset.delete_index),
    url(r'^asset/export$', asset.export),
    url(r'^asset/export_csv$', asset.download),
    url(r'^asset/get_subdomain_body$', asset.get_subdomain_body),
    url(r'^report$', report.report),
    url(r'^report/new$', report.new),
    url(r'^report/edit$', report.edit),
    url(r'^report/add_chart$', chart.add_chart),
    url(r'^report/chart_delete$', chart.chart_delete),
    url(r'^report/manual_report$', report.manual_report),
    url(r'^report/detail$', report.detail),
    url(r'^report/report_detail$', report.report_detail),
    url(r'^report/delete$', report.delete),
    url(r'^search$', search.search),
    url(r'^result$', result.result, name='search'),
    url(r'^result/download$', result.download),
    url(r'^result/count$', result.count),
    url(r'^result/page$', result.page),
    url(r'^result/get_host_content$', result.get_host_content),
    url(r'^threats$', threats.threats,name='threats'),
    url(r'^threats/detail$', threats.detail),
    url(r'^threats/clear$', threats.clear),
    url(r'^threats/get_vuls$', threats.get_vuls),
    url(r'^threats/exp_info$', threats.exp_info),
    url(r'^threats/poc_exp$', threats.poc_exp),
    url(r'^threats/poc_vertify_progress$', threats.poc_vertify_progress),
    url(r'^threats/export$', threats.export),
    url(r'^pocs$', pocs.pocs),
    url(r'^pocs/scan_start$', pocs.scan_start),
    url(r'^pocs/pocs_scan_status$', pocs.pocs_scan_status),
    url(r'^scancfgs$', __scan__.asset_scan),
    url(r'^scan/get_scan_status$', __scan__.get_scan_status),
    url(r'^scan/start_scan$', __scan__.start_scan),
    url(r'^scan/stop_scan$', __scan__.stop_scan),
    url(r'^network_settings$', scan_settings.network_settings),
    url(r'^scan_settings$', scan_settings.scan_settings),
    url(r'^fgap_settings', scan_settings.fgap_settings),
    url(r'^system_info$', system_info.info),
    url(r'^systems/get_systems$', system_info.get_systems),
    url(r'^port_management$', __port__.port_management),
    url(r'^port_management/new$', __port__.add_port),
    url(r'^port_management/edit$', __port__.edit_port),
    url(r'^port_management/delete$', __port__.delete_port),
    url(r'^port_management/get_port_group$', __port__.get_port_group),
    url(r'^port_group_management$', __portgroup__.port_group_management),
    url(r'^port_group_management/new$', __portgroup__.add_port_group),
    url(r'^port_group_management/edit$', __portgroup__.edit),
    url(r'^port_group_management/delete$', __portgroup__.delete),
    url(r'^port_group_management/get_port$', __portgroup__.get_port),
    url(r'^target_management$', target.management),
    url(r'^target_management/new$', target.new),
    url(r'^target_management/edit$', target.edit),
    url(r'^target_management/delete$', target.delete),
    url(r'^system/update$', update.update),
    url(r'^system/upgrade$', update.upgrade),
    url(r'^system/get_upgrade_status$', __update__.get_upgrade_status),
    url(r'^system/modify_upgrade_url$', update.modify_upgrade_url),
    url(r'^system/compare_versions$', __update__.compare_versions),
    url(r'^system/download_file$', __update__.download_file),
    url(r'^system/download_progress$', __update__.download_progress),
    url(r'^$', panels.panels, name="main")
]
