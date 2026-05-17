"""OpenCV camera capture module."""

import logging
import threading
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class CameraFeed:
    """Manages OpenCV camera capture for the interview."""

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        """Initialize the camera feed.
        
        Args:
            camera_index: Camera device index (0 for default).
            width: Frame width.
            height: Frame height.
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._cap = None
        self._lock = threading.Lock()
        self._is_open = False

    def open(self) -> bool:
        """Open the camera.
        
        Returns:
            True if camera opened successfully.
        """
        try:
            import cv2
        except ImportError:
            logger.error("OpenCV not installed")
            return False

        with self._lock:
            if self._is_open:
                return True
            try:
                self._cap = cv2.VideoCapture(self.camera_index)
                if not self._cap.isOpened():
                    logger.error(f"Cannot open camera {self.camera_index}")
                    return False
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._is_open = True
                logger.info(f"Camera {self.camera_index} opened")
                return True
            except Exception as e:
                logger.error(f"Failed to open camera: {e}")
                return False

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a single frame from the camera.
        
        Returns:
            Frame as numpy array (BGR), or None if failed.
        """
        import cv2
        with self._lock:
            if not self._is_open or self._cap is None:
                return None
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Failed to read frame")
                return None
            return frame

    def read_frame_rgb(self) -> Optional[np.ndarray]:
        """Read a frame and convert to RGB.
        
        Returns:
            Frame as numpy array (RGB), or None if failed.
        """
        import cv2
        frame = self.read_frame()
        if frame is not None:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def release(self) -> None:
        """Release the camera."""
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._is_open = False
                logger.info("Camera released")

    @property
    def is_open(self) -> bool:
        """Check if camera is open."""
        return self._is_open

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.release()


def list_cameras(max_cameras: int = 10) -> list:
    """List available camera devices.
    
    Args:
        max_cameras: Maximum number of cameras to check.
        
    Returns:
        List of available camera indices.
    """
    try:
        import cv2
    except ImportError:
        return []

    available = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available
