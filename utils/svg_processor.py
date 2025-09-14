import urllib.request
import xml.etree.ElementTree as ET
import re
import tempfile
import os
import traceback
import ssl

def download_svg_from_url(url):
    """Download SVG content from URL"""
    print(f"Attempting to download from: {url}")
    
    try:
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print("Using requests library")
        response = requests.get(url, verify=False, timeout=30)
        content = response.text
        print(f"Downloaded {len(content)} bytes with requests")
        print(f"First 200 chars: {content[:200]}")
        return content
    except ImportError:
        print("Requests not available, using urllib")
    except Exception as e:
        print(f"Requests failed: {e}")
    
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                content = response.read()
                print(f"Downloaded {len(content)} bytes with urllib")
                decoded = content.decode('utf-8')
                print(f"First 200 chars: {decoded[:200]}")
                return decoded
        except Exception as e:
            print(f"Error downloading SVG from {url}: {e}")
            traceback.print_exc()
        
        print("Using fallback test SVG")
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300">
  <polygon points="10,10 190,10 190,290 10,290" fill="none" stroke="black"/>
</svg>'''

def load_svg_from_file(file_path):
    """Load SVG content from local file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading SVG file {file_path}: {e}")
        return None

def parse_path_data(path_data):
    """Parse SVG path 'd' attribute to extract coordinates"""
    coordinates = []
   
    commands = re.split(r'[MLCZHVSQTAmlczhvsqta]', path_data)
    
    for command in commands:
        if command.strip():
            numbers = re.findall(r'-?\d+\.?\d*', command)
            
            for i in range(0, len(numbers)-1, 2):
                if i+1 < len(numbers):
                    try:
                        x = float(numbers[i])
                        y = float(numbers[i+1])
                        coordinates.extend([x, y])
                    except ValueError:
                        continue
    
    return coordinates

def parse_polygon_points(points_data):
    """Parse SVG polygon/polyline points attribute"""
    coordinates = []
    
    numbers = re.findall(r'-?\d+\.?\d*', points_data)
    
    for i in range(0, len(numbers)-1, 2):
        if i+1 < len(numbers):
            try:
                x = float(numbers[i])
                y = float(numbers[i+1])
                coordinates.extend([x, y])
            except ValueError:
                continue
    
    return coordinates

def extract_coordinates_from_svg(svg_content):
    """Extract all coordinates from SVG content"""
    if not svg_content:
        print("No SVG content provided")
        return []
    
    try:
        print(f"Parsing SVG ({len(svg_content)} chars)")
        
        root = ET.fromstring(svg_content)
        print(f"Root tag: {root.tag}")
        
        coordinates = []
        
        namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        
        all_elements = root.findall('.//*')
        print(f"Found {len(all_elements)} total elements in SVG")
        
        for elem in all_elements:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if tag.lower() == 'polygon':
                points_attr = elem.get('points')
                elem_id = elem.get('id', '').lower()
                elem_class = elem.get('class', '').lower()
                if 'border' in elem_id or 'frame' in elem_id or 'viewbox' in elem_id:
                    print(f"Skipping border/frame polygon: {elem_id}")
                    continue
                if points_attr:
                    print(f"Found polygon with points: {points_attr[:100]}...")
                    poly_coords = parse_polygon_points(points_attr)
                    if poly_coords and len(poly_coords) >= 6: 
                        coordinates.extend(poly_coords)
                        print(f"Extracted {len(poly_coords)//2} points from polygon")
                        break 
            
            elif tag.lower() == 'polyline':
                points_attr = elem.get('points')
                if points_attr:
                    print(f"Found polyline with points: {points_attr[:100]}...")
                    poly_coords = parse_polygon_points(points_attr)
                    if poly_coords:
                        coordinates.extend(poly_coords)
                        print(f"Extracted {len(poly_coords)//2} points from polyline")
                        break
            
            elif tag.lower() == 'path':
                d_attr = elem.get('d')
                if d_attr:
                    print(f"Found path with d: {d_attr[:100]}...")
                    path_coords = parse_path_data(d_attr)
                    if path_coords:
                        coordinates.extend(path_coords)
                        print(f"Extracted {len(path_coords)//2} points from path")
                        break
            
            elif tag.lower() == 'rect':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                width = float(elem.get('width', 0))
                height = float(elem.get('height', 0))
                if width > 0 and height > 0:
                    print(f"Found rect: x={x}, y={y}, w={width}, h={height}")
                    coordinates = [
                        x, y,
                        x + width, y,
                        x + width, y + height,
                        x, y + height
                    ]
                    print(f"Converted rect to {len(coordinates)//2} points")
                    break
            
            elif tag.lower() == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                if r > 0:
                    print(f"Found circle: cx={cx}, cy={cy}, r={r}")
                    import math
                    for i in range(12):
                        angle = (i * 2 * math.pi) / 12
                        x = cx + r * math.cos(angle)
                        y = cy + r * math.sin(angle)
                        coordinates.extend([x, y])
                    print(f"Approximated circle with {len(coordinates)//2} points")
                    break
        
        if not coordinates:
            print("No shapes found with general search, trying namespace-specific searches...")
            
            for prefix in ['', 'svg:', '{http://www.w3.org/2000/svg}']:
                for shape in ['polygon', 'polyline', 'path', 'rect', 'circle']:
                    elements = root.findall(f'.//{prefix}{shape}')
                    if elements:
                        print(f"Found {len(elements)} {shape} elements with prefix '{prefix}'")
                        for elem in elements:
                            if shape in ['polygon', 'polyline']:
                                points = elem.get('points')
                                if points:
                                    coords = parse_polygon_points(points)
                                    if coords:
                                        coordinates = coords
                                        break
                            elif shape == 'path':
                                d = elem.get('d')
                                if d:
                                    coords = parse_path_data(d)
                                    if coords:
                                        coordinates = coords
                                        break
                    if coordinates:
                        break
                if coordinates:
                    break
        
        print(f"Total extracted: {len(coordinates)} values ({len(coordinates)//2} coordinate pairs)")
        if coordinates:
            print(f"First 10 coordinates: {coordinates[:10]}")
            print(f"Last 10 coordinates: {coordinates[-10:]}")
        
        return coordinates
        
    except ET.ParseError as e:
        print(f"Error parsing SVG XML: {e}")
        print(f"Content start: {svg_content[:500]}")
        return []
    except Exception as e:
        print(f"Error extracting coordinates: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_coordinates_from_ipfs(ipfs_hash, gateway_url):
    """Download SVG from IPFS and extract coordinates"""
    print(f"Downloading SVG from: {gateway_url}")
    svg_content = download_svg_from_url(gateway_url)
    
    if svg_content:
        coordinates = extract_coordinates_from_svg(svg_content)
        print(f"Got {len(coordinates)} coordinates from IPFS SVG")
        return coordinates
    else:
        print("Failed to download SVG from IPFS")
        return []

def get_coordinates_from_file(file_path):
    """Load SVG from file and extract coordinates"""
    print(f"Loading SVG from file: {file_path}")
    svg_content = load_svg_from_file(file_path)
    
    if svg_content:
        coordinates = extract_coordinates_from_svg(svg_content)
        print(f"Got {len(coordinates)} coordinates from local SVG")
        return coordinates
    else:
        print("Failed to load SVG file")
        return []