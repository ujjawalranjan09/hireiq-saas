"""AI Avatar Interviewer module - D-ID powered talking avatar."""

from modules.avatar.avatar_renderer import generate_avatar_video, get_avatar_status, stream_avatar_response
from modules.avatar.d_id_client import DIDClient

__all__ = [
    "generate_avatar_video",
    "get_avatar_status",
    "stream_avatar_response",
    "DIDClient",
]
