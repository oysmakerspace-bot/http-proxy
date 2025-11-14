from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.before_request
def before_request_func():
    allowed_ips_str = os.environ.get('ALLOWED_IPS', '')
    if allowed_ips_str:
        ALLOWED_IPS = allowed_ips_str.split(',')
        if request.remote_addr not in ALLOWED_IPS:
            return jsonify({"error": "Source IP not allowed"}), 403

@app.route('/', methods=['POST'])
def proxy():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Invalid JSON body"}), 400

    method = json_data.pop('method', None)
    destination = json_data.pop('destination', None)

    if not method or not destination:
        return jsonify({"error": "method and destination are required in the JSON body"}), 400

    method = method.upper()
    if method not in ['GET', 'POST']:
        return jsonify({"error": "Invalid method specified"}), 400

    try:
        if method == 'GET':
            resp = requests.get(destination, params=json_data, headers=request.headers)
        elif method == 'POST':
            resp = requests.post(destination, json=json_data, headers=request.headers)

        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
