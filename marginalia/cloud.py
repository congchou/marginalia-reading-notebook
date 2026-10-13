"""Small Supabase Auth/PostgREST client with no third-party runtime dependency."""

from __future__ import annotations

import json
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


def validate_config(url: str, publishable_key: str) -> bool:
    parsed = urlparse(url.strip())
    key = publishable_key.strip()
    return (parsed.scheme == "https" and parsed.hostname is not None
            and parsed.hostname.endswith(".supabase.co") and key.startswith("sb_publishable_"))


def _default_request(method: str, url: str, headers: dict[str, str], body: str | None) -> Any:
    request = Request(url, data=body.encode("utf-8") if body is not None else None,
                      headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            content = response.read()
            return json.loads(content) if content else None
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read())
            message = payload.get("msg") or payload.get("error_description") or payload.get("message") or payload.get("error")
        except (ValueError, UnicodeError):
            message = None
        raise RuntimeError(message or f"云端请求失败（{exc.code}）") from exc
    except URLError as exc:
        raise RuntimeError(f"无法连接同步服务：{exc.reason}") from exc


class CloudClient:
    def __init__(self, url: str, publishable_key: str,
                 request: Callable[[str, str, dict[str, str], str | None], Any] = _default_request):
        if not validate_config(url, publishable_key):
            raise ValueError("请配置 HTTPS Supabase URL 和 publishable key")
        self.url = url.rstrip("/")
        self.key = publishable_key
        self.request = request
        self.session: dict[str, Any] | None = None

    def _auth(self, path: str, payload: dict[str, Any]) -> Any:
        return self.request("POST", f"{self.url}/auth/v1/{path}",
                            {"apikey": self.key, "Content-Type": "application/json"},
                            json.dumps(payload))

    def set_session(self, session: dict[str, Any] | None) -> None:
        if session:
            session = dict(session)
            session["expires_at"] = session.get("expires_at") or time.time() + int(session.get("expires_in", 3600))
        self.session = session

    def sign_up(self, email: str, password: str) -> Any:
        return self._auth("signup", {"email": email, "password": password})

    def sign_in(self, email: str, password: str) -> dict[str, Any]:
        self.set_session(self._auth("token?grant_type=password", {"email": email, "password": password}))
        return self.session or {}

    def _token(self) -> str:
        if not self.session:
            raise RuntimeError("请先登录同步账号")
        if time.time() + 60 >= self.session["expires_at"]:
            previous_user = self.session.get("user")
            refreshed = self._auth("token?grant_type=refresh_token", {"refresh_token": self.session["refresh_token"]})
            if not refreshed.get("user"):
                refreshed["user"] = previous_user
            self.set_session(refreshed)
        return self.session["access_token"]

    def _data(self, path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
        headers = {"apikey": self.key, "Authorization": f"Bearer {self._token()}",
                   "Content-Type": "application/json", "Prefer": "return=representation"}
        return self.request(method, f"{self.url}/rest/v1/{path}", headers,
                            json.dumps(payload, ensure_ascii=False) if payload is not None else None)

    def list_cards(self) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for offset in range(0, 100000, 500):
            page = self._data(f"cards?select=*&order=id&limit=500&offset={offset}")
            cards.extend(page)
            if len(page) < 500:
                break
        return cards

    def _payload(self, card: dict[str, Any], revision: int) -> dict[str, Any]:
        if not self.session or not self.session.get("user", {}).get("id"):
            raise RuntimeError("登录状态缺少用户 ID")
        fields = ("kind", "word", "meaning", "sentence", "translation", "structure", "source", "tags", "status")
        return {"id": card["id"], "user_id": self.session["user"]["id"],
                **{field: card.get(field) or "" for field in fields},
                "deleted": bool(card.get("deleted")), "revision": revision}

    def create_card(self, card: dict[str, Any]) -> dict[str, Any]:
        return self._data("cards", "POST", self._payload(card, 1))[0]

    def update_card(self, card: dict[str, Any], expected_version: int) -> dict[str, Any] | None:
        query = urlencode({"id": f"eq.{card['id']}", "revision": f"eq.{expected_version}"})
        rows = self._data(f"cards?{query}", "PATCH", self._payload(card, expected_version + 1))
        return rows[0] if rows else None
