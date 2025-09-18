import bpy
import urllib.request
import ssl
import re
import math
import bmesh
import mathutils
import xml.etree.ElementTree as ET
import traceback
from mathutils import Vector
import requests
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty
from bpy.types import Operator, Panel, PropertyGroup

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
    "back_panel": {
        "ipfs": "QmYpqS8Bvooy8VZuyYB4QCa4AEzyiKYaevLZxTMdSKQ8LW",
        "quantity": 1,
        "display_name": "Back Panel",
        "description": "Back panel pattern piece for hoodie with fold cutting line"
    },
    "hood": {
        "ipfs": "QmZCiFkntv59eDymtZKpLbFuy1HHVBgWk7YxJbousgUhmE",
        "quantity": 2,
        "display_name": "Hood",
        "description": "Hood pattern piece for hoodie"
    },
    "pocket": {
        "ipfs": "QmeRcLaAJt2tMEtc6fQs4awzZJHPLUGkGsk7sM4FijBa2S",
        "quantity": 1,
        "display_name": "Pocket",
        "description": "Pocket pattern piece for hoodie"
    },
    "sleeve_cuff": {
        "ipfs": "QmR2aM7nPH6PmswKc4115GhdxbCEhwDhFAUqXBGrDZuCws",
        "quantity": 2,
        "display_name": "Sleeve Cuff",
        "description": "Sleeve cuff pattern piece for hoodie"
    },
    "sleeve": {
        "ipfs": "QmTEAfKjAnJ8Rm7BwgzGCtb1wE5H9J3BkSoEFgeBCeHU2a",
        "quantity": 2,
        "display_name": "Sleeve",
        "description": "Sleeve pattern piece for hoodie"
    },
    "waist_band": {
        "ipfs": "QmZQFmPophwckf4UKDCD5YMLPeism2oYNkrgFhN33N52Q6",
        "quantity": 1,
        "display_name": "Waist Band",
        "description": "Waist band pattern piece for hoodie"
    }
}

TSHIRT_DEFAULTS = {
    "back_panel": {
        "ipfs": "QmZR3yzYnKfbMMw48E7gRG71H7VGATgF6jkm3Q8LXAYehy",
        "quantity": 1,
        "display_name": "Back Panel",
        "description": "Back panel pattern piece for t-shirt with fold cutting line"
    },
    "front_panel": {
        "ipfs": "QmdrXEuXshhPUDUTsfHKzNVMrmQn68H4oPA92vBbLxBBa4",
        "quantity": 1,
        "display_name": "Front Panel",
        "description": "Front panel pattern piece for t-shirt with fold cutting line"
    },
    "neck_binding": {
        "ipfs": "QmVkhYT7SfWt4TR2gx6t9fsT76rrmqbaeZmYHLzdaSs84m",
        "quantity": 1,
        "display_name": "Neck Binding",
        "description": "Neck binding pattern piece for t-shirt collar"
    },
    "sleeve": {
        "ipfs": "Qmd8nXv1mn2D5V3nUYxpGdPmGfksAZkRru3YtRT3Nvf58j",
        "quantity": 2,
        "display_name": "Sleeve",
        "description": "Sleeve pattern piece for t-shirt"
    }
}

def get_garment_defaults(garment_type):
    garment_map = {
        "hoodie": HOODIE_DEFAULTS,
        "tshirt": TSHIRT_DEFAULTS,
    }
    return garment_map.get(garment_type, {})

def ipfs_to_gateway_url(ipfs_hash):
    if ipfs_hash.startswith("ipfs://"):
        hash_only = ipfs_hash.replace("ipfs://", "")
    else:
        hash_only = ipfs_hash
    return f"{INFURA_GATEWAY}{hash_only}"

def download_svg_from_url(url):
    try:
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

def parse_path_data(path_data):
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
        traceback.print_exc()
        return []

def get_coordinates_from_ipfs(ipfs_hash, gateway_url):
    svg_content = download_svg_from_url(gateway_url)
    
    if svg_content:
        coordinates = extract_coordinates_from_svg(svg_content)
        return coordinates
    else:
        return []

def load_svg_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading SVG file: {e}")
        return None

def get_coordinates_from_file(file_path):
    svg_content = load_svg_from_file(file_path)
    
    if svg_content:
        coordinates = extract_coordinates_from_svg(svg_content)
        return coordinates
    else:
        return []

