"""Generate simple PNG icons for the Mnemosyne Chrome extension."""
import struct
import zlib
import os

def create_png(size, filepath):
    """Create a simple PNG icon with a purple gradient background and white 'M'."""
    width = height = size
    
    # Create pixel data (RGBA)
    pixels = []
    for y in range(height):
        row = []
        for x in range(width):
            # Verdigris-to-brass gradient background
            t = (x + y) / (width + height)
            r = int(63 + (181 - 63) * t)    # 3F -> B5
            g = int(143 + (138 - 143) * t)  # 8F -> 8A
            b = int(132 + (58 - 132) * t)   # 84 -> 3A
            a = 255
            
            # Rounded corners
            corner_radius = size * 0.2
            in_corner = False
            for cx, cy in [(corner_radius, corner_radius), 
                          (width - corner_radius, corner_radius),
                          (corner_radius, height - corner_radius),
                          (width - corner_radius, height - corner_radius)]:
                dx = abs(x - cx)
                dy = abs(y - cy)
                if x < corner_radius or x > width - corner_radius:
                    if y < corner_radius or y > height - corner_radius:
                        if dx * dx + dy * dy > corner_radius * corner_radius:
                            a = 0
                            in_corner = True
            
            # Draw 'M' letter (simple bitmap approach)
            margin = size * 0.2
            letter_top = size * 0.25
            letter_bottom = size * 0.75
            stroke = max(2, size // 8)
            
            in_letter = False
            if letter_top <= y <= letter_bottom and not in_corner:
                # Left vertical bar
                if margin <= x <= margin + stroke:
                    in_letter = True
                # Right vertical bar
                elif width - margin - stroke <= x <= width - margin:
                    in_letter = True
                # Left diagonal
                elif margin + stroke < x < width / 2:
                    expected_y = letter_top + (y - letter_top)
                    slope_x = margin + stroke + (x - margin - stroke)
                    target_y = letter_top + (slope_x - margin - stroke) / (width/2 - margin - stroke) * (letter_bottom - letter_top) * 0.5
                    if abs(y - target_y) < stroke:
                        in_letter = True
                # Right diagonal
                elif width / 2 <= x < width - margin - stroke:
                    slope_x = x - width/2
                    target_y = letter_top + (letter_bottom - letter_top) * 0.5 - slope_x / (width/2 - margin - stroke) * (letter_bottom - letter_top) * 0.5
                    if abs(y - target_y) < stroke:
                        in_letter = True
            
            if in_letter and a > 0:
                r, g, b = 255, 255, 255
            
            row.extend([r, g, b, a])
        pixels.append(bytes([0] + row))  # filter byte + row data
    
    raw_data = b''.join(pixels)
    
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
    
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)
    
    # IDAT
    compressed = zlib.compress(raw_data)
    idat = make_chunk(b'IDAT', compressed)
    
    # IEND
    iend = make_chunk(b'IEND', b'')
    
    with open(filepath, 'wb') as f:
        f.write(signature + ihdr + idat + iend)
    
    print(f"Created {filepath} ({size}x{size})")

if __name__ == "__main__":
    icon_dir = os.path.join(os.path.dirname(__file__), "icons")
    os.makedirs(icon_dir, exist_ok=True)
    
    for size in [16, 48, 128]:
        create_png(size, os.path.join(icon_dir, f"icon{size}.png"))
    
    print("Done! Icons created.")
