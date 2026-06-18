from __future__ import annotations

import json
from typing import Any

import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config.settings import get_global_settings


class HttpClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: int | None = None,
        retries: int | None = None,
        backoff: float | None = None,
    ) -> None:
        settings = get_global_settings()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout or settings.timeout_seconds
        self.session = self._build_session(
            retries or settings.retry.max_attempts,
            backoff if backoff is not None else settings.retry.backoff_factor,
        )
        if token:
            self.set_token(token)

    @staticmethod
    def _build_session(retries: int, backoff: float) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            backoff_factor=backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "PATCH", "DELETE"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def set_token(self, token: str) -> None:
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self) -> None:
        self.session.headers.pop("Authorization", None)

    @allure.step("{method} {path}")
    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        if response.status_code >= 400:
            self._attach_exchange(method, url, kwargs, response)
        return response

    def _attach_exchange(
        self,
        method: str,
        url: str,
        kwargs: dict[str, Any],
        response: requests.Response,
    ) -> None:
        request_body = kwargs.get("json") or kwargs.get("data")
        payload = {
            "method": method,
            "url": url,
            "body": request_body,
            "status": response.status_code,
        }
        allure.attach(
            json.dumps(payload, indent=2, default=str),
            name=f"{method} {url}",
            attachment_type=allure.attachment_type.JSON,
        )
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                allure.attach(
                    json.dumps(response.json(), indent=2, default=str),
                    name="response_body",
                    attachment_type=allure.attachment_type.JSON,
                )
            except ValueError:
                pass

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
