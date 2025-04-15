from flask import Flask,render_template,Blueprint,request
device_bp = Blueprint('device', __name__)
from flask_security import login_required