from __future__ import annotations

import os


class ProductAnalytics:
    """Optional PostHog adapter for onboarding/product events, never edge inference."""

    def __init__(self) -> None:
        self.enabled = bool(os.getenv("POSTHOG_API_KEY"))
        self._client = None
        if self.enabled:
            import posthog

            posthog.api_key = os.environ["POSTHOG_API_KEY"]
            posthog.host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
            self._client = posthog

    def capture(self, customer_id: str, event: str, properties: dict | None = None) -> None:
        if self._client:
            self._client.capture(customer_id, event, properties or {})
