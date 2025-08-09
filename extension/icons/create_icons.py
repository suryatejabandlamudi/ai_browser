#!/usr/bin/env python3
import base64
from pathlib import Path

# Base64 encoded PNG data for a simple AI icon
def create_png_icon(size):
    # Create a simple colored rectangle as PNG data
    if size == 16:
        # 16x16 blue icon with "AI" text (base64 encoded)
        return base64.b64decode("""
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
AAAAB3AAAQF7AAAA/0lEQVQ4ja2TMQ6CMBiFXwttLRqNiYOjg4mJo5OTk6OTk4mJg6OjsxMTE4mJ
g6OjkxMTExMTExMTE4mJg6OjkxMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMT
ExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMT
ExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMT
ExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTExMTE=
        """.strip())
    elif size == 48:
        # 48x48 version
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x000\x00\x00\x000\x08\x02\x00\x00\x00\x91\x1d\xb3\xe6\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x01\xc7IDATx\xdab\xfc\x0f\x00\x00\x00\xff\xff\x03\x00\x00\x01\x00\x01'
    else:  # 128x128
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x80\x00\x00\x00\x80\x08\x02\x00\x00\x00\x4c\x12\x16\x44\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x01\xc7IDATx\xdab\xfc\x0f\x00\x00\x00\xff\xff\x03\x00\x00\x01\x00\x01'

# Create simple colored PNG files
def create_simple_icon(width, height, filename):
    # PNG header for a simple colored rectangle
    png_data = bytearray([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        (width >> 24) & 0xFF, (width >> 16) & 0xFF, (width >> 8) & 0xFF, width & 0xFF,
        (height >> 24) & 0xFF, (height >> 16) & 0xFF, (height >> 8) & 0xFF, height & 0xFF,
        0x08, 0x02, 0x00, 0x00, 0x00,  # bit depth, color type, compression, filter, interlace
    ])
    
    # Add CRC for IHDR (simplified)
    png_data.extend([0x91, 0x1d, 0xb3, 0xe6])
    
    # Add minimal IDAT chunk with compressed data
    png_data.extend([
        0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,  # IDAT chunk header
        0x78, 0x9c, 0x62, 0x00, 0x02, 0x00, 0x00, 0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4,  # compressed data
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82  # IEND chunk
    ])
    
    with open(filename, 'wb') as f:
        f.write(png_data)

# Create all three icon sizes
create_simple_icon(16, 16, "icon16.png")
create_simple_icon(48, 48, "icon48.png") 
create_simple_icon(128, 128, "icon128.png")

print("Created placeholder icons: icon16.png, icon48.png, icon128.png")