def create_mesh_from_coordinates(coordinates, part_name, collection_name, scale_factor=None):
    if not coordinates or len(coordinates) < 6:  
        return None
    
    if "front_panel" in part_name.lower() or "back_panel" in part_name.lower():
        coordinates = auto_orient_front_panel(coordinates)
    elif "neck_binding" in part_name.lower() or "waist_band" in part_name.lower():
        coordinates = auto_orient_horizontal_piece(coordinates)
    elif "sleeve" in part_name.lower() and "cuff" not in part_name.lower():
        coordinates = auto_orient_sleeve(coordinates)
    
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
            if "sleeve" in part_name.lower() and "cuff" not in part_name.lower():
                y = float(coordinates[i]) / scale_factor    
                z = -float(coordinates[i+1]) / scale_factor  
                value = mathutils.Vector((0, y, z))         
            else:
                x = float(coordinates[i]) / scale_factor    
                z = -float(coordinates[i+1]) / scale_factor  
                value = mathutils.Vector((x, 0, z))         
            newVerts.append(value)
    
    if newVerts:
        min_x = min(v.x for v in newVerts)
        max_x = max(v.x for v in newVerts)
        min_y = min(v.y for v in newVerts)
        max_y = max(v.y for v in newVerts)
        min_z = min(v.z for v in newVerts)
        max_z = max(v.z for v in newVerts)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        
        for v in newVerts:
            v.x -= center_x
            v.y -= center_y
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
    
    if "front_panel" in part_name.lower():
        obj.location.x = 0.5
        obj.rotation_euler[2] += 1.5708
    
    if "back_panel" in part_name.lower():
        obj.location.x = -0.5
        obj.rotation_euler[2] += 1.5708
    
    if "neck_binding" in part_name.lower():
        obj.rotation_euler[2] += 1.5708
        obj.location.x = 0.5
        obj.location.y = 0
        obj.location.z = 1.0
    
    if "waist_band" in part_name.lower():
        obj.rotation_euler[2] += 1.5708
        obj.location.x = 0.5
        obj.location.y = 0
        obj.location.z = -1.0
    
    if "sleeve" in part_name.lower() and "cuff" not in part_name.lower():
        if not hasattr(create_mesh_from_coordinates, 'sleeve_counter'):
            create_mesh_from_coordinates.sleeve_counter = 0
        
        create_mesh_from_coordinates.sleeve_counter += 1
        sleeve_num = create_mesh_from_coordinates.sleeve_counter
        
        obj.location.x = 0.5
        obj.location.z = 0
        
        front_panel_edges = get_front_panel_edges()
        if front_panel_edges:
            left_edge, right_edge = front_panel_edges
            panel_width = right_edge - left_edge
            gap = 0.3  # Gap between panel edge and sleeve
            sleeve_distance = panel_width/2 + gap
            
            
            # Store intended positions
            if sleeve_num == 1:
                intended_y = -sleeve_distance
            elif sleeve_num == 2:
                intended_y = sleeve_distance
            else:
                intended_y = sleeve_num * 2.0
        else:
            if sleeve_num == 1:
                intended_y = -1.5
            elif sleeve_num == 2:
                intended_y = 1.5
            else:
                intended_y = sleeve_num * 2.0
        
        # Set initial position
        obj.location.y = intended_y
        
        # Set origin to geometry (this might change position)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        
        # Restore intended position after origin change
        obj.location.x = 0.5
        obj.location.y = intended_y
        obj.location.z = 0
        
        # Ensure curved edge faces the front panel
        ensure_sleeve_curved_edge_faces_panel(obj, sleeve_num)
    
    if "pocket" in part_name.lower():
        position_pocket_on_front_panel(obj)
    
    print(f"DEBUG: Checking part_name '{part_name}' for hood pattern")
    print(f"DEBUG: '_hood_' in '{part_name.lower()}'? {('_hood_' in part_name.lower())}")
    
    if "_hood_" in part_name.lower():
        print(f"DEBUG: HOOD MATCHED - calling position_hood_safely for {part_name}")
        position_hood_safely(obj)
    elif "sleeve_cuff" in part_name.lower():
        print(f"DEBUG: SLEEVE CUFF MATCHED - orienting {part_name}")
        orient_sleeve_cuff_longest_edge_y(obj)
    else:
        print(f"DEBUG: Hood pattern NOT matched for {part_name}")
    
    return obj

def ensure_sleeve_curved_edge_faces_panel(sleeve_obj, sleeve_num):
    """Ensure the curved edge of the sleeve is closest to the front panel"""
    
    mesh = sleeve_obj.data
    if not mesh or not mesh.vertices:
        return
    
    verts = mesh.vertices
    
    # Get the left and right edges of the sleeve (in Y direction)
    min_y = min(v.co.y for v in verts)
    max_y = max(v.co.y for v in verts)
    
    # Get points on left edge and right edge
    left_edge_points = [v.co for v in verts if abs(v.co.y - min_y) < 0.1]
    right_edge_points = [v.co for v in verts if abs(v.co.y - max_y) < 0.1]
    
    # Calculate curvature for both edges
    left_curvature = calculate_edge_curvature(left_edge_points)
    right_curvature = calculate_edge_curvature(right_edge_points)
    
    
    # Get the intended position for this sleeve (before any potential flip)
    intended_x = sleeve_obj.location.x
    intended_y = sleeve_obj.location.y
    intended_z = sleeve_obj.location.z
    
    
    # Determine which edge is more curved
    if sleeve_num == 1:  # Left sleeve
        # For left sleeve, curved edge should be on the right (closer to front panel)
        if left_curvature > right_curvature:
            # Need to flip - curved edge is on wrong side
            sleeve_obj.rotation_euler[0] = math.pi  # Rotate 180 degrees around X axis
            # Restore full intended position after flip
            sleeve_obj.location.x = intended_x
            sleeve_obj.location.y = intended_y
            sleeve_obj.location.z = intended_z
    else:  # Right sleeve (sleeve_num == 2)
        # For right sleeve, curved edge should be on the left (closer to front panel)
        if right_curvature > left_curvature:
            # Need to flip - curved edge is on wrong side
            sleeve_obj.rotation_euler[0] = math.pi  # Rotate 180 degrees around X axis
            # Restore full intended position after flip
            sleeve_obj.location.x = intended_x
            sleeve_obj.location.y = intended_y
            sleeve_obj.location.z = intended_z

