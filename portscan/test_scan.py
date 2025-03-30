from scan import Portscan

def test_portscan():
    ip_list = "157.0.30.0/24"
    port_list = "80,443,8080,10000-10010"
    scanner = Portscan(ip_str=ip_list, port_str=port_list, timeout=1, threads=100)
    
    # 直接运行扫描
    scanner.run_scan()
    
    # 打印扫描结果
    results = scanner.get_results()
    print(f"扫描结果: {results}")
    print(f"结果数量: {len(results)}")

if __name__ == "__main__":
    test_portscan()
