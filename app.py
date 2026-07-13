import os, secrets
from datetime import timedelta
from functools import wraps
from flask import Flask, jsonify, request, render_template, session

from database import (
    init_db, get_all_links, create_link, update_link, delete_link, get_link, STATUSES,
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=8)

OPS_HUB_PIN = os.environ.get('OPS_HUB_PIN', '2104')

init_db()


# ── Auth helpers ─────────────────────────────────────────────────────────────
def is_authenticated():
    return session.get('auth') == True


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return jsonify({'error': 'Unauthorised'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Pages ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if not is_authenticated():
        return render_template('pin.html')
    return render_template('index.html')


# ── PIN auth ─────────────────────────────────────────────────────────────────
@app.route('/api/auth/pin', methods=['POST'])
def api_pin():
    data = request.get_json() or {}
    pin = str(data.get('pin', ''))
    if pin == OPS_HUB_PIN:
        session.permanent = True
        session['auth'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Incorrect PIN'}), 401


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})


# ── Links CRUD ───────────────────────────────────────────────────────────────
def _validate_link(data):
    name = (data.get('name') or '').strip()
    url = (data.get('url') or '').strip()
    category = (data.get('category') or '').strip() or 'Uncategorised'
    status = (data.get('status') or 'idea').strip()

    if not name or not url:
        return None, ('Name and URL are required', 400)
    if status not in STATUSES:
        return None, ('Invalid status', 400)
    if not url.lower().startswith(('http://', 'https://')):
        url = 'https://' + url

    return {'name': name, 'url': url, 'category': category, 'status': status}, None


@app.route('/api/links', methods=['GET'])
@require_auth
def api_get_links():
    return jsonify(get_all_links())


@app.route('/api/links', methods=['POST'])
@require_auth
def api_create_link():
    data = request.get_json() or {}
    fields, error = _validate_link(data)
    if error:
        return jsonify({'error': error[0]}), error[1]
    link = create_link(fields['name'], fields['url'], fields['category'], fields['status'])
    return jsonify(link), 201


@app.route('/api/links/<int:link_id>', methods=['PUT'])
@require_auth
def api_update_link(link_id):
    if not get_link(link_id):
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    fields, error = _validate_link(data)
    if error:
        return jsonify({'error': error[0]}), error[1]
    link = update_link(link_id, fields['name'], fields['url'], fields['category'], fields['status'])
    return jsonify(link)


@app.route('/api/links/<int:link_id>', methods=['DELETE'])
@require_auth
def api_delete_link(link_id):
    if not delete_link(link_id):
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n  Ops Hub: http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=False)