def calculate_edge_curvature(edge_points):
    """Calculate curvature of an edge based on its points"""
    if len(edge_points) < 3:
        return 0
    
    # Sort points by Z coordinate
    sorted_points = sorted(edge_points, key=lambda p: p.z)
    
    if len(sorted_points) < 3:
        return 0
    
    # Calculate total deviation from straight line
    start = sorted_points[0]
    end = sorted_points[-1]
    
    total_deviation = 0
    for i in range(1, len(sorted_points) - 1):
        point = sorted_points[i]
        # Calculate distance from point to line between start and end
        t = (point.z - start.z) / (end.z - start.z) if end.z != start.z else 0
        line_x = start.x + t * (end.x - start.x)
        line_y = start.y + t * (end.y - start.y)
        
        deviation = math.sqrt((point.x - line_x)**2 + (point.y - line_y)**2)
        total_deviation += deviation
    
    return total_deviation / (len(sorted_points) - 2) if len(sorted_points) > 2 else 0

def position_pocket_on_front_panel(pocket_obj):
    """Position pocket slightly in front of the front panel, above its bottom edge"""
    
    # Find the front panel
    front_panel = None
    for obj in bpy.data.objects:
        if "front_panel" in obj.name.lower():
            front_panel = obj
            break
    
    if not front_panel:
        return
    
    # Get front panel bounds
    if front_panel.data and front_panel.data.vertices:
        verts = front_panel.data.vertices
        world_verts = [front_panel.matrix_world @ v.co for v in verts]
        
        # Find front panel's bottom edge (minimum Z)
        min_z = min(v.z for v in world_verts)
        
        # Get front panel's X position
        front_x = front_panel.location.x
        
        # Get pocket height to position it properly
        if pocket_obj.data and pocket_obj.data.vertices:
            pocket_verts = pocket_obj.data.vertices
            pocket_height = max(v.co.z for v in pocket_verts) - min(v.co.z for v in pocket_verts)
        else:
            pocket_height = 0.5  # Default if can't get height
        
        # Position pocket:
        # - X: slightly in front of front panel (add 0.1)
        # - Y: centered (0)
        # - Z: slightly above bottom edge (add pocket height/2 + small gap)
        pocket_obj.location.x = front_x + 0.1  # Slightly in front
        pocket_obj.location.y = 0  # Centered on Y
        pocket_obj.location.z = min_z + pocket_height/2 + 0.2  # Above bottom edge
        
        
        # Orient pocket so longest straight edge runs horizontally along Y axis
        orient_pocket_longest_edge_horizontal(pocket_obj)

def orient_pocket_longest_edge_horizontal(pocket_obj):
    """Orient pocket so its longest straight edge runs horizontally along Y axis"""
    
    if not pocket_obj.data or not pocket_obj.data.vertices:
        return
    
    verts = pocket_obj.data.vertices
    points = [v.co for v in verts]
    
    # Find all edges and their lengths
    edges = []
    for i in range(len(points)):
        next_i = (i + 1) % len(points)
        p1 = points[i]
        p2 = points[next_i]
        
        # Calculate edge length and straightness
        length = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2 + (p2.z - p1.z)**2)
        
        # Calculate angle of edge in XZ plane to orient toward Y axis
        # We want longest edge to run along X, then we'll rotate to make it run along Y
        edge_angle = math.atan2(p2.z - p1.z, p2.x - p1.x)
        
        edges.append({
            'start': p1,
            'end': p2, 
            'length': length,
            'angle': edge_angle,
            'index': i
        })
    
    # Find longest edge
    longest_edge = max(edges, key=lambda e: e['length'])
    
    
    # Calculate rotation needed to make longest edge horizontal (angle = 0)
    current_angle = longest_edge['angle']
    required_rotation = -current_angle
   
    # Apply rotation around Z axis to make longest edge run along Y axis
    # First make edge horizontal (along X), then add 90° to make it run along Y
    pocket_obj.rotation_euler[2] += required_rotation + math.pi/2

