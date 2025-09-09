#!/usr/bin/env python3
"""
Demo script untuk testing Studio Media Player.
Membuat sample files untuk testing berbagai format.
"""

import os
import numpy as np
from PIL import Image
import cv2

def create_demo_files():
    """Create demo files for testing."""
    demo_dir = "demo_files"
    os.makedirs(demo_dir, exist_ok=True)
    
    print("Creating demo files...")
    
    # Create sample JPG
    create_sample_image(os.path.join(demo_dir, "sample.jpg"), "JPEG")
    
    # Create sample PNG
    create_sample_image(os.path.join(demo_dir, "sample.png"), "PNG")
    
    # Create animated sequence (as individual frames)
    create_frame_sequence(demo_dir)
    
    print(f"Demo files created in '{demo_dir}' directory")
    print("You can now test the media player with these files!")

def create_sample_image(filepath, format_type):
    """Create a sample image file."""
    # Create colorful gradient image
    width, height = 800, 600
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create gradient
    for y in range(height):
        for x in range(width):
            image[y, x] = [
                int(255 * x / width),      # Red gradient
                int(255 * y / height),     # Green gradient
                int(255 * (x + y) / (width + height))  # Blue gradient
            ]
    
    # Add some text
    cv2.putText(image, f"Studio Media Player", (50, 100), 
               cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.putText(image, f"Sample {format_type} File", (50, 200), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    cv2.putText(image, f"{width}x{height}", (50, 300), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
    
    # Convert BGR to RGB for PIL
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    pil_image.save(filepath, format=format_type, quality=95)
    print(f"Created: {filepath}")

def create_frame_sequence(demo_dir):
    """Create a sequence of frames to simulate video."""
    frames_dir = os.path.join(demo_dir, "frame_sequence")
    os.makedirs(frames_dir, exist_ok=True)
    
    width, height = 640, 480
    num_frames = 30
    
    for frame_num in range(num_frames):
        # Create animated circle
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image.fill(50)  # Dark background
        
        # Animated circle position
        center_x = int(width/2 + 200 * np.sin(2 * np.pi * frame_num / num_frames))
        center_y = height // 2
        radius = 30
        color = (
            int(255 * (frame_num / num_frames)),
            int(255 * (1 - frame_num / num_frames)),
            128
        )
        
        cv2.circle(image, (center_x, center_y), radius, color, -1)
        
        # Frame number
        cv2.putText(image, f"Frame {frame_num + 1:02d}/{num_frames}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Save frame
        frame_path = os.path.join(frames_dir, f"frame_{frame_num+1:03d}.jpg")
        cv2.imwrite(frame_path, image)
    
    print(f"Created {num_frames} frames in: {frames_dir}")

if __name__ == "__main__":
    create_demo_files()
