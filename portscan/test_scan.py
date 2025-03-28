from scan import Portscan

def test_portscan():
    ip_list = "157.0.30.78"
    port_list = "80,443,8080"
    scanner = Portscan(ip_list=ip_list, port_list=port_list, timeout=1, threads=10)
    scanner.run()
    for result in scanner.results:
        print(result)

if __name__ == "__main__":
    test_portscan()
