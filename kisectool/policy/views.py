from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import FirewallPolicy
@login_required
def index(request):
    
    policies=FirewallPolicy.objects.all()
    return render(request,'index.html',{'policies':policies})

    