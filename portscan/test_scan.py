from scan import Portscan

def test_portscan():
    ip_list = "157.0.30.0/24"
    port_list = "80,443,8080,10000-10010"
    scanner = Portscan(ip_str=ip_list, port_str=port_list, timeout=1, threads=100)
    print(scanner.run_scan())
    

if __name__ == "__main__":
    test_portscan()
