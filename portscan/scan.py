#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio  # 添加协程模块
import ipaddress  # 添加 IP 地址处理模块
import port_scan

class Portscan:
    def __init__(self, ip_list=None, port_list=None, timeout=1, threads=10):
        # 将输入的字符串转换为列表
        self.ip_list = self.parse_ip_list(ip_list.split(',')) if ip_list else []
        self.port_list = self.parse_port_list(port_list.split(',')) if port_list else []
        self.timeout = timeout
        self.threads = threads
        self.results = []

    def parse_ip_list(self, ip_input):
        """解析 IP 列表，支持 CIDR、范围和单个 IP"""
        for ip in ip_input:
            if '/' in ip:  # CIDR 格式
                try:
                    network = ipaddress.ip_network(ip, strict=False)
                    for host in network.hosts():
                        yield str(host)
                except ValueError:
                    raise ValueError(f"无效的 CIDR 格式: {ip}")
            elif '-' in ip:  # 范围格式
                try:
                    start_ip, end_ip = ip.split('-')
                    start = ipaddress.ip_address(start_ip)
                    end = ipaddress.ip_address(end_ip)
                    if start > end:
                        raise ValueError(f"无效的 IP 范围: {ip}")
                    while start <= end:
                        yield str(start)
                        start += 1
                except ValueError:
                    raise ValueError(f"无效的 IP 范围: {ip}")
            else:  # 单个 IP
                try:
                    yield str(ipaddress.ip_address(ip))
                except ValueError:
                    raise ValueError(f"无效的单个 IP: {ip}")

    def parse_port_list(self, port_input):
        """解析端口列表，支持单个端口和范围"""
        for port in port_input:
            if '-' in port:  # 范围格式
                try:
                    start_port, end_port = map(int, port.split('-'))
                    if start_port > end_port or start_port < 1 or end_port > 65535:
                        raise ValueError(f"无效的端口范围: {port}")
                    for p in range(start_port, end_port + 1):
                        yield p
                except ValueError:
                    raise ValueError(f"无效的端口范围: {port}")
            else:  # 单个端口
                try:
                    port = int(port)
                    if port < 1 or port > 65535:
                        raise ValueError(f"无效的端口: {port}")
                    yield port
                except ValueError:
                    raise ValueError(f"无效的端口: {port}")

    async def portScanner(self, host, port):
        """异步扫描单个IP:PORT"""
        try:
            port_scan_result = await asyncio.to_thread(port_scan.port_scan, host, port, self.timeout)
            if port_scan_result[2] != 'Closed':  # 过滤掉状态为 Closed 的结果
                self.results.append(port_scan_result)
        except Exception:
            pass  # 忽略异常，不添加到结果中

    async def start_scan(self):
        """启动异步扫描"""
        tasks = []
        for ip in self.parse_ip_list(self.ip_list):
            for port in self.parse_port_list(self.port_list):
                tasks.append(self.portScanner(ip, port))
                if len(tasks) >= self.threads:  # 控制并发任务数量
                    await asyncio.gather(*tasks)
                    tasks = []
        if tasks:  # 处理剩余的任务
            await asyncio.gather(*tasks)

    def run(self):
        """运行扫描"""
        asyncio.run(self.start_scan())







