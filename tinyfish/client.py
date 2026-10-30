"""Small, testable TinyFish HTTP client with optional SDK compatibility."""

from dataclasses import dataclass
from typing import Any

import requests

from core.config import get_settings


class TinyFishError(RuntimeError):
    """Raised when TinyFish returns an unrecoverable API error."""


@dataclass
class TinyFishClient:
    api_key: str | None = None
    timeout: float | None = None

    def __post_init__(self) -> None:
        settings = get_settings()
        self.api_key = self.api_key or settings.tinyfish_api_key
        self.timeout = self.timeout or settings.request_timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise TinyFishError("TINYFISH_API_KEY is not configured.")
        return {"X-API-Key": self.api_key, "Accept": "application/json"}

    def search(self, **params: Any) -> Any:
        response = requests.get(
            "https://api.search.tinyfish.ai/",
            headers=self._headers(),
            params=params,
            timeout=self.timeout,
        )
        if response.status_code in {401, 403}:
            raise TinyFishError("TinyFish authentication failed.")
        response.raise_for_status()
        return response.json()

    def fetch(self, urls: list[str], **params: Any) -> Any:
        if len(urls) > 10:
            raise ValueError("TinyFish fetch accepts at most 10 URLs per request.")
        response = requests.post(
            "https://api.fetch.tinyfish.ai/",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"urls": urls, "output_format": "markdown", **params},
            timeout=self.timeout,
        )
        if response.status_code in {401, 403}:
            raise TinyFishError("TinyFish authentication failed.")
        response.raise_for_status()
        return response.json()

    def run_agent(
        self,
        *,
        url: str,
        goal: str,
        output_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a metered TinyFish browser agent against a specific page."""
        payload: dict[str, Any] = {"url": url, "goal": goal}
        if output_schema:
            payload["output_schema"] = output_schema
        response = requests.post(
            "https://agent.tinyfish.ai/v1/automation/run",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=max(self.timeout, 90),
        )
        if response.status_code in {401, 403}:
            raise TinyFishError("TinyFish agent authentication failed.")
        response.raise_for_status()
        body = response.json()
        result = body.get("result", body) if isinstance(body, dict) else body
        if isinstance(result, dict) and isinstance(result.get("result"), dict):
            result = result["result"]
        if not isinstance(result, dict):
            raise TinyFishError("TinyFish agent returned no structured result.")
        return result
