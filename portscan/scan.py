from port_scan import port_scan
from concurrent.futures import ThreadPoolExecutor
import ipaddress
from queue import Queue, Empty
import threading

class Portscan:
    def __init__(self, ip_str, port_str, timeout=1, threads=100):
        self.ip_list = self.parse_ip_list(ip_str)
        self.port_list =self.parse_port_list(port_str)
        self.timeout = timeout
        self.threads = threads
        self.results = []
        self.lock = threading.Lock()

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
                    queue.put((ip, port))
            # 放入若干个 None, None 作为哨兵
            for _ in range(self.threads):
                queue.put((None, None))

        def consumer():
            while True:
                ip_port = queue.get()
                if ip_port == (None, None):
                    queue.task_done()
                    break
                ip, port = ip_port
                result = port_scan(ip, port, self.timeout)
                if result['status'] == 'Opened':
                    with self.lock:
                        self.results.append(result)
                queue.task_done()

        with ThreadPoolExecutor(max_workers=self.threads + 1) as executor:
            executor.submit(producer)
            for _ in range(self.threads):
                executor.submit(consumer)
        queue.join()
        return self.results