def position_hood_safely(hood_obj):
    """Position hood above back panel using only object locations - NO matrix_world"""
    
    # Find back panel using only object location (no matrix_world access)
    back_panel = None
    for obj in bpy.data.objects:
        if "back_panel" in obj.name.lower():
            back_panel = obj
            break
    
    if not back_panel:
        print("DEBUG: Back panel not found for hood positioning")
        # Fallback position if no back panel
        hood_obj.location.x = -0.5  # Default back panel X
        hood_obj.location.y = 0
        hood_obj.location.z = 2.0
        return
    
    # Use only object location and local mesh bounds (NO matrix_world)
    back_x = back_panel.location.x
    back_y = back_panel.location.y  
    back_z = back_panel.location.z
    
    print(f"DEBUG: Back panel location: X={back_x:.3f}, Y={back_y:.3f}, Z={back_z:.3f}")
    
    # Get back panel local mesh height (avoiding matrix_world)
    if back_panel.data and back_panel.data.vertices:
        back_verts = back_panel.data.vertices
        back_local_max_z = max(v.co.z for v in back_verts)
        back_top_world_z = back_z + back_local_max_z
    else:
        back_top_world_z = back_z + 1.0  # Fallback
    
    # Orient hood so width (shortest cross-section) runs along Y axis
    if hood_obj.data and hood_obj.data.vertices:
        hood_verts = hood_obj.data.vertices
        
        # Test all possible 90-degree rotations to find the hood's width along Y axis
        best_rotation_x = 0
        best_rotation_y = 0  
        best_rotation_z = 0
        best_score = -1
        
        print("DEBUG: Testing all rotations to find optimal Y orientation...")
        
        # Test rotations around X, Y, Z axes
        for rot_x in [0, 90, 180, 270]:
            for rot_y in [0, 90, 180, 270]:
                for rot_z in [0, 90, 180, 270]:
                    # Apply test rotation
                    hood_obj.rotation_euler[0] = math.radians(rot_x)
                    hood_obj.rotation_euler[1] = math.radians(rot_y)
                    hood_obj.rotation_euler[2] = math.radians(rot_z)
                    
                    # Update mesh to get new coordinates
                    bpy.context.view_layer.update()
                    
                    # Calculate spans in all dimensions using WORLD coordinates
                    world_verts = [hood_obj.matrix_world @ v.co for v in hood_verts]
                    min_x = min(v.x for v in world_verts)
                    max_x = max(v.x for v in world_verts)
                    min_y = min(v.y for v in world_verts)
                    max_y = max(v.y for v in world_verts)
                    min_z = min(v.z for v in world_verts)
                    max_z = max(v.z for v in world_verts)
                    
                    x_span = max_x - min_x
                    y_span = max_y - min_y
                    z_span = max_z - min_z
                    
                    # Score: want Y=width (smaller) and Z=height (larger)
                    # Higher score = better orientation
                    score = 0
                    if y_span > 0.01 and z_span > 0.01:  # Both Y and Z have meaningful spans
                        if y_span < z_span:  # Y is width, Z is height
                            score = 1000 / y_span  # Prefer smaller Y span (smaller width)
                    
                    print(f"DEBUG: Rotation X={rot_x}° Y={rot_y}° Z={rot_z}° → X:{x_span:.3f} Y:{y_span:.3f} Z:{z_span:.3f} Score:{score:.1f}")
                    
                    # Keep track of best rotation
                    if score > best_score:
                        best_score = score
                        best_rotation_x = rot_x
                        best_rotation_y = rot_y
                        best_rotation_z = rot_z
        
        # Apply the best rotation
        hood_obj.rotation_euler[0] = math.radians(best_rotation_x)
        hood_obj.rotation_euler[1] = math.radians(best_rotation_y)
        hood_obj.rotation_euler[2] = math.radians(best_rotation_z)
        
        print(f"DEBUG: Best orientation: X={best_rotation_x}° Y={best_rotation_y}° Z={best_rotation_z}° with score: {best_score:.1f}")
        
        # Update mesh and get final bounds
        bpy.context.view_layer.update()
        min_z = min(v.co.z for v in hood_verts)
        hood_local_min_z = min_z
    else:
        hood_local_min_z = 0
    
    # Position hoods side by side with straight edges facing each other
    gap = 0.2
    hood_obj.location.x = back_x  # Same X as back panel
    hood_obj.location.z = back_top_world_z + gap - hood_local_min_z  # Above back panel
    
    # Determine hood number from object name
    hood_num = 1
    if "hood_2" in hood_obj.name.lower():
        hood_num = 2
    
    # Calculate hood width after orientation
    bpy.context.view_layer.update()
    world_verts = [hood_obj.matrix_world @ v.co for v in hood_obj.data.vertices]
    min_y = min(v.y for v in world_verts)
    max_y = max(v.y for v in world_verts)
    hood_width = max_y - min_y
    
    # Position hoods side by side
    hood_offset = hood_width / 2 + 0.1  # Small gap between hoods
    
    if hood_num == 1:
        # Hood 1: negative Y side, straight edge faces toward center (Y=0)
        hood_obj.location.y = -hood_offset
        print(f"DEBUG: Hood 1 positioned at negative Y with straight edge toward center")
    else:
        # Hood 2: positive Y side, FLIP so straight edge faces toward center (Y=0)
        # Flip hood 2 around Z axis (180 degrees) to mirror it
        hood_obj.rotation_euler[2] += math.pi  # Add 180 degrees
        hood_obj.location.y = hood_offset
        print(f"DEBUG: Hood 2 FLIPPED and positioned at positive Y with straight edge toward center")
    
    print(f"DEBUG: Positioned hood {hood_num} at X={hood_obj.location.x:.3f}, Y={hood_obj.location.y:.3f}, Z={hood_obj.location.z:.3f}")
    print(f"DEBUG: Hood width: {hood_width:.3f}, offset: {hood_offset:.3f}")

