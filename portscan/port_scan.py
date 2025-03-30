import random
import re
from random import randint
from socket import *
from scapy.layers.inet import IP,TCP, UDP
import requests
from scapy.sendrecv import sr1, send
import urllib3
import warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=SyntaxWarning)
PROBES =open('probes.txt', 'r').read().splitlines()# 读取探测文件
signs_rules= open('rules.txt', 'r').read().splitlines()# 读取规则文件

def port_scan(host,port=80,timeout=5):
    status='Closed'
    service='Null'
    banner='Null'
    title=''
    port = int(port)
    socket_result = socket_scan(host,port,timeout)
    if socket_result[2] == '1':
        scan_result = scan_service(host, port, timeout)
        service = scan_result[2]
        banner = scan_result[3]
        title = scan_result[4]
        status = 'Opened'
    return {
        'host': host,
        'port': port,
        'status': status,
        'service': service,
    }

#
def scan_service(host,port=80,timeout=5):
    title=''
    return_Data = scanservice(host, port, timeout)
    # host,port,service,Banner
    service = return_Data[2]
    if return_Data[3] != '':
        Banner = return_Data[3]
    else:
        Banner=''
    if service in ['http', 'https', 'HTTP', 'HTTPS']:
        http_result = scan_http(host, port, service, Banner)
        # host, port, service, Banner, title
        service = http_result[2]
        if http_result[3]:
            Banner = http_result[3]
        title = http_result[4]
        # print(title)
    return  host,port,service,Banner,title
def scan_http(host,port,service,Banner):
    try:
        # if service in ['http','HTTP'] and Banner!='':
        #     title = get_title(Banner)
        #     if title:
        #         return host, port, service, Banner, title
        if service == 'https' or service == 'HTTPS':
            url_address = 'https://' + host + ':' + str(port)
        else:
            url_address = 'http://' + host + ':' +  str(port)

        html = requests.get(url_address, verify=False)
        if html.status_code == 400 and 'The plain HTTP request was sent to HTTPS port' in html.text:
            url_address = 'https://' + host + ':' +  str(port)
        html = requests.get(url_address, verify=False)
        if not html:
            html = requests.post(url_address, verify=False)
        html.encoding = html.apparent_encoding
        # html.encoding = html.encoding
        # print(html.apparent_encoding)
        if html.status_code == 404:
            Banner = html.text
            title = "404 Not Found"
        elif html.text:
            Banner = html.text
            # print (html.text)
            title = get_title(Banner)
        else:
            title = '404'
        return host,port,service,Banner,title
            # print (title)
    except Exception as e:
        # print(str(e))
        title = ""
        return host,port,service,Banner,title
def get_title(banner):
    re_data = re.search(r'<title>(.+)</title>', banner, re.I | re.M)
    if re_data:
        title = re_data.group().replace('<title>', '').replace('</title>',
                                                               '').replace(
            '<TITLE>', '').replace('</TITLE>', '')
    # print(html.text)
    elif "404 Not Found" in banner:
        title = "404 Not Found"
    elif "Page Not Found" in banner:
        title = "Page Not Found"
    else:
        title = ''
    return  title
def scapy_tcp_syn_scan(ip,port=80):
    try:
        # print(type(port))
        sport = random.randint(2, 5)
        packet = IP(dst=ip) / TCP(flags="S", sport = sport,dport=port)/B"dadadadad"  # 构造标志位为ACK的数据包
        response = sr1(packet, timeout=0.5, verbose=0)
        if int(response[TCP].flags) == 18:
            return ip, port, '1'
        else:
            return ip, port, '0'
    except:
        return ip, port, '0'
def scapy_udp_scan(ip,port=80):
    try:
        packet = IP(dst=ip) / UDP(dport=port, sport=randint(1, 65535))/B"dadadadad"   # 随机src端口，让扫面不易被察觉
        result = sr1(packet, timeout=0.5, verbose=0)  # timeout=5 为数据包提供五秒等待时间，如果没有回复就放弃，verbose=0，不显示输出
        if result is None:
            return ip, port, '1'
        else:
            return ip, port, '0'
    except:
        return ip, port, '0'

