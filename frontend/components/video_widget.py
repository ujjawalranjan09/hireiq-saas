"""Camera feed component for Streamlit."""

import streamlit as st
import numpy as np


def show_camera_feed():
    """Display a live camera feed in the Streamlit sidebar.
    
    Uses st.camera_input for simplicity, or falls back to
    a placeholder if camera is not available.
    """
    camera_input = st.camera_input("Take a picture", key="camera_feed")

    if camera_input:
        st.image(camera_input, caption="Camera Preview", use_container_width=True)
        return True
    return False


def show_video_widget(camera_index: int = 0):
    """Display a more advanced video widget using OpenCV.
    
    Args:
        camera_index: Camera device index.
    """
    try:
        import cv2
    except ImportError:
        st.warning("OpenCV not available for live video feed.")
        return show_camera_feed()

    from modules.video.camera_feed import CameraFeed

    if "camera" not in st.session_state:
        st.session_state["camera"] = CameraFeed(camera_index=camera_index)

    camera = st.session_state["camera"]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📷 Start Camera"):
            if camera.open():
                st.success("Camera started!")
            else:
                st.error("Cannot open camera.")
    with col2:
        if st.button("⏹️ Stop Camera"):
            camera.release()
            st.info("Camera stopped.")

    if camera.is_open:
        frame = camera.read_frame_rgb()
        if frame is not None:
            st.image(frame, caption="Live Feed", use_container_width=True)
        else:
            st.warning("No frame available.")
