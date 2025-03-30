import eventlet
from port_scan import port_scan
from concurrent.futures import ThreadPoolExecutor
import ipaddress
from queue import Queue, Empty
import threading
import json
import os
import tempfile
import uuid

eventlet.monkey_patch(socket=True, time=True)

class Portscan:
    def __init__(self, ip_str, port_str, timeout=1, threads=100):
        self.ip_list = self.parse_ip_list(ip_str)
        self.port_list =self.parse_port_list(port_str)
        self.timeout = timeout
        self.threads = threads
        self.results = []
        self.lock = threading.Lock()
        self.stop_flag = False  # 新增停止标志位
        self.temp_dir = tempfile.mkdtemp()  # 创建临时目录
        self.batch_size = 100  # 每批次写入的结果数量

    def parse_ip_list(self, ip_str):
        ip_list = []
        for part in ip_str.split(','):
            part = part.strip()
            if '/' in part:  # CIDR notation
                network = ipaddress.ip_network(part, strict=False)
                ip_list.extend([str(ip) for ip in network.hosts()])
            elif '-' in part:  # Range notation
                start_ip, end_ip = part.split('-')
                start_ip = ipaddress.IPv4Address(start_ip.strip())
                end_ip = ipaddress.IPv4Address(end_ip.strip())
                ip_list.extend([str(ip) for ip in range(int(start_ip), int(end_ip) + 1)])
            else:
                ip_list.append(part)
        return ip_list

    def parse_port_list(self, port_str):
        port_list = []
        for part in port_str.split(','):
            part = part.strip()
            if '-' in part:
                start_port, end_port = part.split('-')
                start_port = int(start_port.strip())
                end_port = int(end_port.strip())
                port_list.extend(range(start_port, end_port + 1))
            else:
                port_list.append(int(part.strip()))
        return port_list

    def run_scan(self):
        """生成者消费者模式"""
        queue = Queue()

        def producer():
            for ip in self.ip_list:
                for port in self.port_list:
                    if self.stop_flag:  # 检查停止标志位
                        return
                    queue.put((ip, port))
            # 放入若干个 None, None 作为哨兵
            for _ in range(self.threads):
                queue.put((None, None))

        def consumer():
            batch = []
            while True:
                if self.stop_flag:  # 检查停止标志位
                    break
                ip_port = queue.get()
                if ip_port == (None, None):
                    if batch:  # 写入剩余的批次
                        self._write_batch_to_file(batch)
                        batch = []
                    queue.task_done()
                    break
                ip, port = ip_port
                result = port_scan(ip, port, self.timeout)
                if result['status'] == 'Opened':
                    batch.append(result)
                if len(batch) >= self.batch_size:  # 达到批次大小时写入文件
                    self._write_batch_to_file(batch)
                    batch = []
                queue.task_done()
            if batch:  # 写入剩余的批次
                self._write_batch_to_file(batch)

        with ThreadPoolExecutor(max_workers=self.threads + 1) as executor:
            executor.submit(producer)
            for _ in range(self.threads):
                executor.submit(consumer)
        queue.join()
        return self.get_results()

    def _write_batch_to_file(self, batch):
        """将结果批次写入唯一命名的临时文件"""
        unique_filename = f"results_{uuid.uuid4().hex}.json"  # 使用 UUID 生成唯一文件名
        file_path = os.path.join(self.temp_dir, unique_filename)
        with open(file_path, 'w') as f:
            json.dump(batch, f)

    def get_results(self):
        """从临时文件中读取结果并返回 JSON 格式数据"""
        results = []
        for file_name in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file_name)
            with open(file_path, 'r') as f:
                results.extend(json.load(f))
        return results

    def stop(self):
        """设置停止标志位"""
        self.stop_flag = True