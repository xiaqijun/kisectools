import requests
import json
import urllib3
# 忽略 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
class ZoomEyePlugin:
    def __init__(self,username=None, password=None,zoomeye_ip=None):
        self.username=username
        self.password=password
        self.zoomeye_ip=zoomeye_ip
    def get_token(self):
        url=f"https://{self.zoomeye_ip}/api/v4/external/login"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'username': self.username,
            'password': self.password
        }
        response = requests.post(url, headers=headers, json=data,verify=False)
        print(response.text)
        if response.status_code != 200:
            return False
        return json.loads(response.text)['data']['token']
    
    def create_task(self,target,task_name,ports):
        url=f"https://{self.zoomeye_ip}/api/v4/external/detection"
        headers={
            'b-json-web-token':self.get_token()
        }
        target_list=target.split(',')
        ports_list=ports.split(',')
        data={
            'name':task_name,
            'target':target_list,
            'ports':ports_list,
            'protocol':["tcp"]
        }
        response=requests.post(url=url,headers=headers,json=data,verify=False)  # Changed 'data' to 'json'
        if response.status_code!=200:
            return response.text
        return response.json()['data']['taskId']
    
    def get_task_status(self,task_id):
        url=f"https://{self.zoomeye_ip}/api/v4/external/taskInfo?taskId={task_id}"
        headers={
            'b-json-web-token':self.get_token()
        }

        response=requests.get(url=url,headers=headers,verify=False)
        if response.status_code!=200:
            return response.text
    
        return response.json()['data']['status']
if __name__ == '__main__':
    zoomeye=ZoomEyePlugin(username='secmg', password='zoomeye25@802q1',zoomeye_ip='172.17.11.27')
    token=zoomeye.get_token()
    #task_id=zoomeye.create_task('172.17.11.34','test_task2','22,80')
    status=zoomeye.get_task_status("67f3802042c076a9ca6532ed")
    print(status)
