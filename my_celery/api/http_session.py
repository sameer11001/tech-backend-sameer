import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RequestsSessionHandler:
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_headers(self, access_token, content_type="application/json"):
        headers = {"Authorization": f"Bearer {access_token}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def post(self, url: str, headers: dict, json: dict):
        return self.session.post(url, headers=headers, json=json)
    
http_session = RequestsSessionHandler()