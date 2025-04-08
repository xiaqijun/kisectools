from flask import Blueprint, render_template, request
from flask_security import login_required
from . import db
from .models import Plugins
plugin_bp = Blueprint('plugin', __name__)
@plugin_bp.route('/', methods=['GET'])
@login_required
def plugin():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    plugins = Plugins.query.paginate(page=page, per_page=per_page)
    responses = {
        'page': plugins.page,
        'per_page': plugins.per_page,
        'total': plugins.total,
        'data': [
            {
                'name': plugin.name,
                'type': plugin.type,
                'description': plugin.description,
                'id': plugin.id
            } for plugin in plugins.items
        ]
    }
    return render_template('plugin.html', plugins=responses)
