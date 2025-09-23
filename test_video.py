#!/usr/bin/env python3
"""
Test script untuk memverifikasi video playback
"""

import cv2
import sys
import os

def test_video_loading(video_path):
    """Test apakah video bisa dimuat dengan OpenCV"""
    print(f"Testing video: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"❌ File tidak ditemukan: {video_path}")
        return False
        
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Gagal membuka video: {video_path}")
        return False
        
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✅ Video berhasil dimuat!")
    print(f"   Resolution: {width}x{height}")
    print(f"   Total frames: {total_frames}")
    print(f"   FPS: {fps}")
    
    # Try reading first frame
    ret, frame = cap.read()
    if ret:
        print(f"✅ Frame pertama berhasil dibaca!")
        print(f"   Frame shape: {frame.shape}")
    else:
        print(f"❌ Gagal membaca frame pertama!")
        cap.release()
        return False
        
    cap.release()
    return True

def test_opencv_installation():
    """Test instalasi OpenCV"""
    try:
        print(f"OpenCV version: {cv2.__version__}")
        
        # Test backend
        backends = []
        if cv2.CAP_FFMPEG in dir(cv2):
            backends.append("FFMPEG")
        if cv2.CAP_GSTREAMER in dir(cv2):
            backends.append("GStreamer")
        if cv2.CAP_DSHOW in dir(cv2):
            backends.append("DirectShow")
            
        print(f"Available backends: {', '.join(backends) if backends else 'None detected'}")
        return True
    except Exception as e:
        print(f"❌ Error dengan OpenCV: {e}")
        return False

if __name__ == "__main__":
    print("=== Video Playback Test ===")
    
    # Test OpenCV installation
    if not test_opencv_installation():
        sys.exit(1)
        
    print("\n=== Instructions ===")
    print("1. Drag dan drop file video (.mp4, .mov, .avi) ke console ini")
    print("2. Atau ketik path lengkap ke file video")
    print("3. Ketik 'quit' untuk keluar")
    
    while True:
        video_path = input("\nMasukkan path video: ").strip()
        
        if video_path.lower() == 'quit':
            break
            
        # Remove quotes if present
        video_path = video_path.strip('"').strip("'")
        
        if video_path:
            test_video_loading(video_path)
            
    print("Test selesai!")