def socket_scan(host,port=80,timeout=5):
    zhuangtai = '0'
    tcp = socket(AF_INET, SOCK_STREAM)
    try:
        tcp.settimeout(int(timeout))  # 如果设置太小，检测不精确，设置太大，检测太慢
        result = tcp.connect_ex((host, int(port)))  # 效率比connect高，成功时返回0，失败时返回错误码
        if result == 0:
            zhuangtai='1'
        else:
            pass
        return host, port, zhuangtai
    except Exception as e:
        return host, port, zhuangtai
    finally:
        try:
            tcp.close()
        except:
            pass

def scanservice(host, port, timeout):
    Banner = ''
    service = 'Unknown'
    for probe in PROBES:
        try:
            sd = socket(AF_INET, SOCK_STREAM)
            sd.settimeout(int(timeout))
            sd.connect((host, int(port)))
            sd.send(probe.encode(encoding='utf-8'))
        except:
            continue
        try:
            result = sd.recv(1024)
            try:
                result = result.decode("utf-8")
                Banner = result

            except:
                result = str(result.decode("raw_unicode_escape").strip().encode("utf-8"))
                # result=str(result.decode("raw_unicode_escape").strip().encode("utf-8"))[2:-1]
                # result = result.decode("raw_unicode_escape")

            # result = sd.recv(1024).decode("raw_unicode_escape")
            # print(result)
            if ("<title>400 Bad Request</title>" in result and "https" in result) or (
                    "<title>400 Bad Request</title>" in result and "HTTPS" in result):
                service = 'https'
                break
            service = matchbanner( Banner, signs_rules)

            if service != 'Unknown':
                break

        except:
            continue
    if service != "Unknown":
        return host, port, service, Banner
    else:
        service = get_server(str(port))
    # host,port,service,Banner,title
    return host, port, service, Banner


def matchbanner(banner, slist):
    for item in slist:
        item = item.split('|')
        p = re.compile(item[1])
        if p.search(banner) != None:
            return item[0]
    return 'Unknown'

def get_server(port):
    SERVER = {
        'FTP': '21',
        'SSH': '22',
        'Telnet': '23',
        'SMTP': '25',
        'DNS': '53',
        'DHCP': '68',
        'HTTP': '80',
        'TFTP': '69',
        'HTTP': '8080',
        'POP3': '995',
        'NetBIOS': '139',
        'IMAP': '143',
        'HTTPS': '443',
        'SNMP': '161',
        'LDAP': '489',
        'SMB': '445',
        'SMTPS': '465',
        'Linux R RPE': '512',
        'Linux R RLT': '513',
        'Linux R cmd': '514',
        'Rsync': '873',
        'IMAPS': '993',
        'Proxy': '1080',
        'JavaRMI': '1099',
        'Lotus': '1352',
        'MSSQL': '1433',
        'MSSQL': '1434',
        'Oracle': '1521',
        'PPTP': '1723',
        'cPanel': '2082',
        'CPanel': '2083',
        'Zookeeper': '2181',
        'Docker': '2375',
        'Zebra': '2604',
        'MySQL': '3306',
        'Kangle': '3312',
        'RDP': '3389',
        'SVN': '3690',
        'Rundeck': '4440',
        'GlassFish': '4848',
        'PostgreSql': '5432',
        'PcAnywhere': '5632',
        'VNC': '5900',
        'CouchDB': '5984',
        'varnish': '6082',
        'Redis': '6379',
        'Weblogic': '7001',
        'Kloxo': '7778',
        'Zabbix': '8069',
        'RouterOS': '8291',
        'Elasticsearch': '9200',
        'Elasticsearch': '9300',
        'Zabbix': '10050',
        'Zabbix': '10051',
        'Memcached': '11211',
        'MongoDB': '27017',
        'MongoDB': '28017',
        'Hadoop': '50070'
    }
    for k, v in SERVER.items():
        if v == port:
            return k
    return 'Unknown'