def orient_sleeve_cuff_longest_edge_y(cuff_obj):
    """Orient sleeve cuff so longest edge runs along Z axis (up-down) and shortest on Y axis (left-right)"""
    
    if not cuff_obj.data or not cuff_obj.data.vertices:
        return
    
    cuff_verts = cuff_obj.data.vertices
    
    # Test all possible 90-degree rotations to find Z=longest, Y=shortest
    best_rotation_x = 0
    best_rotation_y = 0  
    best_rotation_z = 0
    best_score = -1
    
    print("DEBUG: Testing all rotations to find Z=longest height, Y=shortest width for sleeve cuff...")
    
    # Test rotations around X, Y, Z axes
    for rot_x in [0, 90, 180, 270]:
        for rot_y in [0, 90, 180, 270]:
            for rot_z in [0, 90, 180, 270]:
                # Apply test rotation
                cuff_obj.rotation_euler[0] = math.radians(rot_x)
                cuff_obj.rotation_euler[1] = math.radians(rot_y)
                cuff_obj.rotation_euler[2] = math.radians(rot_z)
                
                # Update mesh to get new coordinates
                bpy.context.view_layer.update()
                
                # Calculate spans in all dimensions using WORLD coordinates
                world_verts = [cuff_obj.matrix_world @ v.co for v in cuff_verts]
                min_x = min(v.x for v in world_verts)
                max_x = max(v.x for v in world_verts)
                min_y = min(v.y for v in world_verts)
                max_y = max(v.y for v in world_verts)
                min_z = min(v.z for v in world_verts)
                max_z = max(v.z for v in world_verts)
                
                x_span = max_x - min_x
                y_span = max_y - min_y
                z_span = max_z - min_z
                
                # Calculate score: want Y to be largest dimension and Z to be smallest
                # For flat objects, Z might be 0, which is perfectly fine as "shortest"
                dimensions = [x_span, y_span, z_span]
                max_dim = max(dimensions)
                min_dim = min(dimensions)
                
                score = 0
                
                print(f"DEBUG: Cuff rotation X={rot_x}° Y={rot_y}° Z={rot_z}° → X:{x_span:.3f} Y:{y_span:.3f} Z:{z_span:.3f}")
                print(f"  Max dimension: {max_dim:.3f}, Min dimension: {min_dim:.3f}")
                
                # We want the cuff oriented in Y-Z plane (not X-Y plane!)
                # X should be minimal (thickness), Z should be longest (height), Y should be shortest (width)
                
                # Check if X is minimal (close to 0 for flat garment piece)
                # AND Z is the longest dimension AND Y is the shortest dimension
                if x_span <= 0.1 and z_span == max_dim and y_span == min_dim:
                    # Perfect score - oriented in Y-Z plane with Z=longest, Y=shortest
                    score = 1000 + z_span  # High base score plus Z span
                    print(f"  PERFECT! Y-Z plane orientation: X={x_span:.3f} Y={y_span:.3f} Z={z_span:.3f} - Score: {score:.1f}")
                elif x_span <= 0.1 and z_span == max_dim:
                    # In Y-Z plane with Z longest but Y not shortest
                    score = 500 + z_span - (y_span * 10)  # Penalize non-shortest Y
                    print(f"  GOOD: Y-Z plane, Z longest but Y not shortest - Score: {score:.1f}")
                elif x_span <= 0.1 and y_span == min_dim:
                    # In Y-Z plane with Y shortest but Z not longest
                    score = 300 + z_span - (abs(z_span - max_dim) * 10)  # Penalize Z not being longest
                    print(f"  OK: Y-Z plane, Y shortest but Z not longest - Score: {score:.1f}")
                elif x_span <= 0.1:
                    # At least in Y-Z plane
                    score = 100 + z_span
                    print(f"  FAIR: Y-Z plane but wrong Y/Z orientation - Score: {score:.1f}")
                else:
                    # Not in Y-Z plane at all
                    print(f"  BAD: Not in Y-Z plane (X={x_span:.3f} too large) - Score: 0.0")
                
                # Keep track of best rotation
                if score > best_score:
                    best_score = score
                    best_rotation_x = rot_x
                    best_rotation_y = rot_y
                    best_rotation_z = rot_z
                    print(f"    NEW BEST! X={rot_x}° Y={rot_y}° Z={rot_z}° Score: {score:.1f}")
    
    # Apply the best rotation (Z=longest height, Y=shortest width)
    cuff_obj.rotation_euler[0] = math.radians(best_rotation_x)
    cuff_obj.rotation_euler[1] = math.radians(best_rotation_y)
    cuff_obj.rotation_euler[2] = math.radians(best_rotation_z)
    
    print(f"DEBUG: FINAL cuff orientation: X={best_rotation_x}° Y={best_rotation_y}° Z={best_rotation_z}° with score: {best_score:.1f}")
    
    # Update mesh one final time and log final dimensions
    bpy.context.view_layer.update()
    world_verts = [cuff_obj.matrix_world @ v.co for v in cuff_verts]
    final_x = max(v.x for v in world_verts) - min(v.x for v in world_verts)
    final_y = max(v.y for v in world_verts) - min(v.y for v in world_verts)
    final_z = max(v.z for v in world_verts) - min(v.z for v in world_verts)
    print(f"DEBUG: FINAL dimensions: X={final_x:.3f} Y={final_y:.3f} Z={final_z:.3f}")

