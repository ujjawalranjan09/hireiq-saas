"""D-ID API client wrapper for avatar video generation."""

import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

DID_BASE_URL = "https://api.d-id.com"
DEFAULT_AVATAR_IMAGE = "https://create-images-results.d-id.com/DefaultPresenters/Noelle_f/image.jpeg"
DEFAULT_VOICE_ID = "en-US-JennyNeural"


class DIDError(Exception):
    """Exception raised for D-ID API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"D-ID API error {status_code}: {message}")


class DIDClient:
    """Client for the D-ID talking-head video API.

    Handles talk creation, status polling, and video download.
    Includes rate limiting and comprehensive error handling.

    Args:
        api_key: D-ID API key (format: "Basic xxx" or bare key).
        base_url: Override the default D-ID API base URL.
        poll_interval: Seconds between status polls (default 2).
        max_poll_attempts: Maximum poll attempts before timeout (default 60).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DID_BASE_URL,
        poll_interval: float = 2.0,
        max_poll_attempts: int = 60,
    ):
        if not api_key:
            raise ValueError("D-ID API key is required")

        # Normalize auth header
        if api_key.startswith("Basic ") or api_key.startswith("Bearer "):
            self._auth = api_key
        else:
            self._auth = f"Basic {api_key}"

        self._base_url = base_url.rstrip("/")
        self._poll_interval = poll_interval
        self._max_poll_attempts = max_poll_attempts
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": self._auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        # Simple rate-limit state
        self._last_request_time: float = 0.0
        self._min_interval: float = 0.5  # seconds between requests

    # ── helpers ───────────────────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Enforce minimum interval between API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the D-ID API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            path: API path (appended to base URL).
            json_data: Optional JSON body.
            timeout: Request timeout in seconds.

        Returns:
            Parsed JSON response.

        Raises:
            DIDError: On non-2xx responses or network errors.
        """
        self._rate_limit()
        url = f"{self._base_url}{path}"

        try:
            resp = self._session.request(method, url, json=json_data, timeout=timeout)
        except requests.RequestException as exc:
            logger.error(f"D-ID network error: {exc}")
            raise DIDError(0, f"Network error: {exc}") from exc

        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", 5))
            logger.warning(f"D-ID rate limited, waiting {retry_after}s")
            time.sleep(retry_after)
            return self._request(method, path, json_data, timeout)

        if not resp.ok:
            detail = resp.text[:300]
            logger.error(f"D-ID API {resp.status_code}: {detail}")
            raise DIDError(resp.status_code, detail)

        if resp.status_code == 204:
            return {}
        return resp.json()

    # ── public API ────────────────────────────────────────────────────

    def create_talk(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE_ID,
        source_url: str = DEFAULT_AVATAR_IMAGE,
        driver_id: str = "Vqx2qg74TC",
        background_color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new talking-head video.

        Args:
            text: The script the avatar will speak (max 5000 chars).
            voice_id: TTS voice identifier.
            source_url: URL of the avatar face image.
            driver_id: D-ID driver (animation style).
            background_color: Optional hex background color.

        Returns:
            Dict with 'id', 'status', and other metadata.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        text = text[:5000]

        payload: Dict[str, Any] = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id,
                },
            },
            "config": {
                "result_format": "mp4",
                "driver_id": driver_id,
            },
        }

        if background_color:
            payload["config"]["background_color"] = background_color

        logger.info(f"Creating D-ID talk ({len(text)} chars)")
        return self._request("POST", "/talks", json_data=payload)

    def get_talk(self, talk_id: str) -> Dict[str, Any]:
        """Get the status and result of a talk.

        Args:
            talk_id: The talk ID returned from create_talk.

        Returns:
            Dict with status, result_url, etc.
        """
        return self._request("GET", f"/talks/{talk_id}")

    def delete_talk(self, talk_id: str) -> Dict[str, Any]:
        """Delete a talk and its associated video.

        Args:
            talk_id: The talk ID to delete.

        Returns:
            Empty dict on success.
        """
        return self._request("DELETE", f"/talks/{talk_id}")

    def wait_for_completion(
        self,
        talk_id: str,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Poll until a talk finishes or fails.

        Args:
            talk_id: The talk ID to monitor.
            on_progress: Optional callback receiving the status dict each poll.

        Returns:
            Final talk status dict with result_url on success.

        Raises:
            DIDError: If the talk fails or polling times out.
        """
        for attempt in range(self._max_poll_attempts):
            status = self.get_talk(talk_id)
            state = status.get("status", "unknown")

            if on_progress:
                on_progress(status)

            if state == "done":
                logger.info(f"Talk {talk_id} completed")
                return status
            if state == "error":
                error_detail = status.get("error", {}).get("description", "Unknown error")
                raise DIDError(500, f"Talk failed: {error_detail}")
            if state == "rejected":
                raise DIDError(400, "Talk was rejected")

            logger.debug(f"Talk {talk_id} status: {state} (attempt {attempt + 1})")
            time.sleep(self._poll_interval)

        raise DIDError(408, f"Talk {talk_id} timed out after {self._max_poll_attempts} polls")

    def download_video(self, result_url: str, output_path: str) -> str:
        """Download a completed video to local disk.

        Args:
            result_url: The video URL from a completed talk.
            output_path: Local file path to save the video.

        Returns:
            The output_path on success.

        Raises:
            DIDError: On download failure.
        """
        try:
            resp = requests.get(result_url, timeout=60, stream=True)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Video downloaded to {output_path}")
            return output_path
        except requests.RequestException as exc:
            raise DIDError(0, f"Download failed: {exc}") from exc
