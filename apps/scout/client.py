import requests


YUTORI_API_BASE = "https://api.yutori.com"


class YutoriAPIError(Exception):
    """Raised when the Yutori API returns a non-2xx status."""

    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body
        super(YutoriAPIError, self).__init__(
            "Yutori API returned {}: {}".format(status_code, body)
        )


class YutoriClient(object):
    def __init__(self, api_key, base_url=YUTORI_API_BASE):
        self.api_key = api_key
        self.base_url = base_url

    def _headers(self):
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _post(self, path, payload):
        url = "{}{}".format(self.base_url, path)
        resp = requests.post(url, json=payload, headers=self._headers())
        if not (200 <= resp.status_code < 300):
            raise YutoriAPIError(resp.status_code, resp.text)
        return resp.json()

    def create_scout(
        self,
        query,
        output_schema,
        webhook_url,
        output_interval=86400,
    ):
        return self._post(
            "/v1/scouting/tasks",
            {
                "query": query,
                "output_schema": output_schema,
                "output_interval": output_interval,
                "webhook_url": webhook_url,
                "webhook_format": "scout",
                "skip_email": True,
            },
        )

    def pause_scout(self, scout_id):
        return self._post(
            "/v1/scouting/tasks/{}/pause".format(scout_id), {}
        )

    def resume_scout(self, scout_id):
        return self._post(
            "/v1/scouting/tasks/{}/resume".format(scout_id), {}
        )