def position_sleeve_cuff_next_to_sleeve(cuff_obj):
    """Position sleeve cuff next to its corresponding sleeve at same X and Z, offset in Y"""
    
    if not cuff_obj:
        return
    
    # Determine which cuff this is (1 or 2) from the name
    cuff_name = cuff_obj.name.lower()
    if "1" in cuff_name or "left" in cuff_name:
        cuff_num = 1
        sleeve_pattern = ["hoodie_sleeve_1", "sleeve_1", "left_sleeve", "sleeve1"]
    elif "2" in cuff_name or "right" in cuff_name:
        cuff_num = 2  
        sleeve_pattern = ["hoodie_sleeve_2", "sleeve_2", "right_sleeve", "sleeve2"]
    else:
        # Default to first sleeve if can't determine
        cuff_num = 1
        sleeve_pattern = ["hoodie_sleeve_1", "sleeve_1", "left_sleeve", "sleeve1", "sleeve"]
    
    # Find the corresponding sleeve
    sleeve_obj = None
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        for pattern in sleeve_pattern:
            if pattern in obj_name:
                sleeve_obj = obj
                break
        if sleeve_obj:
            break
    
    # If still no sleeve found, try to find any sleeve
    if not sleeve_obj:
        print(f"DEBUG: No exact match found, searching for any sleeve...")
        for obj in bpy.data.objects:
            print(f"DEBUG: Checking object: {obj.name}")
            if "sleeve" in obj.name.lower() and "cuff" not in obj.name.lower():
                sleeve_obj = obj
                print(f"DEBUG: Using fallback sleeve: {obj.name}")
                break
    
    if not sleeve_obj:
        print(f"DEBUG: No sleeve found for cuff {cuff_obj.name}")
        return
    
    print(f"DEBUG: Positioning cuff {cuff_obj.name} next to sleeve {sleeve_obj.name}")
    
    # Get sleeve dimensions and position
    if sleeve_obj.data and sleeve_obj.data.vertices:
        sleeve_verts = sleeve_obj.data.vertices
        sleeve_world_verts = [sleeve_obj.matrix_world @ v.co for v in sleeve_verts]
        
        # Get sleeve bounds
        sleeve_min_y = min(v.y for v in sleeve_world_verts)
        sleeve_max_y = max(v.y for v in sleeve_world_verts)
        sleeve_width = sleeve_max_y - sleeve_min_y
        
        # Get cuff width to calculate offset
        if cuff_obj.data and cuff_obj.data.vertices:
            cuff_verts = cuff_obj.data.vertices  
            cuff_world_verts = [cuff_obj.matrix_world @ v.co for v in cuff_verts]
            cuff_width = max(v.y for v in cuff_world_verts) - min(v.y for v in cuff_world_verts)
        else:
            cuff_width = 1.0  # Default
        
        # Position cuff at same X and Z as sleeve, but offset in Y
        cuff_obj.location.x = sleeve_obj.location.x  # Same front/back position
        cuff_obj.location.z = sleeve_obj.location.z  # Same up/down position
        
        # Offset in Y direction (left/right) - reduced spacing
        offset = (sleeve_width + cuff_width) / 2 + 0.1  # Very small gap between sleeve and cuff
        
        if cuff_num == 1:
            # Cuff 1: position to the left of sleeve (negative Y)
            cuff_obj.location.y = sleeve_min_y - offset
            print(f"DEBUG: Positioned cuff 1 to LEFT of sleeve at Y={cuff_obj.location.y:.3f}")
        else:
            # Cuff 2: position to the right of sleeve (positive Y) 
            cuff_obj.location.y = sleeve_max_y + offset
            print(f"DEBUG: Positioned cuff 2 to RIGHT of sleeve at Y={cuff_obj.location.y:.3f}")
        
        print(f"DEBUG: Cuff final position: X={cuff_obj.location.x:.3f}, Y={cuff_obj.location.y:.3f}, Z={cuff_obj.location.z:.3f}")
    else:
        print(f"DEBUG: Sleeve {sleeve_obj.name} has no vertex data")

def get_front_panel_edges():
    for obj in bpy.data.objects:
        if "front_panel" in obj.name.lower():
            if obj.data and obj.data.vertices:
                verts = obj.data.vertices
                world_verts = [obj.matrix_world @ v.co for v in verts]
                min_y = min(v.y for v in world_verts)
                max_y = max(v.y for v in world_verts)
                print(f"DEBUG: Found front panel Y range: {min_y:.3f} to {max_y:.3f}")
                return (min_y, max_y)
    
    print("DEBUG: Front panel not found")
    return None

def markSeam(mesh_obj):
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




def find_mirror_line_and_visualize(coordinates, part_name="test"):
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    if len(points) < 4:
        return None
    
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    best_mirror_line = None
    best_symmetry_score = 0
    best_angle = 0
    
    num_test_angles = 18
    for i in range(num_test_angles):
        angle = i * math.pi / num_test_angles
        
        line_direction = (math.cos(angle), math.sin(angle))
        line_length = max(max_x - min_x, max_y - min_y) * 2
        
        line_start = (center_x - line_direction[0] * line_length, center_y - line_direction[1] * line_length)
        line_end = (center_x + line_direction[0] * line_length, center_y + line_direction[1] * line_length)
        
        symmetry_score = calculate_mirror_symmetry_score(points, (line_start, line_end))
        
        
        if symmetry_score > best_symmetry_score:
            best_symmetry_score = symmetry_score
            best_mirror_line = (line_start, line_end)
            best_angle = angle
    
    
    if best_mirror_line and best_symmetry_score > 0.4:
        return best_mirror_line
    else:
        return None

def calculate_mirror_symmetry_score(points, mirror_line):
    line_start, line_end = mirror_line
    
    matches = 0
    total_points = len(points)
    
    for point in points:
        mirrored_point = mirror_point_across_line(point, line_start, line_end)
        
        min_distance = float('inf')
        for other_point in points:
            distance = math.sqrt((mirrored_point[0] - other_point[0])**2 + (mirrored_point[1] - other_point[1])**2)
            min_distance = min(min_distance, distance)
        
        tolerance = 50
        if min_distance < tolerance:
            matches += 1
    
    return matches / total_points if total_points > 0 else 0

def mirror_point_across_line(point, line_start, line_end):
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return point
    
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    mirrored_x = 2 * closest_x - px
    mirrored_y = 2 * closest_y - py
    
    return (mirrored_x, mirrored_y)

def auto_orient_sleeve(coordinates):
    print("DEBUG: auto_orient_sleeve called")
    print(f"DEBUG: coordinates length: {len(coordinates)}")
    
    mirror_line = find_mirror_line_and_visualize(coordinates, "sleeve")
    if mirror_line:
        print("DEBUG: Found sleeve mirror line")
        
        aligned_coords = align_mirror_line_to_y_axis(coordinates, mirror_line)
        print("DEBUG: Aligned sleeve mirror line to Y axis")
        return aligned_coords
    else:
        print("DEBUG: No sleeve mirror line found")
        return coordinates

