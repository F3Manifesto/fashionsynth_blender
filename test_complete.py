
import bpy
import os
import urllib.request
import json
import ssl
import re
import math
import bmesh
import mathutils
import xml.etree.ElementTree as ET
import traceback
from mathutils import Vector




bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)


INFURA_GATEWAY = "https://thedial.infura-ipfs.io/ipfs/"

HOODIE_DEFAULTS = {
   "front_panel": {
        "ipfs": "QmWwRYcuyNeXzNFbFHn6NomxerQJH7gpdv337uNkygvS3u",
        "quantity": 1,
        "display_name": "Front Panel",
        "description": "Front panel pattern piece for hoodie with fold cutting line"
    },
  "back_panel":  {
        "ipfs": "QmYpqS8Bvooy8VZuyYB4QCa4AEzyiKYaevLZxTMdSKQ8LW",
        "quantity": 1,
        "display_name": "Back Panel",
        "description": "Back panel pattern piece for hoodie with fold cutting line"
    },
    "hood":  {
        "ipfs": "QmZCiFkntv59eDymtZKpLbFuy1HHVBgWk7YxJbousgUhmE",
        "quantity": 2,
        "display_name": "Hood",
        "description": "Hood pattern piece for hoodie"
    },
      "pocket":  {
        "ipfs": "QmeRcLaAJt2tMEtc6fQs4awzZJHPLUGkGsk7sM4FijBa2S",
        "quantity": 1,
        "display_name": "Pocket",
        "description": "Pocket pattern piece for hoodie"
    },
      "sleeve_cuff":  {
        "ipfs": "QmR2aM7nPH6PmswKc4115GhdxbCEhwDhFAUqXBGrDZuCws",
        "quantity": 2,
        "display_name": "Sleeve Cuff",
        "description": "Sleeve cuff pattern piece for hoodie"
    },
      "sleeve":  {
        "ipfs": "QmTEAfKjAnJ8Rm7BwgzGCtb1wE5H9J3BkSoEFgeBCeHU2a",
        "quantity": 2,
        "display_name": "Sleeve",
        "description": "Sleeve pattern piece for hoodie"
    },
      "waist_band":  {
        "ipfs": "QmZQFmPophwckf4UKDCD5YMLPeism2oYNkrgFhN33N52Q6",
        "quantity": 1,
        "display_name": "Waist Band",
        "description": "Waist band pattern piece for hoodie"
    }
}

def get_garment_defaults(garment_type):
    garment_map = {
        "hoodie": HOODIE_DEFAULTS,
    }
    return garment_map.get(garment_type, {})

def ipfs_to_gateway_url(ipfs_hash):
    if ipfs_hash.startswith("ipfs://"):
        hash_only = ipfs_hash.replace("ipfs://", "")
    else:
        hash_only = ipfs_hash
    return f"{INFURA_GATEWAY}{hash_only}"


def download_svg_from_url(url):
    """Download SVG content from URL"""
    
    try:
        import requests
        response = requests.get(url, verify=False, timeout=30)
        content = response.text
     
        return content
    except ImportError:
        print("Requests not available, using urllib")
    except Exception as e:
        print(f"Requests failed: {e}")
    
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
            decoded = content.decode('utf-8')
            return decoded
    except Exception as e:
        traceback.print_exc()
        

