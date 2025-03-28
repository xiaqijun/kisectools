from flask import Blueprint, render_template
from flask_security import login_required
from . import db
from .models import User, Role