def align_mirror_line_to_y_axis(coordinates, mirror_line):
    line_start, line_end = mirror_line
    
    mirror_dx = line_end[0] - line_start[0]
    mirror_dy = line_end[1] - line_start[1]
    current_angle = math.atan2(mirror_dy, mirror_dx)
    
    target_angle = 0
    rotation_needed = target_angle - current_angle
    
    print(f"DEBUG: Current mirror angle: {math.degrees(current_angle):.1f}°")
    print(f"DEBUG: Rotating by: {math.degrees(rotation_needed):.1f}°")
    
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    mirror_center_x = (line_start[0] + line_end[0]) / 2
    mirror_center_y = (line_start[1] + line_end[1]) / 2
    
    rotated_points = []
    for x, y in points:
        temp_x = x - mirror_center_x
        temp_y = y - mirror_center_y
        
        cos_angle = math.cos(rotation_needed)
        sin_angle = math.sin(rotation_needed)
        new_x = temp_x * cos_angle - temp_y * sin_angle
        new_y = temp_x * sin_angle + temp_y * cos_angle
        
        final_x = new_x + mirror_center_x
        final_y = new_y + mirror_center_y
        rotated_points.append((final_x, final_y))
    
    final_coords = []
    for x, y in rotated_points:
        final_coords.extend([x, y])
    
    return final_coords


def auto_orient_horizontal_piece(coordinates):
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
        
    best_rotation = 0
    best_horizontal_span = 0
    
    for rotation in [0, 90, 180, 270]:
        if rotation == 0:
            test_coords = coordinates
        else:
            test_coords = rotate_coordinates(coordinates, rotation)
        
        test_points = []
        for i in range(0, len(test_coords)-1, 2):
            if i+1 < len(test_coords):
                test_points.append((test_coords[i], test_coords[i+1]))
        
        min_x = min(p[0] for p in test_points)
        max_x = max(p[0] for p in test_points)
        horizontal_span = max_x - min_x
        
        if horizontal_span > best_horizontal_span:
            best_horizontal_span = horizontal_span
            best_rotation = rotation
    
    if best_rotation == 0:
        return coordinates
    else:
        return rotate_coordinates(coordinates, best_rotation)

def auto_orient_front_panel(coordinates):
    for rotation in [0, 90, 180, 270]:
        if rotation == 0:
            test_coords = coordinates
        else:
            test_coords = rotate_coordinates(coordinates, rotation)
        
        points = []
        for i in range(0, len(test_coords)-1, 2):
            if i+1 < len(test_coords):
                points.append((test_coords[i], test_coords[i+1]))
        
        if len(points) < 4:
            continue
            
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        if height > width:
            mirrored_coords = mirror_vertically(test_coords)
            return mirrored_coords
    
    mirrored_coords = mirror_vertically(coordinates)
    return mirrored_coords

def mirror_vertically(coordinates):
    points = []
    for i in range(0, len(coordinates)-1, 2):
        if i+1 < len(coordinates):
            points.append((coordinates[i], coordinates[i+1]))
    
    longest_straight_x = find_longest_straight_z_line(points)
    fold_x = longest_straight_x
    
    mirrored_points = []
    for x, y in points:
        mirrored_x = 2 * fold_x - x
        mirrored_points.append((mirrored_x, y))
    
    mirrored_points.reverse()
    full_points = points + mirrored_points
    
    full_coordinates = []
    for x, y in full_points:
        full_coordinates.extend([x, y])
    
    return full_coordinates

def find_longest_straight_z_line(points):
    straight_lines = []
    tolerance = 5
    
    for i in range(len(points)):
        for j in range(i + 2, len(points)):
            p1 = points[i]
            p2 = points[j]
            
            if abs(p1[0] - p2[0]) < tolerance:
                length = abs(p2[1] - p1[1])
                avg_x = (p1[0] + p2[0]) / 2
                straight_lines.append((length, avg_x))
    
    if straight_lines:
        longest = max(straight_lines, key=lambda x: x[0])
        return longest[1]
    else:
        max_x = max(p[0] for p in points)
        return max_x

def rotate_coordinates(coordinates, rotation_degrees):
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

class FASHIONSYNTH_Properties(PropertyGroup):
    garment_type: EnumProperty(
        description="Select garment type",
        items=[
            ('hoodie', "Hoodie", "Hoodie garment"),
            ('tshirt', "T-Shirt", "T-Shirt garment")
        ],
        default='hoodie'
    )
    
    loading_method: EnumProperty(
        description="Choose how to load garment",
        items=[
            ('coinop', "Coin Op Default", "Use default patterns"),
            ('custom', "Custom", "Load custom SVG files")
        ],
        default='coinop'
    )
    
    front_panel_file: StringProperty(
        name="Front Panel",
        description="Front panel SVG file",
        default="",
        subtype='FILE_PATH'
    )
    
    back_panel_file: StringProperty(
        name="Back Panel",
        description="Back panel SVG file",
        default="",
        subtype='FILE_PATH'
    )
    
    sleeve_file: StringProperty(
        name="Sleeve",
        description="Sleeve SVG file", 
        default="",
        subtype='FILE_PATH'
    )
    
    hood_file: StringProperty(
        name="Hood",
        description="Hood SVG file",
        default="",
        subtype='FILE_PATH'
    )
    
    pocket_file: StringProperty(
        name="Pocket",
        description="Pocket SVG file",
        default="",
        subtype='FILE_PATH'
    )
    
    sleeve_cuff_file: StringProperty(
        name="Sleeve Cuff",
        description="Sleeve cuff SVG file",
        default="",
        subtype='FILE_PATH'
    )
    
    waist_band_file: StringProperty(
        name="Waist Band",
        description="Waist band SVG file",
        default="",
        subtype='FILE_PATH'
    )
    
    neck_binding_file: StringProperty(
        name="Neck Binding",
        description="Neck binding SVG file",
        default="",
        subtype='FILE_PATH'
    )