def load_svg_from_file(file_path):
    """Load SVG content from local file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
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
        return []
    
    try:
        
        root = ET.fromstring(svg_content)
        
        coordinates = []
        
        namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        
        all_elements = root.findall('.//*')
        
        for elem in all_elements:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if tag.lower() == 'polygon':
                points_attr = elem.get('points')
                elem_id = elem.get('id', '').lower()
                elem_class = elem.get('class', '').lower()
                if 'border' in elem_id or 'frame' in elem_id or 'viewbox' in elem_id:
                    continue
                if points_attr:
                    poly_coords = parse_polygon_points(points_attr)
                    if poly_coords and len(poly_coords) >= 6: 
                        coordinates.extend(poly_coords)
                        break 
            
            elif tag.lower() == 'polyline':
                points_attr = elem.get('points')
                if points_attr:
                    poly_coords = parse_polygon_points(points_attr)
                    if poly_coords:
                        coordinates.extend(poly_coords)
                        break
            
            elif tag.lower() == 'path':
                d_attr = elem.get('d')
                if d_attr:
                    path_coords = parse_path_data(d_attr)
                    if path_coords:
                        coordinates.extend(path_coords)
                        break
            
            elif tag.lower() == 'rect':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                width = float(elem.get('width', 0))
                height = float(elem.get('height', 0))
                if width > 0 and height > 0:
                    coordinates = [
                        x, y,
                        x + width, y,
                        x + width, y + height,
                        x, y + height
                    ]
                    break
            
            elif tag.lower() == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                if r > 0:
                    import math
                    for i in range(12):
                        angle = (i * 2 * math.pi) / 12
                        x = cx + r * math.cos(angle)
                        y = cy + r * math.sin(angle)
                        coordinates.extend([x, y])
                    break
        
        if not coordinates:
            
            for prefix in ['', 'svg:', '{http://www.w3.org/2000/svg}']:
                for shape in ['polygon', 'polyline', 'path', 'rect', 'circle']:
                    elements = root.findall(f'.//{prefix}{shape}')
                    if elements:
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
        
        return coordinates
        
    except ET.ParseError as e:
        return []
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

def get_coordinates_from_ipfs(ipfs_hash, gateway_url):
    """Download SVG from IPFS and extract coordinates"""
    svg_content = download_svg_from_url(gateway_url)
    
    if svg_content:
        coordinates = extract_coordinates_from_svg(svg_content)
        return coordinates
    else:
        return []

def get_coordinates_from_file(file_path):
    """Load SVG from file and extract coordinates"""
    svg_content = load_svg_from_file(file_path)
    
    if svg_content:
        coordinates = extract_coordinates_from_svg(svg_content)
        return coordinates
    else:
        return []

def selectAll(vertices):
    for vert in vertices:
        vert.select = True

def unSelectAll(vertices):
    for vert in vertices:
        vert.select = False

def detect_bottom_and_fold_edges(coordinates):
    """Detect shortest edge (bottom) and longest edge (fold line) with required rotations
    
    In Blender mapping: SVG X -> Blender X, SVG Y -> Blender Z
    We want shortest edge to face FRONT on Blender Y-axis (negative Y)
    """
    if len(coordinates) < 6:
        return 'horizontal', 'vertical', 0
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1])) 
    
    straight_edges = []
    
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        x_diff = abs(p2[0] - p1[0])  
        y_diff = abs(p2[1] - p1[1])  
        length = math.sqrt(x_diff**2 + y_diff**2)
        
        if x_diff < 5 and y_diff > 10: 
            straight_edges.append(('svg_vertical', length, p1, p2))
        elif y_diff < 5 and x_diff > 10: 
            straight_edges.append(('svg_horizontal', length, p1, p2))
    
    if len(straight_edges) < 2:
        return 'svg_horizontal', 'svg_vertical', 0
    
    shortest_edge = min(straight_edges, key=lambda x: x[1])
    bottom_orientation, bottom_length, _, _ = shortest_edge
    
    longest_edge = max(straight_edges, key=lambda x: x[1])
    fold_orientation, fold_length, _, _ = longest_edge
    
    
 
    rotation_needed = 0
    if bottom_orientation == 'svg_vertical':
        rotation_needed = 90
        fold_orientation = 'svg_horizontal' if fold_orientation == 'svg_vertical' else 'svg_vertical'
        bottom_orientation = 'svg_horizontal'  
    
    return bottom_orientation, fold_orientation, rotation_needed

def rotate_coordinates(coordinates, rotation_degrees):
    """Rotate coordinates by specified degrees around center"""
    if rotation_degrees == 0:
        return coordinates
    
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    center_x = sum(p[0] for p in points) / len(points)
    center_y = sum(p[1] for p in points) / len(points)
    
    angle = math.radians(rotation_degrees)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    
    rotated_points = []
    for x, y in points:
        x_centered = x - center_x
        y_centered = y - center_y
        
        x_rotated = x_centered * cos_angle - y_centered * sin_angle
        y_rotated = x_centered * sin_angle + y_centered * cos_angle
        
        x_final = x_rotated + center_x
        y_final = y_rotated + center_y
        
        rotated_points.append((x_final, y_final))
    
    rotated_coordinates = []
    for x, y in rotated_points:
        rotated_coordinates.extend([x, y])
    
    return rotated_coordinates

def detect_bottom_edge(coordinates):
    """Detect bottom edge (longest straight horizontal line)"""
    if len(coordinates) < 6:
        return None
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    longest_horizontal_line = None
    max_length = 0
    
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        y_diff = abs(p2[1] - p1[1])
        x_diff = abs(p2[0] - p1[0])
        
        if y_diff < 5 and x_diff > max_length:  
            max_length = x_diff
            longest_horizontal_line = (p1, p2)
    
    if longest_horizontal_line:
        return longest_horizontal_line
    return None

def orient_pocket_coordinates(coordinates, part_name):
    if 'pocket' not in part_name.lower():
        return coordinates
    
    
    bottom_orientation, fold_orientation, rotation_needed = detect_bottom_and_fold_edges(coordinates)
    
    if rotation_needed != 0:
        coordinates = rotate_coordinates(coordinates, rotation_needed)
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    straight_edges = []
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        x_diff = abs(p2[0] - p1[0])
        y_diff = abs(p2[1] - p1[1])
        length = math.sqrt(x_diff**2 + y_diff**2)
        
        if y_diff < 5 and x_diff > 10:
            avg_y = (p1[1] + p2[1]) / 2
            straight_edges.append((length, avg_y))
    
    if straight_edges:
        shortest_edge_length, shortest_edge_y = min(straight_edges, key=lambda x: x[0])
        
        if shortest_edge_y > (min_y + max_y) / 2:
            coordinates = rotate_coordinates(coordinates, 180)
    
    return coordinates


def orient_cuff_coordinates(coordinates, part_name):
    if 'cuff' not in part_name.lower():
        return coordinates
    
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    straight_edges = []
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        x_diff = abs(p2[0] - p1[0])  
        y_diff = abs(p2[1] - p1[1])  
        length = math.sqrt(x_diff**2 + y_diff**2)
        
        if x_diff < 5 and y_diff > 10:
            straight_edges.append(('svg_vertical', length, p1, p2))
        elif y_diff < 5 and x_diff > 10:
            straight_edges.append(('svg_horizontal', length, p1, p2))
    
    if len(straight_edges) < 2:
        return coordinates
    
    longest_edge = max(straight_edges, key=lambda x: x[1])
    longest_orientation, longest_length, p1, p2 = longest_edge
    
    
    rotation_needed = 0
    if longest_orientation == 'svg_vertical':
        rotation_needed = 90
        coordinates = rotate_coordinates(coordinates, rotation_needed)
        
        points = []
        for i in range(0, len(coordinates)-1, 2):
            if i+1 < len(coordinates):
                points.append((coordinates[i], coordinates[i+1]))
    
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    horizontal_edges = []
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        x_diff = abs(p2[0] - p1[0])
        y_diff = abs(p2[1] - p1[1])
        length = math.sqrt(x_diff**2 + y_diff**2)
        
        if y_diff < 5 and x_diff > 10:
            avg_y = (p1[1] + p2[1]) / 2
            horizontal_edges.append((length, avg_y))
    
    if horizontal_edges:
        longest_edge_length, longest_edge_y = max(horizontal_edges, key=lambda x: x[0])
        
        if longest_edge_y > (min_y + max_y) / 2:
            coordinates = rotate_coordinates(coordinates, 180)
    
    return coordinates

def orient_waistband_coordinates(coordinates, part_name):
    if 'waist_band' not in part_name.lower():
        return coordinates
    
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    straight_edges = []
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        x_diff = abs(p2[0] - p1[0])
        y_diff = abs(p2[1] - p1[1])
        length = math.sqrt(x_diff**2 + y_diff**2)
        
        if y_diff < 5 and x_diff > 10:
            straight_edges.append(('svg_horizontal', length, p1, p2))
        elif x_diff < 5 and y_diff > 10:
            straight_edges.append(('svg_vertical', length, p1, p2))
    
    if straight_edges:
        longest_edge = max(straight_edges, key=lambda x: x[1])
        longest_orientation, longest_length, p1, p2 = longest_edge
        
        
        if longest_orientation == 'svg_vertical':
            coordinates = rotate_coordinates(coordinates, 90)
        
        points = []
        for i in range(0, len(coordinates)-1, 2):
            if i+1 < len(coordinates):
                points.append((coordinates[i], coordinates[i+1]))
        
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        straight_edges_after = []
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            p1, p2 = points[i], points[next_i]
            
            x_diff = abs(p2[0] - p1[0])
            y_diff = abs(p2[1] - p1[1])
            length = math.sqrt(x_diff**2 + y_diff**2)
            
            if y_diff < 5 and x_diff > 10:
                avg_y = (p1[1] + p2[1]) / 2
                straight_edges_after.append((length, avg_y))
        
        if straight_edges_after:
            longest_edge_length, longest_edge_y = max(straight_edges_after, key=lambda x: x[0])
            
            if longest_edge_y < (min_y + max_y) / 2:
                coordinates = rotate_coordinates(coordinates, 180)

    
    return coordinates

def create_full_panel_coordinates(coordinates, part_name):
    """Create full panel by mirroring - ONLY FOR PANELS"""
    if "front_panel" in part_name.lower():
        pass
    elif "back_panel" in part_name.lower():
        pass
    elif "pocket" in part_name.lower():
        return orient_pocket_coordinates(coordinates, part_name)
    elif "sleeve" in part_name.lower() and not "cuff" in part_name.lower():
        return coordinates
    elif "sleeve_cuff" in part_name.lower():
        return orient_cuff_coordinates(coordinates, part_name)
    elif "waist_band" in part_name.lower():
        return orient_waistband_coordinates(coordinates, part_name)
    elif "hood" in part_name.lower():
        return orient_pocket_coordinates(coordinates, part_name)
    else:
        return coordinates
    
    
    bottom_orientation, fold_orientation, rotation_needed = detect_bottom_and_fold_edges(coordinates)
    
    if rotation_needed != 0:
        coordinates = rotate_coordinates(coordinates, rotation_needed)
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    straight_edges = []
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1, p2 = points[i], points[next_i]
        
        x_diff = abs(p2[0] - p1[0])
        y_diff = abs(p2[1] - p1[1])
        length = math.sqrt(x_diff**2 + y_diff**2)
        
        if y_diff < 5 and x_diff > 10:
            straight_edges.append(('horizontal', length, p1, p2))
        elif x_diff < 5 and y_diff > 10:
            straight_edges.append(('vertical', length, p1, p2))
    
    if len(straight_edges) >= 2:
        longest_edge = max(straight_edges, key=lambda x: x[1])
        longest_orientation, longest_length, longest_p1, longest_p2 = longest_edge
        
        
        if longest_orientation == 'horizontal':
            fold_y = (longest_p1[1] + longest_p2[1]) / 2
            
            mirrored_points = []
            for x, y in points:
                mirrored_y = 2 * fold_y - y
                mirrored_points.append((x, mirrored_y))
        else:
            fold_x = (longest_p1[0] + longest_p2[0]) / 2
            
            mirrored_points = []
            for x, y in points:
                mirrored_x = 2 * fold_x - x
                mirrored_points.append((mirrored_x, y))
    else:
        mirrored_points = []
        for x, y in points:
            mirrored_points.append((x + 1.0, y))
    
    mirrored_points.reverse()
    full_points = points + mirrored_points
    
    full_coordinates = []
    for x, y in full_points:
        full_coordinates.extend([x, y])
    
    shortest_edge_length, shortest_edge_y = min(straight_edges, key=lambda x: x[1])[1:3]
    if len(straight_edges) >= 2:
        shortest_edge = min(straight_edges, key=lambda x: x[1])
        shortest_orientation, shortest_length, shortest_p1, shortest_p2 = shortest_edge
        shortest_edge_y = (shortest_p1[1] + shortest_p2[1]) / 2
        
        if shortest_edge_y > (min_y + max_y) / 2:
            full_coordinates_flipped = []
            full_points_reversed = []
            for i in range(0, len(full_coordinates)-1, 2):
                if i+1 < len(full_coordinates):
                    x, y = full_coordinates[i], full_coordinates[i+1]
                    full_points_reversed.append((x, y))
            
            center_x = sum(p[0] for p in full_points_reversed) / len(full_points_reversed)
            center_y = sum(p[1] for p in full_points_reversed) / len(full_points_reversed)
            
            for x, y in full_points_reversed:
                x_centered = x - center_x
                y_centered = y - center_y
                x_rotated = x_centered * -1 - y_centered * 0
                y_rotated = x_centered * 0 + y_centered * -1
                x_final = x_rotated + center_x
                y_final = y_rotated + center_y
                full_coordinates_flipped.extend([x_final, y_final])
            
            full_coordinates = full_coordinates_flipped
    
    return full_coordinates

def create_mesh_from_coordinates(coordinates, part_name, collection_name, scale_factor=None, preserve_position=False):
    """
    Create a mesh from SVG coordinates
    
    Args:
        coordinates: List of coordinates [x1, y1, x2, y2, ...]
        part_name: Name for the mesh object
        collection_name: Name of collection to add mesh to
        scale_factor: Factor to scale down coordinates (default 200)
        preserve_position: If True, don't center the mesh
    
    Returns:
        The created mesh object
    """
    
    if not coordinates or len(coordinates) < 6:  
        return None
    
    coordinates = create_full_panel_coordinates(coordinates, part_name)
    
    if scale_factor is None:
        max_coord = max(abs(c) for c in coordinates)
        if max_coord > 1000:
            scale_factor = 1000  
        elif max_coord > 100:
            scale_factor = 100  
        elif max_coord > 10:
            scale_factor = 10   
        else:
            scale_factor = 1    
    

    newVerts = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            x = float(coordinates[i]) / scale_factor    
            z = -float(coordinates[i+1]) / scale_factor  
            value = mathutils.Vector((x, 0, z))         
            newVerts.append(value)
    
    if newVerts:
        min_x = min(v.x for v in newVerts)
        max_x = max(v.x for v in newVerts)
        min_z = min(v.z for v in newVerts)
        max_z = max(v.z for v in newVerts)
        
        center_x = (min_x + max_x) / 2
        center_z = (min_z + max_z) / 2
        
        
        for v in newVerts:
            v.x -= center_x
            v.z -= center_z
    
    
    mesh = bpy.data.meshes.new(name=part_name)
    
    obj = bpy.data.objects.new(name=part_name, object_data=mesh)
    
    if collection_name in bpy.data.collections:
        col = bpy.data.collections[collection_name]
    else:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)
    
    col.objects.link(obj)
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    

    edges = []
    for i in range(len(newVerts)):
        if i == len(newVerts) - 1:
            edges.append([i, 0]) 
        else:
            edges.append([i, i+1])
    
    face = list(range(len(newVerts)))
    
    mesh.from_pydata(newVerts, edges, [face])
    mesh.update()
    
    return obj

def addMesh_compatible(array, name, collection_name):
    """
    Compatible version with original addMesh function signature
    """
    return create_mesh_from_coordinates(array, name, collection_name, scale_factor=200)

def markSeam(mesh_obj):
    """
    Mark all edges as seams
    """
    if not mesh_obj:
        return None
        
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.mesh.mark_seam(clear=False)

    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return mesh_obj


# ========== FROM pattern_layout.py ==========

def get_mesh_dimensions(mesh_obj):
    """Get the dimensions of a mesh object"""
    if not mesh_obj or not mesh_obj.data.vertices:
        return 0, 0, 0
    
    world_verts = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
    
    if not world_verts:
        return 0, 0, 0
    
    min_x = min(v.x for v in world_verts)
    max_x = max(v.x for v in world_verts)
    min_y = min(v.y for v in world_verts)
    max_y = max(v.y for v in world_verts)
    min_z = min(v.z for v in world_verts)
    max_z = max(v.z for v in world_verts)
    
    width = max_x - min_x
    height = max_y - min_y
    depth = max_z - min_z
    
    return width, height, depth

def arrange_pattern_layout(created_meshes, garment_type):
    """
    Arrange pattern pieces in a professional layout
    Based on traditional pattern cutting layouts
    """
    
    if not created_meshes:
        return
    
    
    HOODIE_LAYOUT = {
        "front_panel": {"row": 0, "col": 1, "priority": 1},
        "back_panel": {"row": 0, "col": 2, "priority": 1},
        
        "sleeve_1": {"row": 0, "col": 0, "priority": 2},
        "sleeve_2": {"row": 0, "col": 3, "priority": 2},
        
        "hood": {"row": 1, "col": 1, "priority": 3},
        "pocket": {"row": 1, "col": 2, "priority": 4},
        "waist_band": {"row": 2, "col": 1.5, "priority": 5},
        "sleeve_cuff": {"row": 2, "col": 0, "priority": 5},
    }
    
    TSHIRT_LAYOUT = {
        "front_panel": {"row": 0, "col": 1, "priority": 1},
        "back_panel": {"row": 0, "col": 2, "priority": 1},
        "sleeve_1": {"row": 0, "col": 0, "priority": 2},
        "sleeve_2": {"row": 0, "col": 3, "priority": 2},
        "neck_binding": {"row": 1, "col": 1.5, "priority": 3},
    }
    
    if garment_type == "hoodie":
        layout_rules = HOODIE_LAYOUT
    elif garment_type == "tshirt":
        layout_rules = TSHIRT_LAYOUT
    else:
        layout_rules = {}
    
    part_groups = {}
    for mesh in created_meshes:
        parts = mesh.name.split('_')
        if len(parts) >= 3:
            part_name = '_'.join(parts[1:-1])
        else:
            part_name = mesh.name
        
        if part_name not in part_groups:
            part_groups[part_name] = []
        part_groups[part_name].append(mesh)
    
    
    max_width = 0
    max_height = 0
    max_depth = 0
    
    for meshes in part_groups.values():
        for mesh in meshes:
            w, h, d = get_mesh_dimensions(mesh)
            max_width = max(max_width, w)
            max_height = max(max_height, h)
            max_depth = max(max_depth, d)
    
    spacing_x = max_width + 0.5
    spacing_z = max_depth + 0.5  
    
    
    positioned_parts = set()
    
    for part_name, meshes in part_groups.items():
        layout_rule = None
        
        if part_name in layout_rules:
            layout_rule = layout_rules[part_name]
        elif f"{part_name}_1" in layout_rules:
            layout_rule = layout_rules[f"{part_name}_1"]
        elif f"{part_name}_2" in layout_rules:
            layout_rule = layout_rules[f"{part_name}_2"]
        elif "sleeve" in part_name and "sleeve_cuff" not in part_name.to:
            if len(positioned_parts) % 2 == 0:
                layout_rule = layout_rules.get("sleeve_1", {"row": 0, "col": 0, "priority": 2})
            else:
                layout_rule = layout_rules.get("sleeve_2", {"row": 0, "col": 3, "priority": 2})
            positioned_parts.add("sleeve")
        
        if layout_rule:
            row = layout_rule["row"]
            col = layout_rule["col"]
            
            for i, mesh in enumerate(meshes):
                mesh.location.x = col * spacing_x
                mesh.location.y = 0 
                mesh.location.z = -row * spacing_z 
                
                if i > 0:
                    mesh.location.x += 0.2 * i
                    mesh.location.z += 0.2 * i
                
                mesh.rotation_euler[0] = 1.5708 
                mesh.rotation_euler[1] = 0
                mesh.rotation_euler[2] = 0
                
        else:
            for i, mesh in enumerate(meshes):
                mesh.location.x = len(positioned_parts) * spacing_x * 0.5
                mesh.location.y = 0
                mesh.location.z = -3 * spacing_z
                
                if i > 0:
                    mesh.location.x += 0.2 * i
                
                mesh.rotation_euler[0] = 1.5708
    
    if created_meshes:
        avg_x = sum(m.location.x for m in created_meshes) / len(created_meshes)
        avg_z = sum(m.location.z for m in created_meshes) / len(created_meshes)
        
        for mesh in created_meshes:
            mesh.location.x -= avg_x
            mesh.location.z -= avg_z
    

def create_pattern_table():
    """
    Optional: Create a cutting table/grid underneath the pattern pieces
    """
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, -0.1, 0))
    table = bpy.context.active_object
    table.name = "Cutting_Table"
    
    mat = bpy.data.materials.new(name="Table_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.5, 0.5, 0.5, 1.0)
    mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.5  
    mat.blend_method = 'BLEND'
    
    table.data.materials.append(mat)
    
    return table

# ========== POSITIONING METHODS FROM SynthGenerateGarment ==========

def find_longest_straight_edge(mesh_obj):
    """Find the longest straight edge in a mesh, returns axis, position, and coordinates"""
    
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bm.edges.ensure_lookup_table()
    
    edge_face_count = {}
    for face in bm.faces:
        for edge in face.edges:
            edge_key = tuple(sorted([edge.verts[0].index, edge.verts[1].index]))
            if edge_key not in edge_face_count:
                edge_face_count[edge_key] = 0
            edge_face_count[edge_key] += 1
    
    straight_edges = []
    tolerance = 0.001
    
    for edge in bm.edges:
        edge_key = tuple(sorted([v.index for v in edge.verts]))
        if edge_key not in edge_face_count or edge_face_count[edge_key] != 1:
            continue
            
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        
        x_diff = abs(v2.x - v1.x)
        y_diff = abs(v2.y - v1.y)
        z_diff = abs(v2.z - v1.z)
        
        edge_data = None
        
        if z_diff < tolerance and y_diff < tolerance and x_diff > tolerance:
            edge_data = {
                'axis': 'X',
                'length': x_diff,
                'position': 'top' if v1.z > 0 else 'bottom',
                'z_coord': v1.z,
                'x_coord': (v1.x + v2.x) / 2,
                'y_coord': v1.y
            }
        elif z_diff < tolerance and x_diff < tolerance and y_diff > tolerance:
            edge_data = {
                'axis': 'Y', 
                'length': y_diff,
                'position': 'front' if v1.y < 0 else 'back',
                'z_coord': v1.z,
                'x_coord': v1.x,
                'y_coord': (v1.y + v2.y) / 2
            }
        elif x_diff < tolerance and y_diff < tolerance and z_diff > tolerance:
            edge_data = {
                'axis': 'Z',
                'length': z_diff,
                'position': 'left' if v1.x < 0 else 'right',
                'z_coord': (v1.z + v2.z) / 2,
                'x_coord': v1.x,
                'y_coord': v1.y
            }
        
        if edge_data:
            straight_edges.append(edge_data)
    
    bm.free()
    
    if straight_edges:
        return max(straight_edges, key=lambda x: x['length'])
    return None


def find_shortest_straight_edge(mesh_obj):
    """Find the shortest straight edge in a mesh, returns axis, position, and coordinates"""
    
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    bm.edges.ensure_lookup_table()
    
    edge_face_count = {}
    for face in bm.faces:
        for edge in face.edges:
            edge_key = tuple(sorted([edge.verts[0].index, edge.verts[1].index]))
            if edge_key not in edge_face_count:
                edge_face_count[edge_key] = 0
            edge_face_count[edge_key] += 1
    
    straight_edges = []
    tolerance = 0.001
    
    for edge in bm.edges:
        edge_key = tuple(sorted([v.index for v in edge.verts]))
        if edge_key not in edge_face_count or edge_face_count[edge_key] != 1:
            continue
            
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        
        x_diff = abs(v2.x - v1.x)
        y_diff = abs(v2.y - v1.y)
        z_diff = abs(v2.z - v1.z)
        
        edge_data = None
        
        if z_diff < tolerance and y_diff < tolerance and x_diff > tolerance:
            edge_data = {
                'axis': 'X',
                'length': x_diff,
                'position': 'top' if v1.z > 0 else 'bottom',
                'z_coord': v1.z,
                'x_coord': (v1.x + v2.x) / 2,
                'y_coord': v1.y
            }
        elif z_diff < tolerance and x_diff < tolerance and y_diff > tolerance:
            edge_data = {
                'axis': 'Y', 
                'length': y_diff,
                'position': 'front' if v1.y < 0 else 'back',
                'z_coord': v1.z,
                'x_coord': v1.x,
                'y_coord': (v1.y + v2.y) / 2
            }
        elif x_diff < tolerance and y_diff < tolerance and z_diff > tolerance:
            edge_data = {
                'axis': 'Z',
                'length': z_diff,
                'position': 'left' if v1.x < 0 else 'right',
                'z_coord': (v1.z + v2.z) / 2,
                'x_coord': v1.x,
                'y_coord': v1.y
            }
        
        if edge_data:
            straight_edges.append(edge_data)
    
    bm.free()
    
    if straight_edges:
        return min(straight_edges, key=lambda x: x['length'])
    return None


def orient_panel_properly(mesh_obj, panel_type):
    """Orient front/back panel - intelligent logic for any SVG panel orientation
    Goal: From ANY starting orientation:
    - Longest straight edge should run horizontally along Y axis
    - Longest straight edge should face down (-Z direction)
    """
    
    longest = find_longest_straight_edge(mesh_obj)
    if not longest:
        print(f"Panel {panel_type}: ERROR - No longest edge found!")
        return
    
    print(f"Panel {panel_type}: Found longest edge on {longest['axis']} axis, length: {longest['length']:.3f}")
    print(f"Panel {panel_type}: Edge position - X:{longest['x_coord']:.3f}, Y:{longest['y_coord']:.3f}, Z:{longest['z_coord']:.3f}")
    print(f"Panel {panel_type}: Goal - longest edge on Y axis, facing -Z direction")
    
    # STEP 1: Intelligently rotate longest edge to Y axis
    print(f"STEP 1: Rotating longest edge from {longest['axis']} to Y axis...")
    
    if longest['axis'] != 'Y':
        if longest['axis'] == 'X':
            # X needs to become Y: rotate 90° around Z
            mesh_obj.rotation_euler[2] = 1.5708
            print(f"Applied: 90° rotation around Z (X → Y)")
        elif longest['axis'] == 'Z':
            # Z needs to become Y: rotate 90° around X
            mesh_obj.rotation_euler[0] = 1.5708
            print(f"Applied: 90° rotation around X (Z → Y)")
    else:
        print(f"No rotation needed - longest edge already on Y axis")
    
    # Update transformations
    bpy.context.view_layer.update()
    
    # STEP 2: Intelligently check and orient edge to face -Z direction
    print(f"STEP 2: Ensuring longest edge faces -Z direction...")
    
    # Re-detect longest edge after rotation to get new position
    longest_after = find_longest_straight_edge(mesh_obj)
    if longest_after:
        print(f"After rotation - Edge position: X:{longest_after['x_coord']:.3f}, Y:{longest_after['y_coord']:.3f}, Z:{longest_after['z_coord']:.3f}")
        
        # Check if edge is facing the correct direction (should be at negative Z)
        if longest_after['z_coord'] > 0:
            # Edge is at positive Z (top), need to flip to negative Z (bottom)
            mesh_obj.rotation_euler[0] += 3.14159  # 180° flip around X
            print(f"Applied: 180° flip around X to move edge to -Z")
        else:
            print(f"Edge already at -Z direction - good!")
            
        # Final verification
        bpy.context.view_layer.update()
        final_longest = find_longest_straight_edge(mesh_obj)
        if final_longest:
            print(f"Final edge position: X:{final_longest['x_coord']:.3f}, Y:{final_longest['y_coord']:.3f}, Z:{final_longest['z_coord']:.3f}")
            print(f"SUCCESS: Panel oriented - longest edge on Y axis at -Z direction")
    else:
        print(f"WARNING: Could not verify edge orientation after rotation!")  

def orient_waistband_properly(mesh_obj):
    """Orient waistband - intelligent logic for any SVG waistband orientation
    Goal: From ANY starting orientation:
    - Run horizontally along Y axis
    - Run vertically along Z axis
    - Will be positioned under front panel bottom edge
    """
    
    longest = find_longest_straight_edge(mesh_obj)
    if not longest:
        print(f"Waistband: ERROR - No longest edge found!")
        return
    
    print(f"Waistband: Found longest edge on {longest['axis']} axis, length: {longest['length']:.3f}")
    print(f"Waistband: Goal - run horizontally on Y, vertically on Z")
    
    # STEP 1: Intelligently rotate longest edge to Y axis (horizontal)
    print(f"STEP 1: Rotating longest edge from {longest['axis']} to Y axis...")
    
    if longest['axis'] != 'Y':
        if longest['axis'] == 'X':
            # X needs to become Y: rotate 90° around Z
            mesh_obj.rotation_euler[2] = 1.5708
            print(f"Applied: 90° rotation around Z (X → Y)")
        elif longest['axis'] == 'Z':
            # Z needs to become Y: rotate 90° around X
            mesh_obj.rotation_euler[0] = 1.5708
            print(f"Applied: 90° rotation around X (Z → Y)")
    else:
        print(f"No rotation needed - longest edge already on Y axis")
    
    # Update transformations
    bpy.context.view_layer.update()
    
    print(f"SUCCESS: Waistband oriented - runs horizontally on Y, vertically on Z")

def orient_pocket_properly(mesh_obj):
    """Orient pocket - intelligent logic for any SVG pocket orientation
    Goal: From ANY starting orientation:
    - Longest straight edge should run horizontally along Y axis
    - Longest straight edge should face down (-Z direction)
    """
    
    longest = find_longest_straight_edge(mesh_obj)
    if not longest:
        print(f"Pocket: ERROR - No longest edge found!")
        return
    
    print(f"Pocket: Found longest edge on {longest['axis']} axis, length: {longest['length']:.3f}")
    print(f"Pocket: Edge position - X:{longest['x_coord']:.3f}, Y:{longest['y_coord']:.3f}, Z:{longest['z_coord']:.3f}")
    print(f"Pocket: Goal - longest edge on Y axis, facing -Z direction")
    
    # STEP 1: Intelligently rotate longest edge to Y axis
    print(f"STEP 1: Rotating longest edge from {longest['axis']} to Y axis...")
    
    if longest['axis'] != 'Y':
        if longest['axis'] == 'X':
            # X needs to become Y: rotate 90° around Z
            mesh_obj.rotation_euler[2] = 1.5708
            print(f"Applied: 90° rotation around Z (X → Y)")
        elif longest['axis'] == 'Z':
            # Z needs to become Y: rotate 90° around X
            mesh_obj.rotation_euler[0] = 1.5708
            print(f"Applied: 90° rotation around X (Z → Y)")
    else:
        print(f"No rotation needed - longest edge already on Y axis")
    
    # Update transformations
    bpy.context.view_layer.update()
    
    # STEP 2: Intelligently check and orient edge to face -Z direction
    print(f"STEP 2: Ensuring longest edge faces -Z direction...")
    
    # Re-detect longest edge after rotation to get new position
    longest_after = find_longest_straight_edge(mesh_obj)
    if longest_after:
        print(f"After rotation - Edge position: X:{longest_after['x_coord']:.3f}, Y:{longest_after['y_coord']:.3f}, Z:{longest_after['z_coord']:.3f}")
        
        # Check if edge is facing the correct direction (should be at negative Z)
        if longest_after['z_coord'] > 0:
            # Edge is at positive Z (top), need to flip to negative Z (bottom)
            mesh_obj.rotation_euler[0] += 3.14159  # 180° flip around X
            print(f"Applied: 180° flip around X to move edge to -Z")
        else:
            print(f"Edge already at -Z direction - good!")
            
        # Final verification
        bpy.context.view_layer.update()
        final_longest = find_longest_straight_edge(mesh_obj)
        if final_longest:
            print(f"Final edge position: X:{final_longest['x_coord']:.3f}, Y:{final_longest['y_coord']:.3f}, Z:{final_longest['z_coord']:.3f}")
            print(f"SUCCESS: Pocket oriented - longest edge on Y axis at -Z direction")
    else:
        print(f"WARNING: Could not verify edge orientation after rotation!")

def orient_hood_properly(mesh_obj, is_first=True):
    """Orient hood pieces - intelligent logic for any SVG hood orientation
    Goal: From ANY starting orientation:
    - Run horizontal on Y axis
    - Run vertical on Z axis  
    - Longest straight edge runs vertical on Z axis
    - Side by side mirrored positioning
    """
    
    longest = find_longest_straight_edge(mesh_obj)
    if not longest:
        print(f"Hood: ERROR - No longest edge found!")
        return
    
    print(f"Hood {'1' if is_first else '2'}: Found longest edge on {longest['axis']} axis, length: {longest['length']:.3f}")
    print(f"Hood: Goal - run horizontal on Y, vertical on Z, longest edge on Z axis")
    
    # STEP 1: Intelligently rotate longest edge to Z axis (vertical)
    print(f"STEP 1: Rotating longest edge from {longest['axis']} to Z axis...")
    
    if longest['axis'] != 'Z':
        if longest['axis'] == 'X':
            # X needs to become Z: rotate 90° around Y
            mesh_obj.rotation_euler[1] = 1.5708
            print(f"Applied: 90° rotation around Y (X → Z)")
        elif longest['axis'] == 'Y':
            # Y needs to become Z: rotate 90° around X
            mesh_obj.rotation_euler[0] = 1.5708
            print(f"Applied: 90° rotation around X (Y → Z)")
    else:
        print(f"No rotation needed - longest edge already on Z axis")
        
    # Update and check orientation
    bpy.context.view_layer.update()
    
    # STEP 2: Ensure hood also runs horizontally along Y axis (like sleeves do)
    print(f"STEP 2: Ensuring hood runs horizontally along Y axis...")
    
    # Check current dimensions after rotation
    verts = [v.co for v in mesh_obj.data.vertices]
    x_span = max(v.x for v in verts) - min(v.x for v in verts)
    y_span = max(v.y for v in verts) - min(v.y for v in verts)
    z_span = max(v.z for v in verts) - min(v.z for v in verts)
    
    print(f"Current spans - X: {x_span:.3f}, Y: {y_span:.3f}, Z: {z_span:.3f}")
    
    # If hood is flat (like sleeves were), rotate to extend along Y
    if y_span < 0.01:  # Hood is flat in Y direction
        print(f"Hood is flat in Y direction - rotating to extend along Y")
        mesh_obj.rotation_euler[2] += 1.5708  # 90° around Z to extend along Y
        print(f"Applied: 90° rotation around Z to extend along Y axis")
        bpy.context.view_layer.update()
    
    # STEP 3: Mirror second hood piece
    if not is_first:
        # Mirror the second hood by rotating 180° around Z axis
        mesh_obj.rotation_euler[2] += 3.14159
        print(f"Applied: 180° rotation around Z for mirrored hood piece")
    
    # Update transformations
    bpy.context.view_layer.update()
    
    print(f"SUCCESS: Hood {'1' if is_first else '2'} oriented - runs horizontal on Y, vertical on Z, longest edge on Z")


def create_proper_stitches_between_edges(edge1_points, edge2_points, stitch_count=4):
    """Create proper stitches between two seam edges using correct algorithm
    
    Algorithm for 2-point edges:
    1. Each edge has exactly 2 points (start and end)
    2. Find the shortest edge between the two
    3. Place evenly spaced points on both edges (same count)
    4. Connect corresponding points with hard connections
    
    Args:
        edge1_points: List of exactly 2 points [start, end] for first edge
        edge2_points: List of exactly 2 points [start, end] for second edge
        stitch_count: Number of stitches to create
        
    Returns:
        List of created stitch line objects
    """
    
    if len(edge1_points) != 2 or len(edge2_points) != 2:
        print(f"ERROR: Expected exactly 2 points per edge, got {len(edge1_points)} and {len(edge2_points)}")
        return []
    
    # STEP 1: Calculate edge lengths to find shortest
    edge1_length = (edge1_points[1] - edge1_points[0]).length
    edge2_length = (edge2_points[1] - edge2_points[0]).length
    
    print(f"Edge 1 length: {edge1_length:.3f}, Edge 2 length: {edge2_length:.3f}")
    
    # Determine which is shortest
    if edge1_length <= edge2_length:
        shortest_edge_points = edge1_points
        longest_edge_points = edge2_points
        shortest_length = edge1_length
        print("Edge 1 is shortest, Edge 2 is longest")
    else:
        shortest_edge_points = edge2_points
        longest_edge_points = edge1_points
        shortest_length = edge2_length
        print("Edge 2 is shortest, Edge 1 is longest")
    
    # STEP 2: Create evenly spaced points on both edges
    print(f"Creating {stitch_count} evenly spaced stitches")
    
    shortest_stitch_points = []
    longest_stitch_points = []
    
    for i in range(stitch_count):
        # Calculate position along edge (0.0 to 1.0)
        if stitch_count == 1:
            t = 0.5  # Middle
        else:
            t = i / (stitch_count - 1)  # 0.0 to 1.0
        
        # Interpolate points along both edges
        shortest_point = shortest_edge_points[0].lerp(shortest_edge_points[1], t)
        longest_point = longest_edge_points[0].lerp(longest_edge_points[1], t)
        
        shortest_stitch_points.append(shortest_point)
        longest_stitch_points.append(longest_point)
    
    print(f"Created {len(shortest_stitch_points)} points on shortest edge")
    print(f"Created {len(longest_stitch_points)} points on longest edge")
    
    # STEP 3: Create hard connections between corresponding points
    stitch_objects = []
    
    for i in range(stitch_count):
        p1 = shortest_stitch_points[i]
        p2 = longest_stitch_points[i]
        
        # Create line mesh connecting the two corresponding points
        verts = [(p1.x, p1.y, p1.z), (p2.x, p2.y, p2.z)]
        edges = [(0, 1)]
        
        mesh = bpy.data.meshes.new(f"stitch_line_{i}")
        mesh.from_pydata(verts, edges, [])
        mesh.update()
        
        obj = bpy.data.objects.new(f"stitch_line_{i}", mesh)
        bpy.context.collection.objects.link(obj)
        
        # Make stitches visible with bright green material
        mat = bpy.data.materials.new(name=f"Stitch_Material_{i}")
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.0, 1.0, 0.0, 1.0)  # Bright green
        mat.node_tree.nodes["Principled BSDF"].inputs[18].default_value = 2.0  # Strong emission
        obj.data.materials.append(mat)
        
        stitch_objects.append(obj)
        
        print(f"Stitch {i+1}: ({p1.x:.3f}, {p1.y:.3f}, {p1.z:.3f}) -> ({p2.x:.3f}, {p2.y:.3f}, {p2.z:.3f})")
    
    print(f"Created {len(stitch_objects)} hard stitch connections")
    return stitch_objects


def create_stitches_between_edges(edge1_points, edge2_points, stitch_spacing=0.05):
    """Legacy function - use create_proper_stitches_between_edges instead"""
    return create_proper_stitches_between_edges(edge1_points, edge2_points)


def get_evenly_spaced_points_on_edge(edge_points, count):
    """Get evenly spaced points along an edge defined by a series of points
    
    Args:
        edge_points: List of 3D points defining the edge
        count: Number of evenly spaced points to generate
        
    Returns:
        List of evenly spaced 3D points along the edge
    """
    
    if count <= 0:
        return []
    
    if count == 1:
        # Return midpoint of edge
        total_length = sum((edge_points[i+1] - edge_points[i]).length for i in range(len(edge_points)-1))
        return [get_point_at_distance_along_edge(edge_points, total_length / 2)]
    
    # Calculate total edge length
    total_length = sum((edge_points[i+1] - edge_points[i]).length for i in range(len(edge_points)-1))
    
    # Generate evenly spaced distances
    spacing = total_length / (count - 1)
    
    spaced_points = []
    for i in range(count):
        distance = i * spacing
        point = get_point_at_distance_along_edge(edge_points, distance)
        spaced_points.append(point)
    
    return spaced_points


def get_point_at_distance_along_edge(edge_points, target_distance):
    """Get a point at a specific distance along an edge
    
    Args:
        edge_points: List of 3D points defining the edge
        target_distance: Distance along edge to find point
        
    Returns:
        3D point at the specified distance along the edge
    """
    
    if target_distance <= 0:
        return edge_points[0]
    
    current_distance = 0
    
    for i in range(len(edge_points) - 1):
        p1 = edge_points[i]
        p2 = edge_points[i + 1]
        segment_length = (p2 - p1).length
        
        if current_distance + segment_length >= target_distance:
            # Point is in this segment
            remaining_distance = target_distance - current_distance
            t = remaining_distance / segment_length if segment_length > 0 else 0
            return p1.lerp(p2, t)
        
        current_distance += segment_length
    
    # If we get here, return the last point
    return edge_points[-1]


def get_longest_edge_endpoints(mesh_obj):
    """Extract ONLY the start and end points of the longest straight edge
    
    Args:
        mesh_obj: Blender mesh object
        
    Returns:
        List of exactly 2 points: [start_point, end_point] in world coordinates
    """
    
    longest_edge_info = find_longest_straight_edge(mesh_obj)
    if not longest_edge_info:
        print(f"ERROR: No longest edge found for {mesh_obj.name}")
        return []
    
    print(f"Found longest edge on {longest_edge_info['axis']} axis, length: {longest_edge_info['length']:.3f}")
    
    # Get all vertices in world coordinates
    world_verts = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
    
    # Transform edge center from local to world coordinates
    local_edge_center = mathutils.Vector((longest_edge_info['x_coord'], longest_edge_info['y_coord'], longest_edge_info['z_coord']))
    world_edge_center = mesh_obj.matrix_world @ local_edge_center
    edge_axis = longest_edge_info['axis']
    edge_length = longest_edge_info['length']
    
    print(f"World edge center: ({world_edge_center.x:.3f}, {world_edge_center.y:.3f}, {world_edge_center.z:.3f})")
    
    # Calculate the two endpoints of the longest edge
    half_length = edge_length / 2
    
    if edge_axis == 'X':
        # Edge runs along X axis
        start_point = mathutils.Vector((world_edge_center.x - half_length, world_edge_center.y, world_edge_center.z))
        end_point = mathutils.Vector((world_edge_center.x + half_length, world_edge_center.y, world_edge_center.z))
    elif edge_axis == 'Y':
        # Edge runs along Y axis
        start_point = mathutils.Vector((world_edge_center.x, world_edge_center.y - half_length, world_edge_center.z))
        end_point = mathutils.Vector((world_edge_center.x, world_edge_center.y + half_length, world_edge_center.z))
    elif edge_axis == 'Z':
        # Edge runs along Z axis
        start_point = mathutils.Vector((world_edge_center.x, world_edge_center.y, world_edge_center.z - half_length))
        end_point = mathutils.Vector((world_edge_center.x, world_edge_center.y, world_edge_center.z + half_length))
    else:
        print(f"ERROR: Unknown edge axis {edge_axis}")
        return []
    
    edge_points = [start_point, end_point]
    
    print(f"Edge endpoints: Start=({start_point.x:.3f}, {start_point.y:.3f}, {start_point.z:.3f}), End=({end_point.x:.3f}, {end_point.y:.3f}, {end_point.z:.3f})")
    print(f"Extracted exactly 2 endpoint coordinates for longest edge")
    
    return edge_points


def add_sleeve_cuff_stitching(sleeve_meshes, cuff_meshes):
    """Add stitching between sleeves and their corresponding cuffs
    
    Args:
        sleeve_meshes: List of (mesh_obj, part_name, index) tuples for sleeves
        cuff_meshes: List of (mesh_obj, part_name, index) tuples for cuffs
        
    Returns:
        List of created stitch objects
    """
    
    print("=== ADDING SLEEVE TO CUFF STITCHING ===")
    all_stitches = []
    
    # Match sleeves with their corresponding cuffs
    for i, (sleeve_mesh, sleeve_name, sleeve_idx) in enumerate(sleeve_meshes):
        if i < len(cuff_meshes):
            cuff_mesh, cuff_name, cuff_idx = cuff_meshes[i]
            
            print(f"\nProcessing {sleeve_name} with {cuff_name}...")
            
            # Get longest edge endpoints (exactly 2 points each)
            sleeve_edge_points = get_longest_edge_endpoints(sleeve_mesh)
            cuff_edge_points = get_longest_edge_endpoints(cuff_mesh)
            
            if sleeve_edge_points and cuff_edge_points:
                print(f"Sleeve edge: {len(sleeve_edge_points)} points")
                print(f"Cuff edge: {len(cuff_edge_points)} points")
                
                # Create stitches using proper algorithm
                stitches = create_proper_stitches_between_edges(sleeve_edge_points, cuff_edge_points)
                all_stitches.extend(stitches)
                
                print(f"Added {len(stitches)} stitches between {sleeve_name} and {cuff_name}")
            else:
                print(f"ERROR: Could not extract edge points for {sleeve_name} or {cuff_name}")
    
    print(f"\nTotal sleeve-cuff stitches created: {len(all_stitches)}")
    return all_stitches


def position_panels_intelligently(panel_meshes):
    """Position front and back panels with proper orientation"""
    
    front_panels = []
    back_panels = []
    
    for mesh_obj, part_name, index in panel_meshes:
        if part_name == "front_panel":
            front_panels.append((mesh_obj, index))
        elif part_name == "back_panel":
            back_panels.append((mesh_obj, index))
    
    for i, (mesh_obj, index) in enumerate(front_panels):
        orient_panel_properly(mesh_obj, "front")
        mesh_obj.location.x = 0.5
        mesh_obj.location.y = 0  
        mesh_obj.location.z = i * 0.5
        
    for i, (mesh_obj, index) in enumerate(back_panels):
        orient_panel_properly(mesh_obj, "back")
        mesh_obj.location.x = -0.5
        mesh_obj.location.y = 0
        mesh_obj.location.z = i * 0.5
        
    

def position_pockets_on_front_panel(pocket_meshes, panel_meshes):
    
    front_panel_mesh = None
    for mesh_obj, part_name, index in panel_meshes:
        if part_name == "front_panel":
            front_panel_mesh = mesh_obj
            break
    
    if not front_panel_mesh:
        return
    
    for i, (mesh_obj, part_name, index) in enumerate(pocket_meshes):
        orient_pocket_properly(mesh_obj)
        mesh_obj.location.x = front_panel_mesh.location.x + 0.1
        mesh_obj.location.y = front_panel_mesh.location.y - 0.01
        
        pocket_verts = mesh_obj.data.vertices
        panel_verts = front_panel_mesh.data.vertices
        
        if pocket_verts and panel_verts:
            pocket_min_z = min(v.co.z for v in pocket_verts)
            panel_min_z = min(v.co.z for v in panel_verts)
            
            gap_above_panel_bottom = 0.2
            pocket_z_layer = 0.01 + (i * 0.01)
            
            panel_bottom_world_z = front_panel_mesh.location.z + panel_min_z
            pocket_bottom_world_z = panel_bottom_world_z + gap_above_panel_bottom
            pocket_center_z = pocket_bottom_world_z - pocket_min_z + pocket_z_layer
            
            mesh_obj.location.z = pocket_center_z
          
        else:
            mesh_obj.location.z = front_panel_mesh.location.z + 0.5
        
    

def position_sleeves(sleeve_meshes):
    """Find longest straight edge and orient it along Z axis (vertical)"""
    
    print(f"DEBUG: Processing {len(sleeve_meshes)} sleeves")
    
    for i, (mesh_obj, part_name, index) in enumerate(sleeve_meshes):
        print(f"DEBUG: Processing sleeve {i+1}: {mesh_obj.name}")
        
        # Position sleeves at different Y coordinates
        mesh_obj.location.x = 1.0
        mesh_obj.location.y = 3.0 if i == 0 else -3.0  # Right (+Y) and Left (-Y)
        mesh_obj.location.z = 2.0
        
        print(f"DEBUG: Positioned sleeve at ({mesh_obj.location.x}, {mesh_obj.location.y}, {mesh_obj.location.z})")
        
        # Check if mesh has data
        if not mesh_obj.data or not mesh_obj.data.vertices:
            print(f"DEBUG: ERROR - Sleeve {i+1} has no mesh data!")
            continue
            
        print(f"DEBUG: Sleeve {i+1} has {len(mesh_obj.data.vertices)} vertices")
        
        # Find the longest straight edge
        longest_edge = find_longest_straight_edge(mesh_obj)
        print(f"DEBUG: find_longest_straight_edge returned: {longest_edge}")
        
        if longest_edge:
            print(f"Sleeve {i+1}: Longest edge on {longest_edge['axis']} axis, length: {longest_edge['length']:.3f}")
            
            # Get the edge center and direction
            edge_center = mathutils.Vector((longest_edge['x_coord'], longest_edge['y_coord'], longest_edge['z_coord']))
            
            # Create extension line from the edge outward
            extension_length = 0.5
            
            # Determine extension direction based on edge position relative to sleeve center
            verts = mesh_obj.data.vertices
            sleeve_center_x = sum(v.co.x for v in verts) / len(verts)
            sleeve_center_y = sum(v.co.y for v in verts) / len(verts)
            sleeve_center_z = sum(v.co.z for v in verts) / len(verts)
            sleeve_center = mathutils.Vector((sleeve_center_x, sleeve_center_y, sleeve_center_z))
            
            # Direction from sleeve center to edge center
            to_edge = edge_center - sleeve_center
            to_edge.normalize()
            
            # Extension point outward from the edge
            extension_end = edge_center + (to_edge * extension_length)
            
            # Transform both points to world coordinates
            world_edge_center = mesh_obj.matrix_world @ edge_center
            world_extension_end = mesh_obj.matrix_world @ extension_end
            
            # Create a simple line mesh
            line_verts = [world_edge_center, world_extension_end]
            line_edges = [(0, 1)]
            
            line_mesh = bpy.data.meshes.new(name=f"EDGE_EXTENSION_{mesh_obj.name}")
            line_mesh.from_pydata(line_verts, line_edges, [])
            line_mesh.update()
            
            line_obj = bpy.data.objects.new(name=f"EDGE_EXTENSION_{mesh_obj.name}", object_data=line_mesh)
            bpy.context.collection.objects.link(line_obj)
            
            # Make the line bright red and thick
            mat = bpy.data.materials.new(name=f"Extension_Material_{mesh_obj.name}")
            mat.use_nodes = True
            mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)  # Bright red
            mat.node_tree.nodes["Principled BSDF"].inputs[18].default_value = 2.0  # Make it emit light
            line_obj.data.materials.append(mat)
            
            print(f"Created red extension line from edge center outward")
            
            # GOAL: Make sleeve run along global Y axis, with longest edge at the outer edge
            # Don't flatten the sleeve - just orient it properly in 3D space
            
            print(f"Current longest edge on {longest_edge['axis']} axis")
            
            # Get current sleeve bounds in all dimensions
            verts = mesh_obj.data.vertices
            min_x = min(v.co.x for v in verts)
            max_x = max(v.co.x for v in verts)
            min_y = min(v.co.y for v in verts)
            max_y = max(v.co.y for v in verts)
            min_z = min(v.co.z for v in verts)
            max_z = max(v.co.z for v in verts)
            
            print(f"Sleeve bounds - X: {min_x:.3f} to {max_x:.3f}, Y: {min_y:.3f} to {max_y:.3f}, Z: {min_z:.3f} to {max_z:.3f}")
            
            # Calculate which dimension the sleeve currently spans the most
            x_span = max_x - min_x
            y_span = max_y - min_y  
            z_span = max_z - min_z
            
            print(f"Sleeve spans - X: {x_span:.3f}, Y: {y_span:.3f}, Z: {z_span:.3f}")
            
            # The sleeve is flat (Y=0.000) because it was created in XZ plane
            # We need to rotate it properly to make it 3D visible
            print(f"PROBLEM: Sleeve is flat! Y span = {y_span}")
            
            # Since sleeve is flat in XZ plane and we want it to run along Y:
            # Rotate 90° around Z axis so X becomes Y (sleeve extends along Y)
            mesh_obj.rotation_euler[2] = 1.5708  # 90° around Z: X becomes Y
            print("Rotated flat sleeve 90° around Z so it extends along Y axis")
            
            # FORCE UPDATE the mesh transformations
            bpy.context.view_layer.update()
            
            # Check what happened after rotation using WORLD COORDINATES
            world_verts = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
            min_x_world = min(v.x for v in world_verts)
            max_x_world = max(v.x for v in world_verts) 
            min_y_world = min(v.y for v in world_verts)
            max_y_world = max(v.y for v in world_verts)
            min_z_world = min(v.z for v in world_verts)
            max_z_world = max(v.z for v in world_verts)
            
            print(f"POST-ROTATION WORLD bounds - X: {min_x_world:.3f} to {max_x_world:.3f}, Y: {min_y_world:.3f} to {max_y_world:.3f}, Z: {min_z_world:.3f} to {max_z_world:.3f}")
            
            # Now orient each sleeve differently based on its position
            if i == 0:
                # RIGHT sleeve (at +Y=3.0): longest edge should face towards +Y (outward right)
                print("Processing RIGHT sleeve - orienting longest edge towards +Y")
                
                # Re-find the longest edge after rotation
                longest_edge_after = find_longest_straight_edge(mesh_obj)
                
                if longest_edge_after:
                    # Transform the edge coordinates to world space
                    edge_local = mathutils.Vector((longest_edge_after['x_coord'], longest_edge_after['y_coord'], longest_edge_after['z_coord']))
                    edge_world = mesh_obj.matrix_world @ edge_local
                    
                    # Use world coordinates for comparison
                    edge_y_world = edge_world.y
                    
                    print(f"After rotation - edge at WORLD Y: {edge_y_world:.3f}, sleeve WORLD Y range: {min_y_world:.3f} to {max_y_world:.3f}")
                    
                    # For right sleeve, we want edge on the +Y side (more positive) relative to sleeve center
                    sleeve_center_y = (min_y_world + max_y_world) / 2
                    if edge_y_world < sleeve_center_y:
                        # Edge is on -Y side, flip 180° to move to +Y side
                        mesh_obj.rotation_euler[2] += 3.14159
                        print("Flipped RIGHT sleeve to put longest edge on +Y side")
                    else:
                        print("RIGHT sleeve longest edge already on +Y side")
                        
            else:
                # LEFT sleeve (at -Y=-3.0): longest edge should face towards -Y (outward left)
                print("Processing LEFT sleeve - orienting longest edge towards -Y")
                
                # Get world coordinates for left sleeve
                world_verts_left = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
                min_y_world_left = min(v.y for v in world_verts_left)
                max_y_world_left = max(v.y for v in world_verts_left)
                
                longest_edge_after = find_longest_straight_edge(mesh_obj)
                
                if longest_edge_after:
                    # Transform the edge coordinates to world space
                    edge_local = mathutils.Vector((longest_edge_after['x_coord'], longest_edge_after['y_coord'], longest_edge_after['z_coord']))
                    edge_world = mesh_obj.matrix_world @ edge_local
                    edge_y_world = edge_world.y
                    
                    print(f"After rotation - edge at WORLD Y: {edge_y_world:.3f}, sleeve WORLD Y range: {min_y_world_left:.3f} to {max_y_world_left:.3f}")
                    
                    # For left sleeve, we want edge on the -Y side (more negative) relative to sleeve center
                    sleeve_center_y = (min_y_world_left + max_y_world_left) / 2
                    if edge_y_world > sleeve_center_y:
                        # Edge is on +Y side, flip 180° to move to -Y side
                        mesh_obj.rotation_euler[2] += 3.14159
                        print("Flipped LEFT sleeve to put longest edge on -Y side")
                    else:
                        print("LEFT sleeve longest edge already on -Y side")
                    
        else:
            print(f"Sleeve {i+1}: No straight edges found")
        
        

        
    

def position_cuffs_under_sleeves(cuff_meshes, sleeve_meshes):
    """Position cuffs so their LONGEST STRAIGHT EDGE aligns with sleeve's SHORTEST edge"""
    
    print(f"\n=== CUFF POSITIONING DEBUG ===")
    print(f"Processing {len(cuff_meshes)} sleeve cuffs")
    
    for i, (cuff_mesh, cuff_part_name, cuff_index) in enumerate(cuff_meshes):
        print(f"\n--- CUFF {i+1}: {cuff_mesh.name} ---")
        
        # Get corresponding sleeve
        if i < len(sleeve_meshes):
            sleeve_mesh, sleeve_part_name, sleeve_index = sleeve_meshes[i]
        else:
            print("ERROR: No corresponding sleeve found!")
            continue
        
        # Find sleeve's longest straight edge
        sleeve_longest = find_longest_straight_edge(sleeve_mesh)
        if not sleeve_longest:
            print("ERROR: No longest edge found in sleeve!")
            continue
            
        print(f"SLEEVE longest edge: {sleeve_longest['axis']} axis, length: {sleeve_longest['length']:.3f}")
        
        # Find cuff's longest straight edge  
        cuff_longest = find_longest_straight_edge(cuff_mesh)
        if not cuff_longest:
            print("ERROR: No longest edge found in cuff!")
            continue
            
        print(f"CUFF longest edge: {cuff_longest['axis']} axis, length: {cuff_longest['length']:.3f}")
        
        # STEP 1: Intelligently rotate cuff so its longest edge aligns with sleeve's longest edge on Z axis
        print(f"\nSTEP 1: Intelligently rotating cuff longest edge to align with sleeve longest edge on Z axis...")
        
        print(f"Cuff longest edge currently on: {cuff_longest['axis']} axis")
        print(f"Sleeve longest edge currently on: {sleeve_longest['axis']} axis") 
        print(f"Target: Both longest edges should align on Z axis")
        
        # Find cuff's shortest edge to determine depth orientation
        cuff_shortest = find_shortest_straight_edge(cuff_mesh)
        if not cuff_shortest:
            print("ERROR: No shortest edge found in cuff!")
            continue
            
        print(f"Cuff shortest edge: {cuff_shortest['axis']} axis, length: {cuff_shortest['length']:.3f}")
        
        # Intelligent rotation: longest edge depth in Z, shortest edge depth in Y
        print(f"Target: longest edge depth in Z, shortest edge depth in Y")
        
        # Step 1: Rotate longest edge to Z axis
        if cuff_longest['axis'] != 'Z':
            if cuff_longest['axis'] == 'X':
                cuff_mesh.rotation_euler[1] = 1.5708  # X → Z
                print("Applied: 90° rotation around Y (longest X → Z)")
            elif cuff_longest['axis'] == 'Y':
                cuff_mesh.rotation_euler[0] = 1.5708  # Y → Z
                print("Applied: 90° rotation around X (longest Y → Z)")
        else:
            print("Longest edge already on Z axis")
            
        # Update and re-detect shortest edge after rotation
        bpy.context.view_layer.update()
        cuff_shortest_after = find_shortest_straight_edge(cuff_mesh)
        
        # Step 2: Rotate shortest edge to Y axis
        if cuff_shortest_after and cuff_shortest_after['axis'] != 'Y':
            if cuff_shortest_after['axis'] == 'X':
                cuff_mesh.rotation_euler[2] += 1.5708  # X → Y
                print("Applied additional: 90° rotation around Z (shortest X → Y)")
            elif cuff_shortest_after['axis'] == 'Z':
                cuff_mesh.rotation_euler[0] += 1.5708  # Z → Y  
                print("Applied additional: 90° rotation around X (shortest Z → Y)")
        else:
            print("Shortest edge already on Y axis")
            
        bpy.context.view_layer.update()
        
        # STEP 2: Position cuff so its Z middle aligns with sleeve's Z middle
        print(f"\nSTEP 2: Aligning cuff Z middle with sleeve Z middle...")
        
        # Get sleeve Z bounds
        sleeve_world_verts = [sleeve_mesh.matrix_world @ v.co for v in sleeve_mesh.data.vertices]
        sleeve_min_z = min(v.z for v in sleeve_world_verts)
        sleeve_max_z = max(v.z for v in sleeve_world_verts)
        sleeve_center_z = (sleeve_min_z + sleeve_max_z) / 2
        
        # Position cuff initially at sleeve location
        cuff_mesh.location.x = sleeve_mesh.location.x
        cuff_mesh.location.y = sleeve_mesh.location.y  
        cuff_mesh.location.z = sleeve_center_z  # Set to sleeve's Z middle
        
        bpy.context.view_layer.update()
        
        # Verify cuff Z middle aligns with sleeve Z middle
        cuff_world_verts = [cuff_mesh.matrix_world @ v.co for v in cuff_mesh.data.vertices]
        cuff_min_z = min(v.z for v in cuff_world_verts)
        cuff_max_z = max(v.z for v in cuff_world_verts)
        cuff_center_z = (cuff_min_z + cuff_max_z) / 2
        
        print(f"Sleeve Z center: {sleeve_center_z:.3f}")
        print(f"Cuff Z center: {cuff_center_z:.3f}")
        print(f"Z alignment offset: {abs(cuff_center_z - sleeve_center_z):.3f}")
        
        # STEP 3: Position cuff in Y axis so sleeve end aligns with cuff start with small gap
        print(f"\nSTEP 3: Positioning cuff in Y axis with small gap from sleeve end...")
        
        # Get sleeve Y bounds
        sleeve_min_y = min(v.y for v in sleeve_world_verts)
        sleeve_max_y = max(v.y for v in sleeve_world_verts)
        
        # Get current cuff Y bounds
        cuff_min_y = min(v.y for v in cuff_world_verts)
        cuff_max_y = max(v.y for v in cuff_world_verts)
        cuff_center_y = (cuff_min_y + cuff_max_y) / 2
        cuff_y_span = cuff_max_y - cuff_min_y
        
        gap = 0.05  # Small gap
        
        if i == 0:  # Right sleeve (+Y side)
            # Sleeve end (most +Y) aligns with cuff start (least +Y) with gap
            target_y = sleeve_max_y + gap + cuff_y_span/2
            cuff_mesh.location.y = target_y
            print(f"RIGHT: Sleeve end Y={sleeve_max_y:.3f} + gap={gap} + cuff start")
        else:  # Left sleeve (-Y side)
            # Sleeve end (most -Y) aligns with cuff start (most -Y) with gap
            target_y = sleeve_min_y - gap - cuff_y_span/2
            cuff_mesh.location.y = target_y
            print(f"LEFT: Sleeve end Y={sleeve_min_y:.3f} - gap={gap} - cuff start")
            
        bpy.context.view_layer.update()
        
        # Verify final positioning
        final_cuff_verts = [cuff_mesh.matrix_world @ v.co for v in cuff_mesh.data.vertices]
        final_cuff_min_y = min(v.y for v in final_cuff_verts)
        final_cuff_max_y = max(v.y for v in final_cuff_verts)
        
        print(f"Final positioning:")
        print(f"  Sleeve Y: {sleeve_min_y:.3f} to {sleeve_max_y:.3f}")
        print(f"  Cuff Y: {final_cuff_min_y:.3f} to {final_cuff_max_y:.3f}")
        
        if i == 0:
            actual_gap = final_cuff_min_y - sleeve_max_y
            print(f"  RIGHT gap: {actual_gap:.3f}")
        else:
            actual_gap = sleeve_min_y - final_cuff_max_y
            print(f"  LEFT gap: {actual_gap:.3f}")
            
        # STEP 4: Position cuff so all vertices share same X value (depth in Y, not X)
        print(f"\nSTEP 4: Flattening cuff to have depth in Y direction, not X...")
        
        # Get current cuff X bounds
        final_cuff_x_min = min(v.x for v in final_cuff_verts)
        final_cuff_x_max = max(v.x for v in final_cuff_verts)
        cuff_x_span = final_cuff_x_max - final_cuff_x_min
        
        print(f"Current cuff X span: {cuff_x_span:.3f} (from {final_cuff_x_min:.3f} to {final_cuff_x_max:.3f})")
        
        # Set cuff to same X position as sleeve center
        sleeve_x_center = sleeve_mesh.location.x
        cuff_mesh.location.x = sleeve_x_center
        
        print(f"Set cuff X to sleeve X center: {sleeve_x_center:.3f}")
        
        bpy.context.view_layer.update()
        
        # Verify final X positioning
        verify_cuff_verts = [cuff_mesh.matrix_world @ v.co for v in cuff_mesh.data.vertices]
        verify_x_min = min(v.x for v in verify_cuff_verts)
        verify_x_max = max(v.x for v in verify_cuff_verts)
        verify_x_span = verify_x_max - verify_x_min
        
        print(f"Final cuff X span: {verify_x_span:.3f} (from {verify_x_min:.3f} to {verify_x_max:.3f})")
        print(f"SUCCESS: Cuff depth now in Y direction, minimal X span!")
            
    

