import json
import time
import subprocess
import requests
from websocket import create_connection
import base64

# 참고 소스
# https://medium.com/@lagenar/using-headless-chrome-via-the-websockets-interface-5f498fb67e0f

def start_browser(browser_path, debugging_port):
    options = ['--headless',
               '--remote-debugging-port={}'.format(debugging_port)]
    browser_proc = subprocess.Popen([browser_path] + options)
    wait_seconds = 10.0
    sleep_step = 0.25
    while wait_seconds > 0:
        try:
            url = 'http://127.0.0.1:{}/json'.format(debugging_port)
            resp = requests.get(url).json()
            ws_url = resp[0]['webSocketDebuggerUrl']
            return browser_proc, create_connection(ws_url)
        except requests.exceptions.ConnectionError:
            time.sleep(sleep_step)
            wait_seconds -= sleep_step
    raise Exception('Unable to connect to chrome')

request_id = 0
def run_command(conn, method, **kwargs):
    global request_id
    request_id += 1
    command = {'method': method,
               'id': request_id,
               'params': kwargs}
    conn.send(json.dumps(command))
    while True:
        msg = json.loads(conn.recv())
        if msg.get('id') == request_id:
            return msg

gnews_url = 'https://news.google.com/news/?ned=us&hl=en'
chrome_path = '../Extern/chrome/chrome.exe'
browser, conn = start_browser(chrome_path, 9222)

# url 오픈
run_command(conn, 'Page.navigate', url=gnews_url)
time.sleep(5) # let it load

# 캡처 추가
result = run_command(conn, 'Page.captureScreenshot', format='png')
data = result.get('result').get('data')
data = bytes(data, 'utf-8')
with open("imageToSave.png", "wb") as fh:
    fh.write(base64.decodebytes(data))

# 자바스크립트 실행
js = """
var sel = '[role="heading"][aria-level="2"]';
var headings = document.querySelectorAll(sel);
headings = [].slice.call(headings).map((link)=>{return link.innerText});
JSON.stringify(headings);
"""
result = run_command(conn, 'Runtime.evaluate', expression=js)
headings = json.loads(result['result']['result']['value'])
for heading in headings:
   print(heading)

browser.terminate()
