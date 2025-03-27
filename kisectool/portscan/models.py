from django.db import models

# Create your models here.
class Asset(models.Model):
    ip=models.GenericIPAddressField(verbose_name='IP地址',unique=True)
    icmp_status=models.BooleanField(verbose_name='ICMP状态',default=False)
    create_time=models.DateTimeField(auto_now_add=True)
    update_time=models.DateTimeField(auto_now=True)

class Port(models.Model):
    asset=models.ForeignKey(Asset,on_delete=models.CASCADE)
    port=models.IntegerField(verbose_name='端口')
    service=models.CharField(verbose_name='服务',max_length=20)
    banner=models.CharField(verbose_name='Banner',max_length=100)
    create_time=models.DateTimeField(auto_now_add=True)
    update_time=models.DateTimeField(auto_now=True)