def position_waistband_under_front_panel(waistband_meshes, panel_meshes):
    
    front_panel_mesh = None
    for mesh_obj, part_name, index in panel_meshes:
        if part_name == "front_panel":
            front_panel_mesh = mesh_obj
            break
    
    if not front_panel_mesh:
        return
    
    for i, (waistband_mesh, waistband_part_name, waistband_index) in enumerate(waistband_meshes):
        orient_waistband_properly(waistband_mesh)
        waistband_mesh.location.x = front_panel_mesh.location.x
        waistband_mesh.location.y = front_panel_mesh.location.y
        
        front_panel_verts = front_panel_mesh.data.vertices
        waistband_verts = waistband_mesh.data.vertices
        
        if front_panel_verts and waistband_verts:
            front_panel_min_z = min(v.co.z for v in front_panel_verts)
            front_panel_bottom_world_z = front_panel_mesh.location.z + front_panel_min_z
            
            waistband_max_z = max(v.co.z for v in waistband_verts)
            
            gap_between_panel_and_waistband = 0.05
            waistband_top_world_z = front_panel_bottom_world_z - gap_between_panel_and_waistband
            waistband_center_z = waistband_top_world_z - waistband_max_z
            
            waistband_mesh.location.z = waistband_center_z
            
        else:
            waistband_mesh.location.z = front_panel_mesh.location.z - 1.0
        
    

