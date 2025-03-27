from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Asset, Port

def index(request):
    return render(request, 'index.html')

def search(request):
    ip = request.GET.get('ip')
    port = request.GET.get('port')
    service = request.GET.get('service')
    banner = request.GET.get('banner')
    selected_ip = request.GET.get('selected_ip')

    assets = Asset.objects.all()
    ports = Port.objects.all()

    if ip:
        assets = assets.filter(ip__icontains=ip)
        ports = ports.filter(asset__ip__icontains=ip)
    if port:
        ports = ports.filter(port__icontains=port)
    if service:
        ports = ports.filter(service__icontains=service)
    if banner:
        ports = ports.filter(banner__icontains=banner)

    # 添加分页功能
    asset_paginator = Paginator(assets, 10)
    port_paginator = Paginator(ports, 10)

    asset_page_number = request.GET.get('asset_page')
    port_page_number = request.GET.get('port_page')

    asset_page_obj = asset_paginator.get_page(asset_page_number)
    port_page_obj = port_paginator.get_page(port_page_number)

    # 获取选中IP的端口信息
    selected_ports = Port.objects.filter(asset__ip=selected_ip) if selected_ip else None

    return render(request, 'index.html', {
        'asset_page_obj': asset_page_obj,
        'port_page_obj': port_page_obj,
        'selected_ip': selected_ip,
        'selected_ports': selected_ports
    })