class FASHIONSYNTH_OT_load_defaults(Operator):
    bl_idname = "fashionsynth.load_defaults"
    bl_label = "Load Garment Defaults"
    bl_description = "Load default garment pieces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.fashionsynth_props
        
        defaults = get_garment_defaults(props.garment_type)
        if not defaults:
            self.report({'ERROR'}, f"No defaults found for {props.garment_type}")
            return {'CANCELLED'}
        
        created_count = 0
        
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
                mesh_name = f"{props.garment_type}_{part_name}_{i+1}" if quantity > 1 else f"{props.garment_type}_{part_name}"
                
                mesh_obj = create_mesh_from_coordinates(
                    coordinates,
                    mesh_name,
                    "FashionSynth"
                )
                
                if mesh_obj:
                    markSeam(mesh_obj)
                    created_count += 1
        
        # Position sleeve cuffs next to their sleeves after all pieces are created
        print("DEBUG: Positioning sleeve cuffs next to sleeves...")
        for obj in bpy.data.objects:
            if "sleeve_cuff" in obj.name.lower():
                print(f"DEBUG: FINAL POSITIONING - moving {obj.name} next to sleeve")
                position_sleeve_cuff_next_to_sleeve(obj)
        
        self.report({'INFO'}, f"Created {created_count} pieces for {props.garment_type}")
        return {'FINISHED'}

class FASHIONSYNTH_OT_load_custom(Operator):
    bl_idname = "fashionsynth.load_custom"
    bl_label = "Load Custom Files"
    bl_description = "Load custom SVG files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.fashionsynth_props
        
        defaults = get_garment_defaults(props.garment_type)
        if not defaults:
            self.report({'ERROR'}, f"No part definitions found for {props.garment_type}")
            return {'CANCELLED'}
        
        created_count = 0
        
        for part_name, part_info in defaults.items():
            file_attr = f"{part_name}_file"
            file_path = getattr(props, file_attr, "")
            
            if not file_path:
                continue
                
            if not file_path.lower().endswith('.svg'):
                self.report({'ERROR'}, f"{part_name} file must be an SVG")
                continue
            
            coordinates = get_coordinates_from_file(file_path)
            
            if not coordinates:
                self.report({'WARNING'}, f"Failed to load coordinates from {part_name}")
                continue
            
            quantity = part_info.get("quantity", 1)
            
            for i in range(quantity):
                mesh_name = f"{props.garment_type}_{part_name}_{i+1}" if quantity > 1 else f"{props.garment_type}_{part_name}"
                
                mesh_obj = create_mesh_from_coordinates(
                    coordinates,
                    mesh_name,
                    "FashionSynth"
                )
                
                if mesh_obj:
                    markSeam(mesh_obj)
                    created_count += 1
        
        if created_count == 0:
            self.report({'ERROR'}, "No valid SVG files loaded")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Created {created_count} pieces from custom files")
        return {'FINISHED'}

class FASHIONSYNTH_OT_clear_scene(Operator):
    bl_idname = "fashionsynth.clear_scene"
    bl_label = "Clear Scene"
    bl_description = "Clear all objects from scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)
        
        self.report({'INFO'}, "Scene cleared")
        return {'FINISHED'}

class FASHIONSYNTH_PT_main_panel(Panel):
    bl_label = "FashionSynth"
    bl_idname = "FASHIONSYNTH_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FashionSynth'

    def draw(self, context):
        layout = self.layout
        props = context.scene.fashionsynth_props
        
        layout.label(text="Garment Type", icon='MESH_DATA')
        
        box = layout.box()
        box.prop(props, "garment_type", text="")
        
        layout.separator()
        layout.label(text="Loading Method", icon='IMPORT')
        
        method_box = layout.box()
        method_box.prop(props, "loading_method", text="")
        
        if props.loading_method == 'coinop':
            method_box.operator("fashionsynth.load_defaults", 
                               text=f"Load {props.garment_type.title()} Defaults", 
                               icon='IMPORT')
        
        elif props.loading_method == 'custom':
            custom_box = layout.box()
            custom_box.label(text="Upload SVG Files", icon='FILEBROWSER')
            
            defaults = get_garment_defaults(props.garment_type)
            if defaults:
                for part_name, part_info in defaults.items():
                    file_attr = f"{part_name}_file"
                    display_name = part_info.get("display_name", part_name.replace('_', ' ').title())
                    if hasattr(props, file_attr):
                        custom_box.prop(props, file_attr, text=display_name)
            
            custom_box.operator("fashionsynth.load_custom", icon='IMPORT')
        
        layout.separator()
        layout.operator("fashionsynth.clear_scene", icon='TRASH')

classes = [
    FASHIONSYNTH_Properties,
    FASHIONSYNTH_OT_load_defaults,
    FASHIONSYNTH_OT_load_custom,
    FASHIONSYNTH_OT_clear_scene,
    FASHIONSYNTH_PT_main_panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.fashionsynth_props = bpy.props.PointerProperty(type=FASHIONSYNTH_Properties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.fashionsynth_props

if __name__ == "__main__":
    register()