def position_hoods_side_by_side(first_hood, second_hood):
    """Step 1: In XZ plane - same Z, align in X so longest edges touch side by side"""
    
    # Find longest straight edge of first hood
    longest_first = find_longest_straight_edge(first_hood)
    if not longest_first:
        return
    
    
    # Position first hood at origin
    first_hood.location.x = 0
    first_hood.location.y = 0
    first_hood.location.z = 0
    
    # Position second hood with SAME Z, adjacent in X so longest edges touch
    first_verts = first_hood.data.vertices
    second_verts = second_hood.data.vertices
    
    # Get bounds
    first_min_x = min(v.co.x for v in first_verts)
    first_max_x = max(v.co.x for v in first_verts)
    second_min_x = min(v.co.x for v in second_verts)
    second_max_x = max(v.co.x for v in second_verts)
    
    # Same Z coordinate
    second_hood.location.z = 0
    second_hood.location.y = 0
    
    # Position in X so edges are adjacent
    gap = 0.02
    second_hood.location.x = first_max_x + gap - second_min_x
    

def align_hoods_after_rotation(first_hood, second_hood):
    """Step 3: After rotation, same X and Z, align in Y so longest edges touch"""
    
    # Update transformations
    bpy.context.view_layer.update()
    
    # Get world coordinates after rotation
    first_verts = [first_hood.matrix_world @ v.co for v in first_hood.data.vertices]
    second_verts = [second_hood.matrix_world @ v.co for v in second_hood.data.vertices]
    
    # Get bounds
    first_min_y = min(v.y for v in first_verts)
    first_max_y = max(v.y for v in first_verts)
    second_min_y = min(v.y for v in second_verts)
    second_max_y = max(v.y for v in second_verts)
    
    # Position first hood at origin for Y
    first_hood.location.y = 0
    
    # Make second hood have same X and Z as first
    second_hood.location.x = first_hood.location.x
    second_hood.location.z = first_hood.location.z
    
    # Position second hood in Y so longest edges are adjacent
    bpy.context.view_layer.update()
    first_verts_updated = [first_hood.matrix_world @ v.co for v in first_hood.data.vertices]
    first_max_y_updated = max(v.y for v in first_verts_updated)
    
    gap = 0.02
    second_hood.location.y = first_max_y_updated + gap - second_min_y
    

