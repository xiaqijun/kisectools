from django.db import models

# Create your models here.
class FirewallPolicy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    source_zone = models.CharField(max_length=100)
    destination_zone = models.CharField(max_length=100)
    source_ip=models.GenericIPAddressField()
    destination_ip=models.GenericIPAddressField()
    source_port=models.IntegerField()
    destination_port=models.IntegerField()
    protocol=models.CharField(max_length=10)
    expiration_date = models.DateField()
    applicant = models.CharField(max_length=100)
    device=models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name