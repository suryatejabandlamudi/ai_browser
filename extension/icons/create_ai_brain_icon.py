#!/usr/bin/env python3
"""
Create AI Brain Icon for the AI Browser Extension
Creates a modern brain/AI-themed icon to replace the default Chrome icon
"""

from PIL import Image, ImageDraw
import os

def create_ai_brain_icon():
    """Create a brain/AI themed icon for the browser extension"""
    
    # Create icons at different sizes
    sizes = [16, 48, 128]
    
    for size in sizes:
        # Create new image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate proportional dimensions
        center_x, center_y = size // 2, size // 2
        brain_width = int(size * 0.8)
        brain_height = int(size * 0.65)
        
        # AI Brain color scheme - modern purple/blue gradient
        if size >= 48:
            # Larger icons get gradient effect
            colors = [
                (138, 43, 226),   # Blue violet
                (75, 0, 130),     # Indigo  
                (147, 0, 211),    # Dark violet
                (123, 104, 238),  # Medium slate blue
            ]
        else:
            # Smaller icons use single color for clarity
            colors = [(138, 43, 226)]
        
        # Draw brain outline
        brain_left = center_x - brain_width // 2
        brain_top = center_y - brain_height // 2 
        brain_right = brain_left + brain_width
        brain_bottom = brain_top + brain_height
        
        # Main brain shape (oval)
        draw.ellipse([brain_left, brain_top, brain_right, brain_bottom], 
                     fill=colors[0], outline=(255, 255, 255, 180), width=max(1, size//32))
        
        if size >= 48:
            # Add brain hemisphere division line
            draw.line([(center_x, brain_top + size//8), (center_x, brain_bottom - size//8)], 
                     fill=(255, 255, 255, 160), width=max(1, size//24))
            
            # Add neural network nodes (circles)
            node_size = size // 16
            nodes = [
                (center_x - brain_width//4, center_y - brain_height//4),
                (center_x + brain_width//4, center_y - brain_height//4),
                (center_x - brain_width//3, center_y + brain_height//6),
                (center_x + brain_width//3, center_y + brain_height//6),
                (center_x, center_y)
            ]
            
            for x, y in nodes:
                draw.ellipse([x-node_size, y-node_size, x+node_size, y+node_size], 
                            fill=(255, 255, 255, 200))
            
            # Connect nodes with lines (neural connections)
            connections = [
                (nodes[0], nodes[4]),  # Left top to center
                (nodes[1], nodes[4]),  # Right top to center  
                (nodes[2], nodes[4]),  # Left bottom to center
                (nodes[3], nodes[4]),  # Right bottom to center
                (nodes[0], nodes[2]),  # Left side
                (nodes[1], nodes[3]),  # Right side
            ]
            
            for start, end in connections:
                draw.line([start, end], fill=(255, 255, 255, 120), width=max(1, size//48))
        
        if size >= 128:
            # Large icon gets extra AI elements
            # Add small "AI" text or circuit pattern
            circuit_color = (255, 255, 255, 100)
            
            # Draw small circuit lines around the brain
            margin = size // 10
            draw.rectangle([margin, margin, margin + size//20, margin + size//15], 
                         fill=circuit_color)
            draw.rectangle([size - margin - size//20, margin, size - margin, margin + size//15], 
                         fill=circuit_color)
            
            # Add small glowing effect
            glow_color = (255, 255, 255, 60)
            draw.ellipse([brain_left - 2, brain_top - 2, brain_right + 2, brain_bottom + 2],
                        outline=glow_color, width=2)
        
        # Save the icon
        icon_path = f'/Volumes/ssd/apple/ai_browser/extension/icons/icon{size}.png'
        img.save(icon_path, 'PNG')
        print(f'Created {icon_path}')
        
        # Also save to root for browser build
        if size == 48:
            browser_icon_path = f'/Volumes/ssd/apple/ai_browser/ai_browser_icon.png'
            img.save(browser_icon_path, 'PNG')
            print(f'Created browser icon: {browser_icon_path}')
    
    print('✅ AI Brain icons created successfully!')
    print('🧠 Modern purple/blue brain with neural network design')
    print('⚡ Represents local AI intelligence and connectivity')

if __name__ == "__main__":
    create_ai_brain_icon()