def position_hoods_above_back_panel(first_hood, second_hood, panel_meshes):
    """Step 4: Move both hoods so their bottom edge is above back panel's top edge"""
    
    # Find back panel
    back_panel_mesh = None
    for mesh_obj, part_name, index in panel_meshes:
        if part_name == "back_panel":
            back_panel_mesh = mesh_obj
            break
    
    if not back_panel_mesh:
        print("No back panel found for hood positioning")
        return
    
    # Get back panel's top edge (max Z)
    bpy.context.view_layer.update()
    back_panel_verts = [back_panel_mesh.matrix_world @ v.co for v in back_panel_mesh.data.vertices]
    back_panel_max_z = max(v.z for v in back_panel_verts)
    
    # Get both hoods' bottom edges (min Z)
    first_hood_verts = [first_hood.matrix_world @ v.co for v in first_hood.data.vertices]
    second_hood_verts = [second_hood.matrix_world @ v.co for v in second_hood.data.vertices]
    
    first_hood_min_z = min(v.z for v in first_hood_verts)
    second_hood_min_z = min(v.z for v in second_hood_verts)
    
    # Calculate how much to move up
    gap = 0.02
    target_z = back_panel_max_z + gap
    
    # Move both hoods up by the same amount so their bottoms are above back panel
    first_hood_z_offset = target_z - first_hood_min_z
    second_hood_z_offset = target_z - second_hood_min_z
    
    first_hood.location.z += first_hood_z_offset
    second_hood.location.z += second_hood_z_offset
    
    # Also align both hoods to have the same X coordinate as back panel
    first_hood.location.x = back_panel_mesh.location.x
    second_hood.location.x = back_panel_mesh.location.x
    
    # Center the hoods so their touching point aligns with back panel's Y center
    # Get back panel's Y center
    back_panel_min_y = min(v.y for v in back_panel_verts)
    back_panel_max_y = max(v.y for v in back_panel_verts)
    back_panel_center_y = back_panel_mesh.location.y + (back_panel_min_y + back_panel_max_y) / 2
    
    # Find where the hoods currently touch (the seam between them)
    bpy.context.view_layer.update()
    first_hood_verts_final = [first_hood.matrix_world @ v.co for v in first_hood.data.vertices]
    second_hood_verts_final = [second_hood.matrix_world @ v.co for v in second_hood.data.vertices]
    
    first_hood_max_y = max(v.y for v in first_hood_verts_final)
    second_hood_min_y = min(v.y for v in second_hood_verts_final)
    current_seam_y = (first_hood_max_y + second_hood_min_y) / 2
    
    # Calculate offset to center the seam with back panel center
    y_offset = back_panel_center_y - current_seam_y
    
    # Apply offset to both hoods
    first_hood.location.y += y_offset
    second_hood.location.y += y_offset
    

