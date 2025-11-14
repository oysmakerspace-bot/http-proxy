from flask import Flask, request, jsonify
import requests
import os
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

def _get_headers(url):
    headers = dict(request.headers)
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'

    # Get the domain from the destination URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    headers['Host'] = domain

    return headers

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
        current_url = destination
        max_redirects = 5
        redirect_count = 0

        while redirect_count < max_redirects:
            headers = _get_headers(current_url)

            if method == 'GET':
                resp = requests.get(current_url, params=json_data, headers=headers, allow_redirects=False)
            elif method == 'POST':
                resp = requests.post(current_url, json=json_data, headers=headers, allow_redirects=False)
                method = 'GET'
                json_data = {}

            if resp.status_code in [301, 302, 307, 308]:
                redirect_url = resp.headers.get('Location')
                if not redirect_url:
                    break

                current_url = urljoin(current_url, redirect_url)
                redirect_count += 1
            else:
                break

        if redirect_count >= max_redirects:
            return jsonify({"error": "Too many redirects"}), 508

        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
