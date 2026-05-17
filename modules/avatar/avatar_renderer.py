"""Avatar renderer - generate talking avatar videos with D-ID or fallback TTS waveform."""

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import OUTPUTS_DIR

logger = logging.getLogger(__name__)

AVATAR_DIR = OUTPUTS_DIR / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

# Cache for D-ID client instance
_did_client = None


def _get_did_client():
    """Lazily instantiate the D-ID client if an API key is configured.

    Returns:
        DIDClient instance or None if not configured.
    """
    global _did_client
    if _did_client is not None:
        return _did_client

    api_key = os.getenv("D_ID_API_KEY", "")
    if not api_key:
        return None

    try:
        from modules.avatar.d_id_client import DIDClient
        _did_client = DIDClient(api_key=api_key)
        logger.info("D-ID client initialized")
        return _did_client
    except Exception as exc:
        logger.warning(f"Failed to initialize D-ID client: {exc}")
        return None


def generate_avatar_video(
    text: str,
    voice_id: str = "en-US-JennyNeural",
    source_url: Optional[str] = None,
    background_color: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a talking avatar video from text.

    Uses D-ID API when configured; falls back to a styled HTML card
    with TTS waveform animation when the API key is absent.

    Args:
        text: The text the avatar should speak.
        voice_id: TTS voice identifier (D-ID voice or edge-tts voice).
        source_url: Optional URL for the avatar's face image (D-ID only).
        background_color: Optional hex background color (D-ID only).

    Returns:
        Dict with keys:
            - video_path: Path to generated video (D-ID) or None.
            - html_path: Path to fallback HTML card (fallback) or None.
            - method: "did" or "fallback".
            - task_id: D-ID talk ID (D-ID only).
            - status: "completed", "processing", or "fallback".
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Text cannot be empty")

    client = _get_did_client()

    if client is not None:
        return _generate_did_video(client, text, voice_id, source_url, background_color)
    else:
        return _generate_fallback_card(text, voice_id)


def get_avatar_status(task_id: str) -> Dict[str, Any]:
    """Check the status of a D-ID avatar generation task.

    Args:
        task_id: The D-ID talk ID.

    Returns:
        Dict with status, progress, and video URL if completed.

    Raises:
        ValueError: If D-ID client is not configured.
    """
    client = _get_did_client()
    if client is None:
        raise ValueError("D-ID API not configured — cannot check status")

    try:
        result = client.get_talk(task_id)
        return {
            "task_id": task_id,
            "status": result.get("status", "unknown"),
            "video_url": result.get("result_url"),
            "progress": result.get("progress", "0%"),
            "created_at": result.get("created_at"),
        }
    except Exception as exc:
        logger.error(f"Status check failed for {task_id}: {exc}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(exc),
        }


def stream_avatar_response(question_text: str) -> Dict[str, Any]:
    """Generate an avatar response suitable for streaming in real time.

    For D-ID: starts generation and returns task_id immediately.
    For fallback: returns HTML card path synchronously.

    Args:
        question_text: The question or response text.

    Returns:
        Dict with task_id (D-ID) or html_path (fallback), plus method indicator.
    """
    client = _get_did_client()

    if client is not None:
        try:
            result = client.create_talk(
                text=question_text,
                voice_id="en-US-JennyNeural",
            )
            return {
                "task_id": result.get("id"),
                "method": "did",
                "status": "processing",
            }
        except Exception as exc:
            logger.error(f"D-ID stream failed, using fallback: {exc}")
            fallback = _generate_fallback_card(question_text, "en-US-JennyNeural")
            fallback["method"] = "fallback"
            return fallback
    else:
        fallback = _generate_fallback_card(question_text, "en-US-JennyNeural")
        fallback["method"] = "fallback"
        return fallback


# ── Internal helpers ──────────────────────────────────────────────────


def _generate_did_video(
    client,
    text: str,
    voice_id: str,
    source_url: Optional[str],
    background_color: Optional[str],
) -> Dict[str, Any]:
    """Create a D-ID talk, poll for completion, and download the video."""
    from modules.avatar.d_id_client import DIDError

    kwargs: Dict[str, Any] = {"voice_id": voice_id}
    if source_url:
        kwargs["source_url"] = source_url
    if background_color:
        kwargs["background_color"] = background_color

    try:
        talk = client.create_talk(text=text, **kwargs)
        talk_id = talk["id"]
        logger.info(f"D-ID talk created: {talk_id}")

        # Poll for completion
        final = client.wait_for_completion(talk_id)
        video_url = final.get("result_url", "")

        if not video_url:
            raise DIDError(500, "No result URL in completed talk")

        # Download
        filename = f"avatar_{uuid.uuid4().hex[:12]}.mp4"
        output_path = str(AVATAR_DIR / filename)
        client.download_video(video_url, output_path)

        return {
            "video_path": output_path,
            "html_path": None,
            "method": "did",
            "task_id": talk_id,
            "status": "completed",
        }

    except DIDError as exc:
        logger.warning(f"D-ID generation failed: {exc}, falling back")
        fallback = _generate_fallback_card(text, voice_id)
        fallback["did_error"] = str(exc)
        return fallback


def _generate_fallback_card(text: str, voice_id: str) -> Dict[str, Any]:
    """Generate a styled HTML card with animated TTS waveform bars.

    This is used when D-ID is not configured or fails.

    Args:
        text: The text to display.
        voice_id: Voice identifier (used for edge-tts if available).

    Returns:
        Dict with html_path, method="fallback", status="completed".
    """
    # Try to generate TTS audio
    audio_filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
    audio_path = str(AVATAR_DIR / audio_filename)
    audio_generated = _generate_tts_audio(text, voice_id, audio_path)

    # Build animated waveform bars
    bars_html = ""
    for i in range(40):
        delay = round(i * 0.05, 2)
        height = 15 + (i * 7) % 55
        bars_html += f'<div class="bar" style="animation-delay:{delay}s; height:{height}px;"></div>\n'

    audio_tag = ""
    if audio_generated:
        audio_tag = f'<audio id="tts-audio" src="{os.path.basename(audio_path)}" preload="auto"></audio>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Interviewer</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    font-family: 'Segoe UI', system-ui, sans-serif; color: #fff;
  }}
  .card {{
    background: rgba(255,255,255,0.06); backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.12); border-radius: 20px;
    padding: 40px; max-width: 640px; width: 90%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    text-align: center;
  }}
  .avatar-circle {{
    width: 100px; height: 100px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    margin: 0 auto 24px; display: flex; align-items: center; justify-content: center;
    font-size: 42px; box-shadow: 0 8px 30px rgba(102,126,234,0.4);
    animation: pulse 2s ease-in-out infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ transform: scale(1); }}
    50% {{ transform: scale(1.05); }}
  }}
  .role {{ font-size: 13px; text-transform: uppercase; letter-spacing: 3px; color: #667eea; margin-bottom: 8px; }}
  .name {{ font-size: 20px; font-weight: 600; margin-bottom: 20px; }}
  .waveform {{
    display: flex; align-items: flex-end; justify-content: center;
    gap: 3px; height: 70px; margin: 20px 0;
  }}
  .bar {{
    width: 4px; background: linear-gradient(to top, #667eea, #764ba2);
    border-radius: 2px; animation: wave 1s ease-in-out infinite alternate;
  }}
  @keyframes wave {{
    from {{ height: 10px; opacity: 0.5; }}
    to {{ height: 60px; opacity: 1; }}
  }}
  .text-box {{
    background: rgba(0,0,0,0.3); border-radius: 12px; padding: 20px;
    margin-top: 20px; text-align: left; line-height: 1.7;
    font-size: 15px; color: rgba(255,255,255,0.9);
    border-left: 3px solid #667eea;
  }}
  .badge {{
    display: inline-block; font-size: 11px; padding: 4px 10px;
    border-radius: 20px; background: rgba(102,126,234,0.2);
    color: #a5b4fc; margin-top: 16px;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="avatar-circle">🤖</div>
  <div class="role">AI Interviewer</div>
  <div class="name">Interview Assistant</div>
  <div class="waveform">
{bars_html}
  </div>
  <div class="text-box">{_escape_html(text)}</div>
  <div class="badge">💬 TTS Mode — D-ID not configured</div>
  {audio_tag}
</div>
<script>
  const audio = document.getElementById('tts-audio');
  if (audio) {{ audio.play().catch(()=>{{}}); }}
</script>
</body>
</html>"""

    html_filename = f"avatar_{uuid.uuid4().hex[:12]}.html"
    html_path = str(AVATAR_DIR / html_filename)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Fallback avatar card created: {html_path}")

    result: Dict[str, Any] = {
        "video_path": None,
        "html_path": html_path,
        "method": "fallback",
        "task_id": None,
        "status": "completed",
    }
    if audio_generated:
        result["audio_path"] = audio_path

    return result


def _generate_tts_audio(text: str, voice_id: str, output_path: str) -> bool:
    """Try to generate TTS audio using edge-tts or gtts.

    Args:
        text: Text to convert to speech.
        voice_id: Voice identifier.
        output_path: Where to save the MP3 file.

    Returns:
        True if audio was generated successfully.
    """
    # Try edge-tts first (better quality)
    try:
        import edge_tts
        import asyncio

        async def _edge_tts():
            communicate = edge_tts.Communicate(text, voice_id)
            await communicate.save(output_path)

        asyncio.run(_edge_tts())
        if os.path.exists(output_path):
            return True
    except ImportError:
        pass
    except Exception as exc:
        logger.debug(f"edge-tts failed: {exc}")

    # Fallback to gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en")
        tts.save(output_path)
        return os.path.exists(output_path)
    except ImportError:
        pass
    except Exception as exc:
        logger.debug(f"gtts failed: {exc}")

    return False


def _escape_html(text: str) -> str:
    """Escape special HTML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "<br>")
    )