def position_hood_pieces_together(hood_meshes, panel_meshes=None):
    
    if len(hood_meshes) < 2:
        return
    
    first_hood = hood_meshes[0][0]
    second_hood = hood_meshes[1][0]
    
    # Step 1: Position them side by side along their longest straight edge (in XZ plane)
    position_hoods_side_by_side(first_hood, second_hood)
    
    # Step 2: Rotate both so shortest edge points down (-Z) and runs along Y
    orient_hood_properly(first_hood, is_first=True)
    orient_hood_properly(second_hood, is_first=False)
    
    # Step 3: After rotation, align them so they have same X and Z, with longest edges touching in Y
    align_hoods_after_rotation(first_hood, second_hood)
    
    # Step 4: Position both hoods so their bottom edge is above back panel's top edge
    if panel_meshes:
        position_hoods_above_back_panel(first_hood, second_hood, panel_meshes)
    
    

# ========== MAIN EXECUTION (FROM SynthGenerateGarment.execute) ==========

def generate_garment(garment_type="hoodie", collection_name="FashionSynth_Hoodie"):
    """Main function to generate a garment from default IPFS patterns"""

    defaults = get_garment_defaults(garment_type)
    if not defaults:
        return
    
    created_meshes = []
    panel_meshes = []
    pocket_meshes = []
    sleeve_meshes = []
    cuff_meshes = []
    waistband_meshes = []
    hood_meshes = []
    
    for part_name, part_info in defaults.items():
        
        ipfs_hash = part_info.get("ipfs", "")
        quantity = part_info.get("quantity", 1)
        
        if not ipfs_hash:
            continue
        
        gateway_url = ipfs_to_gateway_url(ipfs_hash)
        
        coordinates = get_coordinates_from_ipfs(ipfs_hash, gateway_url)
        
        if not coordinates:
            continue
        
        
        for i in range(quantity):
            mesh_name = f"{garment_type}_{part_name}_{i+1}" if quantity > 1 else f"{garment_type}_{part_name}"
            
            mesh_obj = create_mesh_from_coordinates(
                coordinates,
                mesh_name,
                collection_name

            )
            
            if mesh_obj:
                markSeam(mesh_obj)
                created_meshes.append(mesh_obj)
                
                # Categorize mesh like plugin does
                if "front_panel" in part_name.lower() or "back_panel" in part_name.lower():
                    panel_meshes.append((mesh_obj, part_name, i))
                elif 'pocket' in part_name.lower():
                    pocket_meshes.append((mesh_obj, part_name, i))
                elif  'sleeve_cuff' in part_name.lower():
                    cuff_meshes.append((mesh_obj, part_name, i))
                elif  'sleeve' in part_name.lower() and "cuff" not in part_name.lower():
                    sleeve_meshes.append((mesh_obj, part_name, i))
                elif "waist_band" in part_name.lower():
                    waistband_meshes.append((mesh_obj, part_name, i))
                elif  'hood' in part_name.lower():
                    hood_meshes.append((mesh_obj, part_name, i))
                
            
    
    if created_meshes:
        if panel_meshes:
            position_panels_intelligently(panel_meshes)
        
        # Position pockets on front panel
        if pocket_meshes and panel_meshes:
            position_pockets_on_front_panel(pocket_meshes, panel_meshes)
        
        if sleeve_meshes:
            position_sleeves(sleeve_meshes)
        
        if cuff_meshes and sleeve_meshes:
            position_cuffs_under_sleeves(cuff_meshes, sleeve_meshes)
        
        if waistband_meshes and panel_meshes:
            position_waistband_under_front_panel(waistband_meshes, panel_meshes)
        
        if hood_meshes:
            position_hood_pieces_together(hood_meshes, panel_meshes)
        
        # Add sleeve-cuff stitching after positioning
        if cuff_meshes and sleeve_meshes:
            stitch_objects = add_sleeve_cuff_stitching(sleeve_meshes, cuff_meshes)
            created_meshes.extend(stitch_objects)
        
    else:
        return []



try:
    generate_garment("hoodie", "FashionSynth_Test")

except Exception as e:
    traceback.print_exc()

