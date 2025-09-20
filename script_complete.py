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

# Don't auto-clear when loaded as addon
# bpy.ops.object.select_all(action='SELECT')
# bpy.ops.object.delete(use_global=False, confirm=False)

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
  
    if "_hood_" in part_name.lower():
        position_hood_safely(obj)
    elif "sleeve_cuff" in part_name.lower():
        orient_sleeve_cuff_longest_edge_y(obj)
    
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
    else:  
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
        # Fallback position if no back panel
        hood_obj.location.x = -0.5  # Default back panel X
        hood_obj.location.y = 0
        hood_obj.location.z = 2.0
        return
    
    # Use only object location and local mesh bounds (NO matrix_world)
    back_x = back_panel.location.x
    back_y = back_panel.location.y  
    back_z = back_panel.location.z
    
    
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
    else:
        # Hood 2: positive Y side, FLIP so straight edge faces toward center (Y=0)
        # Flip hood 2 around Z axis (180 degrees) to mirror it
        hood_obj.rotation_euler[2] += math.pi  # Add 180 degrees
        hood_obj.location.y = hood_offset
    

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
                

                # We want the cuff oriented in Y-Z plane (not X-Y plane!)
                # X should be minimal (thickness), Z should be longest (height), Y should be shortest (width)
                
                # Check if X is minimal (close to 0 for flat garment piece)
                # AND Z is the longest dimension AND Y is the shortest dimension
                if x_span <= 0.1 and z_span == max_dim and y_span == min_dim:
                    # Perfect score - oriented in Y-Z plane with Z=longest, Y=shortest
                    score = 1000 + z_span  # High base score plus Z span
                elif x_span <= 0.1 and z_span == max_dim:
                    # In Y-Z plane with Z longest but Y not shortest
                    score = 500 + z_span - (y_span * 10)  # Penalize non-shortest Y
                elif x_span <= 0.1 and y_span == min_dim:
                    # In Y-Z plane with Y shortest but Z not longest
                    score = 300 + z_span - (abs(z_span - max_dim) * 10)  # Penalize Z not being longest
                elif x_span <= 0.1:
                    # At least in Y-Z plane
                    score = 100 + z_span
                
                
                # Keep track of best rotation
                if score > best_score:
                    best_score = score
                    best_rotation_x = rot_x
                    best_rotation_y = rot_y
                    best_rotation_z = rot_z
    
    # Apply the best rotation (Z=longest height, Y=shortest width)
    cuff_obj.rotation_euler[0] = math.radians(best_rotation_x)
    cuff_obj.rotation_euler[1] = math.radians(best_rotation_y)
    cuff_obj.rotation_euler[2] = math.radians(best_rotation_z)
    
    
    # Update mesh one final time and log final dimensions
    bpy.context.view_layer.update()
    world_verts = [cuff_obj.matrix_world @ v.co for v in cuff_verts]
    final_x = max(v.x for v in world_verts) - min(v.x for v in world_verts)
    final_y = max(v.y for v in world_verts) - min(v.y for v in world_verts)
    final_z = max(v.z for v in world_verts) - min(v.z for v in world_verts)

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
        for obj in bpy.data.objects:
            if "sleeve" in obj.name.lower() and "cuff" not in obj.name.lower():
                sleeve_obj = obj
                break
    
    if not sleeve_obj:
        return
    
    
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
        else:
            # Cuff 2: position to the right of sleeve (positive Y) 
            cuff_obj.location.y = sleeve_max_y + offset
        
    

def create_sewing_springs_between_edges(obj1, edge1, obj2, edge2):
    """Create visual sewing spring connections between two edges"""
    
    # Create a new mesh for the sewing springs visualization
    spring_mesh = bpy.data.meshes.new("SewingSpring_HoodCenter")
    spring_obj = bpy.data.objects.new("SewingSpring_HoodCenter", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    # Get edge vertices in world space
    mesh1 = obj1.data
    mesh2 = obj2.data
    
    # We need to get the edge vertex indices from the bmesh edge
    # Since we passed the edge from bmesh, we need to get back to object mode first
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get vertices for each edge
    edge1_verts = []
    edge2_verts = []
    
    # Find the edge vertices by checking all edges
    for e in mesh1.edges:
        v1_co = obj1.matrix_world @ mesh1.vertices[e.vertices[0]].co
        v2_co = obj1.matrix_world @ mesh1.vertices[e.vertices[1]].co
        
        # Check if this edge is vertical and near center
        edge_vector = v2_co - v1_co
        if abs(edge_vector.z) > 0.5 and abs(edge_vector.y) < 0.3 and abs(edge_vector.x) < 0.1:
            avg_y = (v1_co.y + v2_co.y) / 2
            if abs(avg_y) < 0.3:  # Close to center
                edge1_verts = [v1_co, v2_co]
                break
    
    for e in mesh2.edges:
        v1_co = obj2.matrix_world @ mesh2.vertices[e.vertices[0]].co
        v2_co = obj2.matrix_world @ mesh2.vertices[e.vertices[1]].co
        
        # Check if this edge is vertical and near center
        edge_vector = v2_co - v1_co
        if abs(edge_vector.z) > 0.5 and abs(edge_vector.y) < 0.3 and abs(edge_vector.x) < 0.1:
            avg_y = (v1_co.y + v2_co.y) / 2
            if abs(avg_y) < 0.3:  # Close to center
                edge2_verts = [v1_co, v2_co]
                break
    
    if not edge1_verts or not edge2_verts:
        return
    
    # Create spring connections - subdivide edges for more connection points
    num_springs = 5  # Number of spring connections along the edge
    
    spring_verts = []
    spring_edges = []
    
    for i in range(num_springs):
        t = i / (num_springs - 1) if num_springs > 1 else 0.5
        
        # Interpolate along each edge
        p1 = edge1_verts[0].lerp(edge1_verts[1], t)
        p2 = edge2_verts[0].lerp(edge2_verts[1], t)
        
        # Add vertices for this spring
        v_idx = len(spring_verts)
        spring_verts.append(p1)
        spring_verts.append(p2)
        
        # Add edge connecting them
        spring_edges.append((v_idx, v_idx + 1))
    
    # Create the mesh
    spring_mesh.from_pydata(spring_verts, spring_edges, [])
    spring_mesh.update()
    
    # Make the springs visible with a material
    mat = bpy.data.materials.new(name="SewingSpringMaterial")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1, 0, 0, 1)  # Red color
    spring_obj.data.materials.append(mat)
    
    # Set display to show as wire
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics to both hood pieces
    setup_cloth_physics_for_sewing(obj1, obj2)

def setup_cloth_physics_for_sewing(obj1, obj2):
    """Add cloth physics modifiers to objects for sewing simulation"""
    
    # Add cloth modifier to first hood
    if "Cloth" not in [mod.name for mod in obj1.modifiers]:
        cloth_mod1 = obj1.modifiers.new(name="Cloth", type='CLOTH')
        cloth_mod1.settings.quality = 5
        cloth_mod1.settings.mass = 0.3
        cloth_mod1.settings.tension_stiffness = 15
        cloth_mod1.settings.compression_stiffness = 15
        cloth_mod1.settings.shear_stiffness = 5
        cloth_mod1.settings.bending_stiffness = 0.5
        # Enable sewing
        cloth_mod1.settings.use_sewing_springs = True
        cloth_mod1.settings.sewing_force_max = 0.5
    
    # Add cloth modifier to second hood
    if "Cloth" not in [mod.name for mod in obj2.modifiers]:
        cloth_mod2 = obj2.modifiers.new(name="Cloth", type='CLOTH')
        cloth_mod2.settings.quality = 5
        cloth_mod2.settings.mass = 0.3
        cloth_mod2.settings.tension_stiffness = 15
        cloth_mod2.settings.compression_stiffness = 15
        cloth_mod2.settings.shear_stiffness = 5
        cloth_mod2.settings.bending_stiffness = 0.5
        # Enable sewing
        cloth_mod2.settings.use_sewing_springs = True
        cloth_mod2.settings.sewing_force_max = 0.5

def setup_hood_center_seam():
    """Find the two hood pieces and mark their facing straight edges for sewing"""
    
    # Find hood pieces
    hood_1 = None
    hood_2 = None
    
    for obj in bpy.data.objects:
        if "_hood_" in obj.name.lower():
            if "hood_1" in obj.name.lower():
                hood_1 = obj
            elif "hood_2" in obj.name.lower():
                hood_2 = obj
    
    if not hood_1 or not hood_2:
        return
    
    
    # Find the straight vertical edges that face each other
    # These are the edges closest to Y=0 (center line where hoods meet)
    
    def find_center_facing_edge(hood_obj):
        """Find the straight vertical edge closest to Y=0"""
        if not hood_obj.data or not hood_obj.data.edges:
            return None
        
        mesh = hood_obj.data
        bpy.context.view_layer.objects.active = hood_obj
        hood_obj.select_set(True)
        
        # Switch to edit mode to work with edges
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(mesh)
        bm.edges.ensure_lookup_table()
        
        best_edge = None
        min_y_distance = float('inf')
        
        # Find edge closest to Y=0 that's also vertical (runs in Z direction)
        for edge in bm.edges:
            v1 = hood_obj.matrix_world @ edge.verts[0].co
            v2 = hood_obj.matrix_world @ edge.verts[1].co
            
            # Check if edge is mostly vertical (Z direction)
            edge_vector = v2 - v1
            z_component = abs(edge_vector.z)
            y_component = abs(edge_vector.y)
            x_component = abs(edge_vector.x)
            
            # Edge should be primarily vertical (Z) with minimal Y and X
            if z_component > 0.5 and y_component < 0.3 and x_component < 0.1:
                # Calculate average Y position (distance from center)
                avg_y = (v1.y + v2.y) / 2
                distance_from_center = abs(avg_y)
                
                if distance_from_center < min_y_distance:
                    min_y_distance = distance_from_center
                    best_edge = edge
                    
        
        # Mark the best edge as seam
        if best_edge:
            best_edge.seam = True
            bmesh.update_edit_mesh(mesh)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        return best_edge
    
    # Find and mark the center-facing edges on both hoods
    edge1 = find_center_facing_edge(hood_1)
    edge2 = find_center_facing_edge(hood_2) 
    
    if edge1 and edge2:
        # Create visual sewing connection
        create_sewing_springs_between_edges(hood_1, edge1, hood_2, edge2)
    

def setup_sleeve_cuff_seams():
    """Connect each sleeve cuff to its corresponding sleeve"""
    
    
    # Find all sleeves and cuffs
    sleeves = []
    cuffs = []
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "sleeve" in obj_name and "cuff" not in obj_name:
            sleeves.append(obj)
        elif "sleeve_cuff" in obj_name:
            cuffs.append(obj)
    
    
    # Match each cuff to its sleeve (by number: 1 to 1, 2 to 2)
    for cuff in cuffs:
        cuff_num = "1" if "1" in cuff.name else ("2" if "2" in cuff.name else "")
        
        # Find matching sleeve
        matching_sleeve = None
        for sleeve in sleeves:
            if cuff_num in sleeve.name:
                matching_sleeve = sleeve
                break
        
        if matching_sleeve:
            connect_sleeve_to_cuff(matching_sleeve, cuff)
        

def connect_sleeve_to_cuff(sleeve_obj, cuff_obj):
    """Connect the closest vertical edges between sleeve and cuff"""
    
    if not sleeve_obj.data or not cuff_obj.data:
        return
    
    # Find the closest vertical edges between sleeve and cuff
    sleeve_edge, cuff_edge = find_closest_vertical_edges(sleeve_obj, cuff_obj)
    
    if sleeve_edge and cuff_edge:
        create_sleeve_cuff_springs(sleeve_obj, sleeve_edge, cuff_obj, cuff_edge)

def find_closest_vertical_edges(sleeve_obj, cuff_obj):
    """Find the closest vertical edges between sleeve and cuff"""
    
    sleeve_mesh = sleeve_obj.data
    cuff_mesh = cuff_obj.data
    
    # Find all vertical edges in sleeve
    sleeve_vertical_edges = []
    for edge in sleeve_mesh.edges:
        v1 = sleeve_obj.matrix_world @ sleeve_mesh.vertices[edge.vertices[0]].co
        v2 = sleeve_obj.matrix_world @ sleeve_mesh.vertices[edge.vertices[1]].co
        
        edge_vector = v2 - v1
        z_component = abs(edge_vector.z)
        edge_length = edge_vector.length
        
        # Check if edge is vertical (runs in Z direction)
        if z_component > 0.3 and z_component / edge_length > 0.7:  # At least 70% vertical
            edge_center = (v1 + v2) / 2
            sleeve_vertical_edges.append((edge, edge_center, edge_length, v1, v2))
    
    # Find all vertical edges in cuff
    cuff_vertical_edges = []
    for edge in cuff_mesh.edges:
        v1 = cuff_obj.matrix_world @ cuff_mesh.vertices[edge.vertices[0]].co
        v2 = cuff_obj.matrix_world @ cuff_mesh.vertices[edge.vertices[1]].co
        
        edge_vector = v2 - v1
        z_component = abs(edge_vector.z)
        edge_length = edge_vector.length
        
        # Check if edge is vertical (runs in Z direction)
        if z_component > 0.3 and z_component / edge_length > 0.7:  # At least 70% vertical
            edge_center = (v1 + v2) / 2
            cuff_vertical_edges.append((edge, edge_center, edge_length, v1, v2))
    
    if not sleeve_vertical_edges or not cuff_vertical_edges:
        return None, None
    
    # Find the pair of edges that are closest to each other
    min_distance = float('inf')
    best_sleeve_edge = None
    best_cuff_edge = None
    
    for sleeve_edge in sleeve_vertical_edges:
        sleeve_center = sleeve_edge[1]
        
        for cuff_edge in cuff_vertical_edges:
            cuff_center = cuff_edge[1]
            
            # Calculate distance between edge centers
            distance = (sleeve_center - cuff_center).length
            
            if distance < min_distance:
                min_distance = distance
                best_sleeve_edge = sleeve_edge
                best_cuff_edge = cuff_edge
    
    if best_sleeve_edge and best_cuff_edge:
 
        # Return tuples with the data needed for spring creation
        return (best_sleeve_edge[0], 0, best_sleeve_edge[2], best_sleeve_edge[3], best_sleeve_edge[4]), \
               (best_cuff_edge[0], 0, best_cuff_edge[2], 0, best_cuff_edge[3], best_cuff_edge[4])
    
    return None, None

def create_sleeve_cuff_springs(sleeve_obj, sleeve_edge_data, cuff_obj, cuff_edge_data):
    """Create sewing springs between sleeve and cuff edges"""
    
    # Extract vertices from edge data
    sleeve_v1, sleeve_v2 = sleeve_edge_data[3], sleeve_edge_data[4]
    cuff_v1, cuff_v2 = cuff_edge_data[4], cuff_edge_data[5]
    
    # Check if edges need to be aligned to prevent crossing
    # Compare distances between endpoints to determine correct alignment
    dist_same = (sleeve_v1 - cuff_v1).length + (sleeve_v2 - cuff_v2).length
    dist_crossed = (sleeve_v1 - cuff_v2).length + (sleeve_v2 - cuff_v1).length
    
    # If crossed distance is shorter, flip the cuff edge direction
    if dist_crossed < dist_same:
        cuff_v1, cuff_v2 = cuff_v2, cuff_v1
    
    # Create spring mesh
    spring_mesh = bpy.data.meshes.new(f"SewingSpring_{sleeve_obj.name}_to_{cuff_obj.name}")
    spring_obj = bpy.data.objects.new(f"SewingSpring_{sleeve_obj.name}_to_{cuff_obj.name}", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    # Create spring connections
    num_springs = 5
    spring_verts = []
    spring_edges = []
    
    for i in range(num_springs):
        t = i / (num_springs - 1) if num_springs > 1 else 0.5
        
        # Interpolate along each edge
        p_sleeve = sleeve_v1.lerp(sleeve_v2, t)
        p_cuff = cuff_v1.lerp(cuff_v2, t)
        
        # Add vertices
        v_idx = len(spring_verts)
        spring_verts.append(p_sleeve)
        spring_verts.append(p_cuff)
        
        # Add edge
        spring_edges.append((v_idx, v_idx + 1))
    
    # Create the mesh
    spring_mesh.from_pydata(spring_verts, spring_edges, [])
    spring_mesh.update()
    
    # Add material (green for sleeve-cuff connections)
    mat = bpy.data.materials.new(name="SewingSpring_SleeveCuff_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0, 1, 0, 1)  # Green
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    setup_cloth_physics_for_sewing(sleeve_obj, cuff_obj)

def setup_front_back_panel_seams():
    """Connect front and back panels at their straight vertical side edges (excluding armholes)"""
    
    
    # Find front and back panels
    front_panel = None
    back_panel = None
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "front_panel" in obj_name:
            front_panel = obj
        elif "back_panel" in obj_name:
            back_panel = obj
    
    if not front_panel or not back_panel:
        return
    
    
    # Find and connect the straight vertical edges on both sides
    # Left side (negative Y)
    left_edges = find_panel_straight_side_edges(front_panel, back_panel, "left")
    if left_edges:
        front_left, back_left = left_edges
        create_panel_side_springs(front_panel, front_left, back_panel, back_left, "left")
    
    # Right side (positive Y)
    right_edges = find_panel_straight_side_edges(front_panel, back_panel, "right")
    if right_edges:
        front_right, back_right = right_edges
        create_panel_side_springs(front_panel, front_right, back_panel, back_right, "right")

def find_panel_straight_side_edges(front_panel, back_panel, side):
    """Find all vertical/semi-vertical edges on side until hitting armhole (perpendicular edge)"""
    
    # Determine which side we're looking for
    if side == "left":
        y_sign = -1
    else:
        y_sign = 1
    
    def find_all_vertical_edges_until_armhole(panel_obj, y_side):
        """Find the main vertical side edge, then trace upward until hitting armhole"""
        mesh = panel_obj.data
        
        
        # First, find the actual Y boundaries of the panel to remove hardcoded values
        all_world_verts = [panel_obj.matrix_world @ v.co for v in mesh.vertices]
        min_y = min(v.y for v in all_world_verts)
        max_y = max(v.y for v in all_world_verts)
        center_y = (min_y + max_y) / 2
        
        # Define dynamic thresholds based on actual panel geometry
        if y_side > 0:
            # Right side: look for edges on the right half
            y_threshold = center_y + (max_y - center_y) * 0.3  # 30% into right side
        else:
            # Left side: look for edges on the left half  
            y_threshold = center_y + (min_y - center_y) * 0.3  # 30% into left side
        
        # Step 1: Find the main vertical side edge (the longest vertical edge on this side)
        main_side_edge = None
        best_length = 0
        vertical_edges_found = 0
        
        for edge in mesh.edges:
            v1 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
            v2 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
            
            edge_vector = v2 - v1
            z_component = abs(edge_vector.z)
            edge_length = edge_vector.length
            avg_y = (v1.y + v2.y) / 2
            
            # Check if this is a vertical edge on the correct side
            if edge_length > 0:
                vertical_ratio = z_component / edge_length
                angle_from_vertical = math.degrees(math.acos(min(1.0, vertical_ratio)))
                
                # Must be vertical (within 30 degrees) and on correct side
                if angle_from_vertical < 30:
                    vertical_edges_found += 1
                    
                    if y_side > 0 and avg_y > y_threshold:  # Right side - dynamic threshold
                        if edge_length > best_length:
                            best_length = edge_length
                            main_side_edge = (edge, v1, v2, avg_y)
                    elif y_side < 0 and avg_y < y_threshold:  # Left side - dynamic threshold
                        if edge_length > best_length:
                            best_length = edge_length
                            main_side_edge = (edge, v1, v2, avg_y)
                    
        
        
        if not main_side_edge:
            return None
            
        
        # Step 2: Find the bottom vertex of this main edge
        edge, v1, v2, avg_y = main_side_edge
        bottom_vertex = v1 if v1.z < v2.z else v2
        top_vertex = v2 if v1.z < v2.z else v1
        
        
        # Step 3: Starting from bottom, collect connected vertical edges going upward
        vertical_edges = []
        current_top_z = top_vertex.z
        processed_edges = {edge}
        
        # Add the main edge first
        vertical_edges.append((edge, best_length, v1, v2, avg_y, (bottom_vertex.z + top_vertex.z) / 2))
        
        # Step 4: Look for connected edges going upward
        while True:
            found_next = False
            
            for next_edge in mesh.edges:
                if next_edge in processed_edges:
                    continue
                    
                nv1 = panel_obj.matrix_world @ mesh.vertices[next_edge.vertices[0]].co
                nv2 = panel_obj.matrix_world @ mesh.vertices[next_edge.vertices[1]].co
                
                # Check if this edge connects to the top of our current chain
                connects_to_top = (abs(nv1.z - current_top_z) < 0.1 or abs(nv2.z - current_top_z) < 0.1)
                
                if connects_to_top:
                    edge_vector = nv2 - nv1
                    z_component = abs(edge_vector.z)
                    edge_length = edge_vector.length
                    navg_y = (nv1.y + nv2.y) / 2
                    
                    if edge_length > 0:
                        vertical_ratio = z_component / edge_length
                        angle_from_vertical = math.degrees(math.acos(min(1.0, vertical_ratio)))
                        
                        # Check if it's still on the same side
                        on_same_side = (y_side > 0 and navg_y > y_threshold) or (y_side < 0 and navg_y < y_threshold)
                        
                        if angle_from_vertical > 35:  # Stop BEFORE armhole (more conservative)
                            found_next = False
                            break
                        elif angle_from_vertical < 30 and on_same_side:  # Must be truly vertical and on same side
                            vertical_edges.append((next_edge, edge_length, nv1, nv2, navg_y, (nv1.z + nv2.z) / 2))
                            current_top_z = max(nv1.z, nv2.z)
                            processed_edges.add(next_edge)
                            found_next = True
                            break
            
            if not found_next:
                break
        
        return vertical_edges if vertical_edges else None
    
    # Find edges on both panels
    front_edges = find_all_vertical_edges_until_armhole(front_panel, y_sign)
    back_edges = find_all_vertical_edges_until_armhole(back_panel, y_sign)
    
    if front_edges and back_edges:
        return front_edges, back_edges
    
    return None

def create_panel_side_springs(front_panel, front_edges_data, back_panel, back_edges_data, side):
    """Create sewing springs between multiple panel side edges with even spacing"""
    
    # Create spring mesh
    spring_mesh = bpy.data.meshes.new(f"SewingSpring_Panel_{side}")
    spring_obj = bpy.data.objects.new(f"SewingSpring_Panel_{side}", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    
    # Step 1: Build continuous paths for both front and back edges
    min_edges = min(len(front_edges_data), len(back_edges_data))
    
    # Sort edges by Z position (bottom to top)
    front_edges_sorted = sorted(front_edges_data[:min_edges], key=lambda edge: edge[5])  # Sort by avg_z
    back_edges_sorted = sorted(back_edges_data[:min_edges], key=lambda edge: edge[5])
    
    # Build continuous front path
    front_path = []
    for i, front_edge in enumerate(front_edges_sorted):
        front_v1, front_v2 = front_edge[2], front_edge[3]
        
        # Order vertices by Z (bottom to top)
        if front_v1.z < front_v2.z:
            front_path.append(front_v1)
            if i == len(front_edges_sorted) - 1:  # Last edge, add top vertex
                front_path.append(front_v2)
        else:
            front_path.append(front_v2)
            if i == len(front_edges_sorted) - 1:  # Last edge, add top vertex
                front_path.append(front_v1)
    
    # Build continuous back path
    back_path = []
    for i, back_edge in enumerate(back_edges_sorted):
        back_v1, back_v2 = back_edge[2], back_edge[3]
        
        # Order vertices by Z (bottom to top)
        if back_v1.z < back_v2.z:
            back_path.append(back_v1)
            if i == len(back_edges_sorted) - 1:  # Last edge, add top vertex
                back_path.append(back_v2)
        else:
            back_path.append(back_v2)
            if i == len(back_edges_sorted) - 1:  # Last edge, add top vertex
                back_path.append(back_v1)
    
    # Step 2: Calculate seam length and determine Z range
    min_z = min(min(v.z for v in front_path), min(v.z for v in back_path))
    max_z = max(max(v.z for v in front_path), max(v.z for v in back_path))
    total_z_range = max_z - min_z
    
    
    # Step 3: Place stitches evenly along Z axis
    desired_stitch_spacing = 0.05  # 5cm spacing
    num_stitches = max(3, int(total_z_range / desired_stitch_spacing))
    
    
    # Step 4: Find positions at specific Z levels
    for i in range(num_stitches):
        target_z = min_z + (i / (num_stitches - 1)) * total_z_range if num_stitches > 1 else (min_z + max_z) / 2
        
        # Find position along front path at this Z level
        front_pos = None
        for j in range(len(front_path) - 1):
            v1, v2 = front_path[j], front_path[j + 1]
            z1, z2 = v1.z, v2.z
            
            # Check if target_z is between these two vertices
            if (z1 <= target_z <= z2) or (z2 <= target_z <= z1):
                # Interpolate between the vertices
                if abs(z2 - z1) > 0.001:  # Avoid division by zero
                    t = (target_z - z1) / (z2 - z1)
                    front_pos = v1.lerp(v2, t)
                else:
                    front_pos = v1
                break
        
        # Find position along back path at this same Z level
        back_pos = None
        for j in range(len(back_path) - 1):
            v1, v2 = back_path[j], back_path[j + 1]
            z1, z2 = v1.z, v2.z
            
            # Check if target_z is between these two vertices
            if (z1 <= target_z <= z2) or (z2 <= target_z <= z1):
                # Interpolate between the vertices
                if abs(z2 - z1) > 0.001:  # Avoid division by zero
                    t = (target_z - z1) / (z2 - z1)
                    back_pos = v1.lerp(v2, t)
                else:
                    back_pos = v1
                break
        
        # Use fallback positions if exact Z match not found
        if front_pos is None:
            # Find closest Z position
            closest_front = min(front_path, key=lambda v: abs(v.z - target_z))
            front_pos = closest_front
        
        if back_pos is None:
            # Find closest Z position
            closest_back = min(back_path, key=lambda v: abs(v.z - target_z))
            back_pos = closest_back
        
        # Add stitch vertices and edge
        v_idx = len(all_spring_verts)
        all_spring_verts.append(front_pos)
        all_spring_verts.append(back_pos)
        all_spring_edges.append((v_idx, v_idx + 1))
        
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (blue for panel connections)
    mat = bpy.data.materials.new(name=f"SewingSpring_Panel_{side}_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0, 0, 1, 1)  # Blue
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    setup_cloth_physics_for_sewing(front_panel, back_panel)

def setup_waist_band_seam():
    """Connect waist band to bottom edges of front and back panels"""
    
    
    # Find waist band, front panel, and back panel
    waist_band = None
    front_panel = None
    back_panel = None
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "waist_band" in obj_name or "waistband" in obj_name:
            waist_band = obj
        elif "front_panel" in obj_name:
            front_panel = obj
        elif "back_panel" in obj_name:
            back_panel = obj
    
    if not waist_band or not front_panel or not back_panel:
        return
    
    
    # Find waist band's SINGLE longest top horizontal edge (highest Z, runs along Y)
    waist_band_edge = find_longest_horizontal_edge(waist_band, "top")
    if not waist_band_edge:
        return
    
    # Find ALL front panel's bottom horizontal edges (lowest Z, runs along Y)
    front_bottom_edges = find_all_horizontal_edges(front_panel, "bottom")
    if not front_bottom_edges:
        return
    
    # Find ALL back panel's bottom horizontal edges (lowest Z, runs along Y)
    back_bottom_edges = find_all_horizontal_edges(back_panel, "bottom")
    if not back_bottom_edges:
        return
    
    # Create continuous seam connecting waist band to both panels
    create_waist_band_springs(waist_band, waist_band_edge, front_panel, front_bottom_edges, back_panel, back_bottom_edges)

def find_longest_horizontal_edge(obj, position="top"):
    """Find the single longest horizontal edge at top or bottom of object"""
    mesh = obj.data
    
    horizontal_edges = []
    target_z = None
    
    # Get all vertices in world coordinates
    world_verts = [obj.matrix_world @ v.co for v in mesh.vertices]
    
    if position == "top":
        target_z = max(v.z for v in world_verts)
    else:  # bottom
        target_z = min(v.z for v in world_verts)
    
    
    for edge in mesh.edges:
        v1 = obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
        v2 = obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
        
        edge_vector = v2 - v1
        edge_length = edge_vector.length
        avg_z = (v1.z + v2.z) / 2
        
        # Check if this edge is at the target Z level (within tolerance)
        if abs(avg_z - target_z) < 0.05 and edge_length > 0:
            # Check if it's horizontal (runs along Y axis)
            y_component = abs(edge_vector.y)
            horizontal_ratio = y_component / edge_length
            angle_from_horizontal = math.degrees(math.acos(min(1.0, horizontal_ratio)))
            
            if angle_from_horizontal < 30:  # Within 30 degrees of horizontal
                horizontal_edges.append((edge, v1, v2, edge_length, avg_z))
    
    if horizontal_edges:
        # Return only the longest edge
        longest_edge = max(horizontal_edges, key=lambda edge_data: edge_data[3])
        return longest_edge
    else:
        return None

def find_all_horizontal_edges(obj, position="bottom"):
    """Find ALL horizontal edges at bottom of object (for mirrored panels)"""
    mesh = obj.data
    
    horizontal_edges = []
    target_z = None
    
    # Get all vertices in world coordinates
    world_verts = [obj.matrix_world @ v.co for v in mesh.vertices]
    
    if position == "top":
        target_z = max(v.z for v in world_verts)
    else:  # bottom
        target_z = min(v.z for v in world_verts)
    
    
    for edge in mesh.edges:
        v1 = obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
        v2 = obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
        
        edge_vector = v2 - v1
        edge_length = edge_vector.length
        avg_z = (v1.z + v2.z) / 2
        
        # Check if this edge is at the target Z level (within tolerance)
        if abs(avg_z - target_z) < 0.05 and edge_length > 0:
            # Check if it's horizontal (runs along Y axis)
            y_component = abs(edge_vector.y)
            horizontal_ratio = y_component / edge_length
            angle_from_horizontal = math.degrees(math.acos(min(1.0, horizontal_ratio)))
            
            if angle_from_horizontal < 30:  # Within 30 degrees of horizontal
                horizontal_edges.append((edge, v1, v2, edge_length, avg_z))
    
    if horizontal_edges:
        # Sort edges by Y position to create continuous path
        horizontal_edges.sort(key=lambda edge_data: min(edge_data[1].y, edge_data[2].y))
        return horizontal_edges
    else:
        return None

def create_waist_band_springs(waist_band, wb_edge_data, front_panel, front_edges_data, back_panel, back_edges_data):
    """Create continuous seam connecting waist band to front and back panels"""
    
    # Create spring mesh
    spring_mesh = bpy.data.meshes.new("SewingSpring_WaistBand")
    spring_obj = bpy.data.objects.new("SewingSpring_WaistBand", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    
    # Extract waist band edge vertices (single longest edge)
    wb_edge, wb_v1, wb_v2, wb_length, wb_z = wb_edge_data
    
    # Order waist band vertices by Y (left to right)
    if wb_v1.y > wb_v2.y:
        wb_v1, wb_v2 = wb_v2, wb_v1
    
    # Build continuous path from all front panel bottom edges
    front_vertices = []
    for edge_data in front_edges_data:
        edge, v1, v2, length, z = edge_data
        front_vertices.append(v1)
        front_vertices.append(v2)
    
    # Remove duplicates and sort
    front_path = []
    for v in front_vertices:
        is_new = True
        for existing in front_path:
            if (existing - v).length < 0.001:
                is_new = False
                break
        if is_new:
            front_path.append(v)
    front_path.sort(key=lambda v: v.y)
    
    # Build continuous path from all back panel bottom edges
    back_vertices = []
    for edge_data in back_edges_data:
        edge, v1, v2, length, z = edge_data
        back_vertices.append(v1)
        back_vertices.append(v2)
    
    # Remove duplicates and sort
    back_path = []
    for v in back_vertices:
        is_new = True
        for existing in back_path:
            if (existing - v).length < 0.001:
                is_new = False
                break
        if is_new:
            back_path.append(v)
    back_path.sort(key=lambda v: v.y)
    
    # Get Y ranges for front and back panels
    front_y_min = min(v.y for v in front_path)
    front_y_max = max(v.y for v in front_path)
    back_y_min = min(v.y for v in back_path)
    back_y_max = max(v.y for v in back_path)
    

    # Create stitches for FIRST HALF of waist band to ENTIRE front panel
    num_stitches_per_panel = 10  # Even spacing
    
    
    # FIRST HALF of waist band (0 to 0.5) connects to ENTIRE front panel
    for i in range(num_stitches_per_panel):
        # Position on waist band (first half)
        wb_t = (i / (num_stitches_per_panel - 1)) * 0.5  # 0 to 0.5
        wb_pos = wb_v1.lerp(wb_v2, wb_t)
        
        # Position on front panel (entire width)
        front_t = i / (num_stitches_per_panel - 1)  # 0 to 1
        
        # Interpolate along front panel path
        if len(front_path) > 1:
            total_length = sum((front_path[j+1] - front_path[j]).length for j in range(len(front_path)-1))
            target_length = front_t * total_length
            
            current_length = 0
            panel_pos = front_path[0]
            for j in range(len(front_path) - 1):
                segment_length = (front_path[j+1] - front_path[j]).length
                if current_length + segment_length >= target_length:
                    local_t = (target_length - current_length) / segment_length if segment_length > 0 else 0
                    panel_pos = front_path[j].lerp(front_path[j+1], local_t)
                    break
                current_length += segment_length
        else:
            panel_pos = front_path[0]
        
        # Add stitch
        v_idx = len(all_spring_verts)
        all_spring_verts.append(wb_pos)
        all_spring_verts.append(panel_pos)
        all_spring_edges.append((v_idx, v_idx + 1))
    
    # SECOND HALF of waist band (0.5 to 1.0) connects to ENTIRE back panel
    for i in range(num_stitches_per_panel):
        # Position on waist band (second half)
        wb_t = 0.5 + (i / (num_stitches_per_panel - 1)) * 0.5  # 0.5 to 1.0
        wb_pos = wb_v1.lerp(wb_v2, wb_t)
        
        # Position on back panel (entire width)
        back_t = i / (num_stitches_per_panel - 1)  # 0 to 1
        
        # Interpolate along back panel path
        if len(back_path) > 1:
            total_length = sum((back_path[j+1] - back_path[j]).length for j in range(len(back_path)-1))
            target_length = back_t * total_length
            
            current_length = 0
            panel_pos = back_path[0]
            for j in range(len(back_path) - 1):
                segment_length = (back_path[j+1] - back_path[j]).length
                if current_length + segment_length >= target_length:
                    local_t = (target_length - current_length) / segment_length if segment_length > 0 else 0
                    panel_pos = back_path[j].lerp(back_path[j+1], local_t)
                    break
                current_length += segment_length
        else:
            panel_pos = back_path[0]
        
        # Add stitch
        v_idx = len(all_spring_verts)
        all_spring_verts.append(wb_pos)
        all_spring_verts.append(panel_pos)
        all_spring_edges.append((v_idx, v_idx + 1))
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (orange for waist band)
    mat = bpy.data.materials.new(name="SewingSpring_WaistBand_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1, 0.5, 0, 1)  # Orange
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    setup_cloth_physics_for_sewing(waist_band, front_panel)
    setup_cloth_physics_for_sewing(waist_band, back_panel)

def setup_pocket_seam():
    """Connect pocket to front panel at its position"""
    
    
    # Find pocket and front panel
    pocket = None
    front_panel = None
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "pocket" in obj_name:
            pocket = obj
        elif "front_panel" in obj_name:
            front_panel = obj
    
    if not pocket or not front_panel:
        return
    
    
    # Find pocket's top and bottom horizontal edges
    pocket_top_edges = find_all_horizontal_edges(pocket, "top")
    pocket_bottom_edges = find_all_horizontal_edges(pocket, "bottom")
    
    if not pocket_top_edges:
        return
    
    if not pocket_bottom_edges:
        return
    
    
    # Create springs connecting pocket edges to front panel
    create_pocket_springs(pocket, pocket_top_edges, pocket_bottom_edges, front_panel)

def create_pocket_springs(pocket, top_edges, bottom_edges, front_panel):
    """Create sewing springs connecting pocket edges to front panel"""
    
    # Create spring mesh
    spring_mesh = bpy.data.meshes.new("SewingSpring_Pocket")
    spring_obj = bpy.data.objects.new("SewingSpring_Pocket", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    
    # Process top edges
    for edge_data in top_edges:
        edge, v1, v2, length, z = edge_data
        
        # Order vertices by Y
        if v1.y > v2.y:
            v1, v2 = v2, v1
        
        # Create stitches along this edge
        num_stitches = max(3, int(length / 0.05))  # 5cm spacing
        
        for i in range(num_stitches):
            t = i / (num_stitches - 1) if num_stitches > 1 else 0.5
            
            # Position on pocket edge
            pocket_pos = v1.lerp(v2, t)
            
            # Find corresponding position on front panel (same X, Y, but on panel surface)
            panel_pos = Vector((front_panel.location.x, pocket_pos.y, pocket_pos.z))
            
            # Add stitch
            v_idx = len(all_spring_verts)
            all_spring_verts.append(pocket_pos)
            all_spring_verts.append(panel_pos)
            all_spring_edges.append((v_idx, v_idx + 1))
    
    # Process bottom edges
    for edge_data in bottom_edges:
        edge, v1, v2, length, z = edge_data
        
        # Order vertices by Y
        if v1.y > v2.y:
            v1, v2 = v2, v1
        
        # Create stitches along this edge
        num_stitches = max(3, int(length / 0.05))  # 5cm spacing
        
        for i in range(num_stitches):
            t = i / (num_stitches - 1) if num_stitches > 1 else 0.5
            
            # Position on pocket edge
            pocket_pos = v1.lerp(v2, t)
            
            # Find corresponding position on front panel (same X, Y, but on panel surface)
            panel_pos = Vector((front_panel.location.x, pocket_pos.y, pocket_pos.z))
            
            # Add stitch
            v_idx = len(all_spring_verts)
            all_spring_verts.append(pocket_pos)
            all_spring_verts.append(panel_pos)
            all_spring_edges.append((v_idx, v_idx + 1))
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (purple for pocket)
    mat = bpy.data.materials.new(name="SewingSpring_Pocket_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.5, 0, 1, 1)  # Purple
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    setup_cloth_physics_for_sewing(pocket, front_panel)

def setup_neck_binding_seam():
    """Connect neck binding to neckline curves of front and back panels"""
    
    
    # Find neck binding, front panel, and back panel
    neck_binding = None
    front_panel = None
    back_panel = None
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "neck" in obj_name and "bind" in obj_name:
            neck_binding = obj
        elif "front_panel" in obj_name:
            front_panel = obj
        elif "back_panel" in obj_name:
            back_panel = obj
    
    if not neck_binding or not front_panel or not back_panel:
        return
    
    
    # Find ALL neck binding bottom horizontal edges
    neck_binding_edges = find_all_horizontal_edges(neck_binding, "bottom")
    if not neck_binding_edges:
        return
    
   
    
    # Find neckline curves on panels
    front_neckline = find_neckline_curve(front_panel)
    if not front_neckline:
        return
    
    back_neckline = find_neckline_curve(back_panel)
    if not back_neckline:
        return
    
    # Create neck binding springs
    create_neck_binding_springs(neck_binding, neck_binding_edges, front_panel, front_neckline, back_panel, back_neckline)

def find_neckline_curve(panel_obj):
    """Find the curved neckline edges between shoulder drop-offs"""
    
    mesh = panel_obj.data
    world_verts = [panel_obj.matrix_world @ v.co for v in mesh.vertices]
    
    # Find approximate top Z (but not absolute max, as shoulders might be higher)
    max_z = max(v.z for v in world_verts)
    
    # Different threshold for front vs back panel
    is_front = "front" in panel_obj.name.lower()
    if is_front:
        # Front panels often have much deeper necklines (V-necks, scoop necks, etc)
        neckline_z_threshold = max_z - 0.40  # Look within 40cm of top for front (much deeper)
    else:
        neckline_z_threshold = max_z - 0.15  # Look within 15cm of top for back
    
    
    # Find all edges near the top
    top_edges = []
    for edge in mesh.edges:
        v1 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
        v2 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
        avg_z = (v1.z + v2.z) / 2
        
        if avg_z > neckline_z_threshold:
            edge_vector = v2 - v1
            edge_length = edge_vector.length
            if edge_length > 0:
                # Calculate angle from horizontal
                y_component = abs(edge_vector.y)
                horizontal_ratio = y_component / edge_length
                angle_from_horizontal = math.degrees(math.acos(min(1.0, horizontal_ratio)))
                
                top_edges.append({
                    'edge': edge,
                    'v1': v1,
                    'v2': v2,
                    'avg_z': avg_z,
                    'avg_y': (v1.y + v2.y) / 2,
                    'angle': angle_from_horizontal,
                    'length': edge_length
                })
    
    # Sort edges by Y position
    top_edges.sort(key=lambda e: e['avg_y'])
    
    # Find shoulder edges (relatively straight, diagonal)
    shoulder_threshold = 45  # Degrees
    potential_shoulders = [e for e in top_edges if 15 < e['angle'] < shoulder_threshold]
    
    if len(potential_shoulders) < 2:
        return None
    
    # Find leftmost and rightmost shoulders
    left_shoulder = min(potential_shoulders, key=lambda e: e['avg_y'])
    right_shoulder = max(potential_shoulders, key=lambda e: e['avg_y'])
    
    
    # Find edges between shoulders (the neckline)
    neckline_edges = []
    
    # For front panel, use the same logic as back panel (which works correctly)
    if is_front:
        # Front neckline: use EXACT same logic as back panel
        for edge_data in top_edges:
            # Must be between shoulders (EXCLUDE shoulders themselves)
            if left_shoulder['avg_y'] < edge_data['avg_y'] < right_shoulder['avg_y']:
                neckline_edges.append((
                    edge_data['edge'],
                    edge_data['v1'],
                    edge_data['v2'],
                    edge_data['length'],
                    edge_data['avg_z']
                ))
    else:
        # Back neckline: original logic works well
        for edge_data in top_edges:
            if left_shoulder['avg_y'] < edge_data['avg_y'] < right_shoulder['avg_y']:
                neckline_edges.append((
                    edge_data['edge'],
                    edge_data['v1'],
                    edge_data['v2'],
                    edge_data['length'],
                    edge_data['avg_z']
                ))
    
    if neckline_edges:
        
        # For front panel, make sure we have enough edges for a complete curve
        if is_front and len(neckline_edges) < 5:
            
            # Expand to include more edges near the neckline
            for edge_data in top_edges:
                already_included = any(
                    (edge_data['v1'] - ne[1]).length < 0.001 and (edge_data['v2'] - ne[2]).length < 0.001
                    for ne in neckline_edges
                )
                if not already_included:
                    # Include if it's within shoulder range and has some angle
                    if left_shoulder['avg_y'] - 0.1 <= edge_data['avg_y'] <= right_shoulder['avg_y'] + 0.1:
                        if edge_data['angle'] > 5:  # Very permissive
                            neckline_edges.append((
                                edge_data['edge'],
                                edge_data['v1'],
                                edge_data['v2'],
                                edge_data['length'],
                                edge_data['avg_z']
                            ))
            
        
        return neckline_edges
    else:
        # Fallback: for front panel, be very inclusive
        if is_front:
            neckline_edges = []
            for edge_data in top_edges:
                # Very permissive - just avoid perfectly horizontal edges
                if edge_data['angle'] > 5:
                    neckline_edges.append((
                        edge_data['edge'],
                        edge_data['v1'],
                        edge_data['v2'],
                        edge_data['length'],
                        edge_data['avg_z']
                    ))
            
            if neckline_edges:
                return neckline_edges
        else:
            # Original fallback for back panel
            curved_edges = [e for e in top_edges if e['angle'] > 45]
            if curved_edges:
                center_y = sum(e['avg_y'] for e in curved_edges) / len(curved_edges)
                neckline_edges = []
                for edge_data in curved_edges:
                    if abs(edge_data['avg_y'] - center_y) < 0.3:
                        neckline_edges.append((
                            edge_data['edge'],
                            edge_data['v1'],
                            edge_data['v2'],
                            edge_data['length'],
                            edge_data['avg_z']
                        ))
                return neckline_edges if neckline_edges else None
    
    return None

def create_neck_binding_springs(neck_binding, nb_edges_data, front_panel, front_neckline, back_panel, back_neckline):
    """Create springs connecting neck binding to panel necklines"""
    
    # Create spring mesh
    spring_mesh = bpy.data.meshes.new("SewingSpring_NeckBinding")
    spring_obj = bpy.data.objects.new("SewingSpring_NeckBinding", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    
    # Build complete neck binding path from ALL edges
    nb_vertices = []
    for edge_data in nb_edges_data:
        edge, v1, v2, length, z = edge_data
        nb_vertices.append(v1)
        nb_vertices.append(v2)
    
    # Remove duplicates and sort by Y to create continuous path
    unique_nb = []
    for v in nb_vertices:
        is_new = True
        for existing in unique_nb:
            if (existing - v).length < 0.001:
                is_new = False
                break
        if is_new:
            unique_nb.append(v)
    unique_nb.sort(key=lambda v: v.y)
    
    # Get the full neck binding Y range
    nb_y_min = min(v.y for v in unique_nb)
    nb_y_max = max(v.y for v in unique_nb)
    nb_total_length = nb_y_max - nb_y_min
    
    
    # Build front neckline path - need to create a connected curve
    front_edges = []
    for edge_data in front_neckline:
        edge, v1, v2, length, z = edge_data
        front_edges.append((v1, v2))
    
    # Build connected path from edges
    unique_front = []
    if front_edges:
        # Start from leftmost edge
        all_verts = []
        for v1, v2 in front_edges:
            all_verts.extend([v1, v2])
        
        # Find leftmost vertex as starting point
        start_vert = min(all_verts, key=lambda v: v.y)
        unique_front = [start_vert]
        used_edges = []
        
        # Build connected path
        current = start_vert
        for _ in range(len(front_edges)):
            found_next = False
            for i, (v1, v2) in enumerate(front_edges):
                if i in used_edges:
                    continue
                
                # Check if this edge connects to current vertex
                if (current - v1).length < 0.001:
                    if not any((v2 - existing).length < 0.001 for existing in unique_front):
                        unique_front.append(v2)
                        current = v2
                        used_edges.append(i)
                        found_next = True
                        break
                elif (current - v2).length < 0.001:
                    if not any((v1 - existing).length < 0.001 for existing in unique_front):
                        unique_front.append(v1)
                        current = v1
                        used_edges.append(i)
                        found_next = True
                        break
            
            if not found_next:
                break
    
    # If path building failed, fall back to Y-sorting
    if len(unique_front) < 2:
        front_path = []
        for v1, v2 in front_edges:
            front_path.extend([v1, v2])
        unique_front = []
        for v in front_path:
            is_new = True
            for existing in unique_front:
                if (existing - v).length < 0.001:
                    is_new = False
                    break
            if is_new:
                unique_front.append(v)
        unique_front.sort(key=lambda v: v.y)
    
    # Build back neckline path
    back_path = []
    for edge_data in back_neckline:
        edge, v1, v2, length, z = edge_data
        back_path.append(v1)
        back_path.append(v2)
    
    # Remove duplicates and sort
    unique_back = []
    for v in back_path:
        is_new = True
        for existing in unique_back:
            if (existing - v).length < 0.001:
                is_new = False
                break
        if is_new:
            unique_back.append(v)
    unique_back.sort(key=lambda v: v.y)
    
    # Calculate how many stitches to create based on neck binding length
    half_nb_length = nb_total_length / 2
    stitch_spacing = 0.05  # 5cm spacing
    num_stitches_per_half = max(5, int(half_nb_length / stitch_spacing))
    
    
    # First FULL half of neck binding to ENTIRE front neckline
    for i in range(num_stitches_per_half):
        # Position on neck binding - spread across FULL first half
        nb_t = (i / (num_stitches_per_half - 1) if num_stitches_per_half > 1 else 0) * 0.5  # 0 to 0.5
        
        # Interpolate along the complete neck binding path
        if len(unique_nb) > 1:
            path_length = sum((unique_nb[j+1] - unique_nb[j]).length for j in range(len(unique_nb)-1))
            target_length = nb_t * path_length
            
            current_length = 0
            nb_pos = unique_nb[0]
            for j in range(len(unique_nb) - 1):
                segment_length = (unique_nb[j+1] - unique_nb[j]).length
                if current_length + segment_length >= target_length:
                    local_t = (target_length - current_length) / segment_length if segment_length > 0 else 0
                    nb_pos = unique_nb[j].lerp(unique_nb[j+1], local_t)
                    break
                current_length += segment_length
        else:
            nb_pos = unique_nb[0] if unique_nb else Vector((0, 0, 0))
        
        # Position on front neckline - spread across ENTIRE front neckline
        if len(unique_front) > 1:
            front_t = i / (num_stitches_per_half - 1)  # 0 to 1 across full front neckline
            total_length = sum((unique_front[j+1] - unique_front[j]).length for j in range(len(unique_front)-1))
            target_length = front_t * total_length
            
            current_length = 0
            panel_pos = unique_front[0]
            for j in range(len(unique_front) - 1):
                segment_length = (unique_front[j+1] - unique_front[j]).length
                if current_length + segment_length >= target_length:
                    local_t = (target_length - current_length) / segment_length if segment_length > 0 else 0
                    panel_pos = unique_front[j].lerp(unique_front[j+1], local_t)
                    break
                current_length += segment_length
        else:
            panel_pos = unique_front[0] if unique_front else nb_pos
        
        # Add stitch
        v_idx = len(all_spring_verts)
        all_spring_verts.append(nb_pos)
        all_spring_verts.append(panel_pos)
        all_spring_edges.append((v_idx, v_idx + 1))
        

    
    # Second FULL half of neck binding to ENTIRE back neckline
    for i in range(num_stitches_per_half):
        # Position on neck binding - spread across FULL second half
        nb_t = 0.5 + (i / (num_stitches_per_half - 1) if num_stitches_per_half > 1 else 0) * 0.5  # 0.5 to 1.0
        
        # Interpolate along the complete neck binding path
        if len(unique_nb) > 1:
            path_length = sum((unique_nb[j+1] - unique_nb[j]).length for j in range(len(unique_nb)-1))
            target_length = nb_t * path_length
            
            current_length = 0
            nb_pos = unique_nb[0]
            for j in range(len(unique_nb) - 1):
                segment_length = (unique_nb[j+1] - unique_nb[j]).length
                if current_length + segment_length >= target_length:
                    local_t = (target_length - current_length) / segment_length if segment_length > 0 else 0
                    nb_pos = unique_nb[j].lerp(unique_nb[j+1], local_t)
                    break
                current_length += segment_length
        else:
            nb_pos = unique_nb[-1] if unique_nb else Vector((0, 0, 0))
        
        # Position on back neckline - spread across ENTIRE back neckline
        if len(unique_back) > 1:
            back_t = i / (num_stitches_per_half - 1) if num_stitches_per_half > 1 else 0.5  # 0 to 1 across full back neckline
            total_length = sum((unique_back[j+1] - unique_back[j]).length for j in range(len(unique_back)-1))
            target_length = back_t * total_length
            
            current_length = 0
            panel_pos = unique_back[0]
            for j in range(len(unique_back) - 1):
                segment_length = (unique_back[j+1] - unique_back[j]).length
                if current_length + segment_length >= target_length:
                    local_t = (target_length - current_length) / segment_length if segment_length > 0 else 0
                    panel_pos = unique_back[j].lerp(unique_back[j+1], local_t)
                    break
                current_length += segment_length
        else:
            panel_pos = unique_back[0] if unique_back else nb_pos
        
        v_idx = len(all_spring_verts)
        all_spring_verts.append(nb_pos)
        all_spring_verts.append(panel_pos)
        all_spring_edges.append((v_idx, v_idx + 1))
        

    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (cyan for neck binding)
    mat = bpy.data.materials.new(name="SewingSpring_NeckBinding_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0, 1, 1, 1)  # Cyan
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    setup_cloth_physics_for_sewing(neck_binding, front_panel)
    setup_cloth_physics_for_sewing(neck_binding, back_panel)

def setup_shoulder_seams():
    """Connect shoulder edges of front and back panels"""
    
    
    # Find front and back panels
    front_panel = None
    back_panel = None
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "front_panel" in obj_name:
            front_panel = obj
        elif "back_panel" in obj_name:
            back_panel = obj
    
    if not front_panel or not back_panel:
        return
    
    
    # Find shoulder edges on both panels
    front_shoulders = find_shoulder_edges(front_panel)
    back_shoulders = find_shoulder_edges(back_panel)
    
    if not front_shoulders or not back_shoulders:
        return
    
    front_left, front_right = front_shoulders
    back_left, back_right = back_shoulders
    
    
    # Create shoulder seams
    create_shoulder_springs(front_panel, front_left, back_panel, back_left, "left")
    create_shoulder_springs(front_panel, front_right, back_panel, back_right, "right")

def find_shoulder_edges(panel_obj):
    """Find the left and right shoulder edges (the diagonal edges we excluded from neckline)"""
    
    mesh = panel_obj.data
    world_verts = [panel_obj.matrix_world @ v.co for v in mesh.vertices]
    
    # Find approximate top Z
    max_z = max(v.z for v in world_verts)
    shoulder_z_threshold = max_z - 0.15  # Look within 15cm of top
    
    
    # Find all edges near the top
    top_edges = []
    for edge in mesh.edges:
        v1 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
        v2 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
        avg_z = (v1.z + v2.z) / 2
        
        if avg_z > shoulder_z_threshold:
            edge_vector = v2 - v1
            edge_length = edge_vector.length
            if edge_length > 0:
                # Calculate angle from horizontal
                y_component = abs(edge_vector.y)
                horizontal_ratio = y_component / edge_length
                angle_from_horizontal = math.degrees(math.acos(min(1.0, horizontal_ratio)))
                
                top_edges.append({
                    'edge': edge,
                    'v1': v1,
                    'v2': v2,
                    'avg_z': avg_z,
                    'avg_y': (v1.y + v2.y) / 2,
                    'angle': angle_from_horizontal,
                    'length': edge_length
                })
    
    # Find shoulder edges (diagonal, relatively straight - what we excluded from neckline)
    shoulder_threshold = 45  # Degrees
    potential_shoulders = [e for e in top_edges if 15 < e['angle'] < shoulder_threshold]
    
    if len(potential_shoulders) < 2:
        return None
    
    # Find leftmost and rightmost shoulders
    left_shoulder = min(potential_shoulders, key=lambda e: e['avg_y'])
    right_shoulder = max(potential_shoulders, key=lambda e: e['avg_y'])
    
    
    # Convert to edge data format
    left_edge_data = (
        left_shoulder['edge'],
        left_shoulder['v1'],
        left_shoulder['v2'],
        left_shoulder['length'],
        left_shoulder['avg_z']
    )
    
    right_edge_data = (
        right_shoulder['edge'],
        right_shoulder['v1'],
        right_shoulder['v2'],
        right_shoulder['length'],
        right_shoulder['avg_z']
    )
    
    return (left_edge_data, right_edge_data)

def create_shoulder_springs(front_panel, front_edge_data, back_panel, back_edge_data, side):
    """Create sewing springs between shoulder edges"""
    
    # Create spring mesh
    spring_mesh = bpy.data.meshes.new(f"SewingSpring_Shoulder_{side}")
    spring_obj = bpy.data.objects.new(f"SewingSpring_Shoulder_{side}", spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    
    # Extract edge vertices
    front_edge, front_v1, front_v2, front_length, front_z = front_edge_data
    back_edge, back_v1, back_v2, back_length, back_z = back_edge_data
    
    # Order vertices consistently (by Y position)
    if front_v1.y > front_v2.y:
        front_v1, front_v2 = front_v2, front_v1
    if back_v1.y > back_v2.y:
        back_v1, back_v2 = back_v2, back_v1
    
    # Check alignment to prevent crossing
    dist_same = (front_v1 - back_v1).length + (front_v2 - back_v2).length
    dist_crossed = (front_v1 - back_v2).length + (front_v2 - back_v1).length
    
    if dist_crossed < dist_same:
        back_v1, back_v2 = back_v2, back_v1
    
    # Create stitches along shoulder edge
    num_stitches = max(3, int(min(front_length, back_length) / 0.05))  # 5cm spacing
    
    
    for i in range(num_stitches):
        t = i / (num_stitches - 1) if num_stitches > 1 else 0.5
        
        # Position on front shoulder
        front_pos = front_v1.lerp(front_v2, t)
        
        # Position on back shoulder
        back_pos = back_v1.lerp(back_v2, t)
        
        # Add stitch
        v_idx = len(all_spring_verts)
        all_spring_verts.append(front_pos)
        all_spring_verts.append(back_pos)
        all_spring_edges.append((v_idx, v_idx + 1))
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (yellow for shoulders)
    mat = bpy.data.materials.new(name=f"SewingSpring_Shoulder_{side}_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1, 1, 0, 1)  # Yellow
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    setup_cloth_physics_for_sewing(front_panel, back_panel)

def get_front_panel_edges():
    for obj in bpy.data.objects:
        if "front_panel" in obj.name.lower():
            if obj.data and obj.data.vertices:
                verts = obj.data.vertices
                world_verts = [obj.matrix_world @ v.co for v in verts]
                min_y = min(v.y for v in world_verts)
                max_y = max(v.y for v in world_verts)
                return (min_y, max_y)
    
    return None

def setup_sleeve_horizontal_seams():
    """Connect top and bottom horizontal edges of each sleeve"""
    
    sleeve_objects = []
    for obj in bpy.data.objects:
        if "_sleeve_" in obj.name.lower() and "_sleeve_cuff_" not in obj.name.lower() and obj.data and obj.data.vertices and not obj.name.startswith("SewingSpring"):
            sleeve_objects.append(obj)
    
    if not sleeve_objects:
        return
    
    for sleeve_obj in sleeve_objects:
        
        top_edges, bottom_edges = find_sleeve_horizontal_edges(sleeve_obj)
        
        if top_edges and bottom_edges:
            create_sleeve_horizontal_springs(sleeve_obj, top_edges, bottom_edges)
        

def find_sleeve_horizontal_edges(sleeve_obj):
    """Find top and bottom horizontal edges that run along Y direction - same as cuff but with Z tolerance for curves"""
    
    if not sleeve_obj.data or not sleeve_obj.data.edges:
        return None, None
    
    mesh = sleeve_obj.data
    bpy.context.view_layer.objects.active = sleeve_obj
    sleeve_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bm.edges.ensure_lookup_table()
    
    horizontal_edges = []
 
    for edge in bm.edges:
        v1 = sleeve_obj.matrix_world @ edge.verts[0].co
        v2 = sleeve_obj.matrix_world @ edge.verts[1].co
        
        edge_vector = v2 - v1
        y_component = abs(edge_vector.y)
        z_component = abs(edge_vector.z)
        x_component = abs(edge_vector.x)
        avg_z = (v1.z + v2.z) / 2
        
        # More relaxed for sleeves: Y should be dominant but allow more Z variation for curves
        if y_component > 0.1 and y_component > z_component * 0.7 and y_component > x_component:
            edge_data = {
                'v1_world': v1,
                'v2_world': v2,
                'avg_z': avg_z,
                'length': edge_vector.length
            }
            horizontal_edges.append(edge_data)
        
    
    total_edges = len(bm.edges)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    
    if not horizontal_edges:
        return None, None
    
    # Sort by Z position to find top and bottom
    horizontal_edges.sort(key=lambda e: e['avg_z'])
    
    # For curved sleeves with Z-dipping, we need to group by Y position, not just Z level
    if len(horizontal_edges) >= 2:
        
        # Group edges by Y overlap regions
        def get_y_range(edge):
            y1, y2 = edge['v1_world'].y, edge['v2_world'].y
            return min(y1, y2), max(y1, y2)
        
        # Find overall Y span
        all_y_coords = []
        for edge in horizontal_edges:
            y_min, y_max = get_y_range(edge)
            all_y_coords.extend([y_min, y_max])
        
        overall_y_min = min(all_y_coords)
        overall_y_max = max(all_y_coords)
        
        
        # Separate into top and bottom based on Z at each Y position
        # Find Z range first
        all_z_coords = [edge['avg_z'] for edge in horizontal_edges]
        z_mid = (min(all_z_coords) + max(all_z_coords)) / 2
        
        top_edges = [e for e in horizontal_edges if e['avg_z'] >= z_mid]
        bottom_edges = [e for e in horizontal_edges if e['avg_z'] < z_mid]
        
        
        if len(top_edges) == 0 or len(bottom_edges) == 0:
            # Fallback to original method if split doesn't work
            z_tolerance = 0.2
            bottom_candidates = [e for e in horizontal_edges if abs(e['avg_z'] - horizontal_edges[0]['avg_z']) < z_tolerance]
            top_candidates = [e for e in horizontal_edges if abs(e['avg_z'] - horizontal_edges[-1]['avg_z']) < z_tolerance]
            
            
            return top_candidates, bottom_candidates
        
        return top_edges, bottom_edges
    else:
        return None, None

def create_sleeve_horizontal_springs(sleeve_obj, top_edges, bottom_edges):
    """Create sewing springs between top and bottom horizontal edges - same as cuff approach"""
    
    
    # Create spring object
    spring_name = f"SewingSpring_Sleeve_Horizontal_{sleeve_obj.name}"
    spring_mesh = bpy.data.meshes.new(spring_name)
    spring_obj = bpy.data.objects.new(spring_name, spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    vert_index = 0
    
    # Combine all edge segments into continuous paths with proper interpolation
    def create_interpolated_points(edges, num_points=10):
        # Sort edges by Y position
        edges.sort(key=lambda e: min(e['v1_world'].y, e['v2_world'].y))
        
        # Find overall Y range
        all_y_coords = []
        for edge in edges:
            all_y_coords.extend([edge['v1_world'].y, edge['v2_world'].y])
        
        y_min = min(all_y_coords)
        y_max = max(all_y_coords)
        
        
        interpolated_points = []
        
        # Create evenly spaced points across the Y range
        for i in range(num_points):
            if num_points == 1:
                target_y = (y_min + y_max) / 2
            else:
                t = i / (num_points - 1)
                target_y = y_min + t * (y_max - y_min)
            
            # Find the edge segment that contains this Y position
            best_point = None
            for edge in edges:
                v1, v2 = edge['v1_world'], edge['v2_world']
                edge_y_min = min(v1.y, v2.y)
                edge_y_max = max(v1.y, v2.y)
                
                # If target Y is within this edge's Y range
                if edge_y_min <= target_y <= edge_y_max:
                    # Interpolate along this edge
                    if abs(v2.y - v1.y) > 0.001:  # Avoid division by zero
                        t_edge = (target_y - v1.y) / (v2.y - v1.y)
                        t_edge = max(0, min(1, t_edge))  # Clamp to [0,1]
                        best_point = v1 + t_edge * (v2 - v1)
                        break
            
            # If no edge contains this Y, find closest edge endpoint
            if best_point is None:
                min_dist = float('inf')
                for edge in edges:
                    for vertex in [edge['v1_world'], edge['v2_world']]:
                        dist = abs(vertex.y - target_y)
                        if dist < min_dist:
                            min_dist = dist
                            best_point = vertex
            
            if best_point:
                interpolated_points.append(best_point)
        
        return interpolated_points
    
    # Create interpolated points for top and bottom edges
    num_stitches = 10
    top_points = create_interpolated_points(top_edges, num_stitches)
    bottom_points = create_interpolated_points(bottom_edges, num_stitches)
    
    
    # Create vertical stitches connecting corresponding points
    num_connections = min(len(top_points), len(bottom_points))
    
    for i in range(num_connections):
        top_point = top_points[i]
        bottom_point = bottom_points[i]
        
        
        all_spring_verts.extend([top_point, bottom_point])
        all_spring_edges.append([vert_index, vert_index + 1])
        vert_index += 2
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (pink for sleeve horizontal)
    mat = bpy.data.materials.new(name=f"SewingSpring_Sleeve_Horizontal_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1, 0.75, 0.8, 1)  # Pink
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    if not any(mod.type == 'CLOTH' for mod in sleeve_obj.modifiers):
        cloth_mod = sleeve_obj.modifiers.new(name="Cloth", type='CLOTH')
        cloth_mod.settings.quality = 5
        cloth_mod.settings.mass = 0.3
        cloth_mod.settings.tension_stiffness = 15
        cloth_mod.settings.compression_stiffness = 15
        cloth_mod.settings.shear_stiffness = 5
        cloth_mod.settings.bending_stiffness = 0.5
        cloth_mod.settings.use_sewing_springs = True
        cloth_mod.settings.sewing_force_max = 0.5

def setup_sleeve_cuff_horizontal_seams():
    """Connect top and bottom horizontal edges of each sleeve cuff"""
    
    
    cuff_objects = []
    for obj in bpy.data.objects:
        if "_sleeve_cuff_" in obj.name.lower() and obj.data and obj.data.vertices and not obj.name.startswith("SewingSpring"):
            cuff_objects.append(obj)
    
    if not cuff_objects:
        return
    
    
    for cuff_obj in cuff_objects:
        
        top_edges, bottom_edges = find_sleeve_cuff_horizontal_edges(cuff_obj)
        
        if top_edges and bottom_edges:
            create_sleeve_cuff_horizontal_springs(cuff_obj, top_edges, bottom_edges)
        
    

def find_sleeve_cuff_horizontal_edges(cuff_obj):
    """Find top and bottom horizontal edges that run along Y direction"""
    
    if not cuff_obj.data or not cuff_obj.data.edges:
        return None, None
    
    mesh = cuff_obj.data
    bpy.context.view_layer.objects.active = cuff_obj
    cuff_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bm.edges.ensure_lookup_table()
    
    horizontal_edges = []
    
    # Get mesh X bounds for back side detection
    all_x_coords = [cuff_obj.matrix_world @ v.co for v in cuff_obj.data.vertices]
    min_x = min(coord.x for coord in all_x_coords)
    max_x = max(coord.x for coord in all_x_coords)
    x_threshold = min_x + (max_x - min_x) * 0.5
    
    # Analyze ALL edges first
    all_edges_info = []
    
    for edge in bm.edges:
        v1 = cuff_obj.matrix_world @ edge.verts[0].co
        v2 = cuff_obj.matrix_world @ edge.verts[1].co
        
        edge_vector = v2 - v1
        y_component = abs(edge_vector.y)
        z_component = abs(edge_vector.z)
        x_component = abs(edge_vector.x)
        avg_z = (v1.z + v2.z) / 2
        avg_x = (v1.x + v2.x) / 2
        
        all_edges_info.append({
            'y': y_component,
            'z': z_component, 
            'x': x_component,
            'avg_z': avg_z,
            'avg_x': avg_x,
            'length': edge_vector.length
        })
        
        # More relaxed: Y should be dominant component (removed back side filter - cuff is too thin)
        if y_component > 0.1 and y_component > z_component and y_component > x_component:
            edge_data = {
                'edge': edge,
                'v1_world': v1,
                'v2_world': v2,
                'avg_z': avg_z,
                'length': edge_vector.length
            }
            horizontal_edges.append(edge_data)
        
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    
    if not horizontal_edges:
        # Show the edge with highest Y component for debugging
        if all_edges_info:
            best_y = max(all_edges_info, key=lambda e: e['y'])
        return None, None
    
    # Sort by Z position to find top and bottom
    horizontal_edges.sort(key=lambda e: e['avg_z'])
    
    # Filter to get only the actual top and bottom edges (collect ALL edges at each Z level)
    if len(horizontal_edges) >= 2:
        # Group edges by similar Z values 
        bottom_candidates = [e for e in horizontal_edges if abs(e['avg_z'] - horizontal_edges[0]['avg_z']) < 0.05]
        top_candidates = [e for e in horizontal_edges if abs(e['avg_z'] - horizontal_edges[-1]['avg_z']) < 0.05]
        
   
        return top_candidates, bottom_candidates
    else:
        return None, None

def create_sleeve_cuff_horizontal_springs(cuff_obj, top_edges, bottom_edges):
    """Create sewing springs between top and bottom horizontal edges"""

    # Create spring object
    spring_name = f"SewingSpring_SleeveCuff_Horizontal_{cuff_obj.name}"
    spring_mesh = bpy.data.meshes.new(spring_name)
    spring_obj = bpy.data.objects.new(spring_name, spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    vert_index = 0
    
    # Combine all edge segments into continuous paths with proper interpolation
    def create_interpolated_points(edges, num_points=12):
        # Sort edges by Y position
        edges.sort(key=lambda e: min(e['v1_world'].y, e['v2_world'].y))
        
        # Find overall Y range
        all_y_coords = []
        for edge in edges:
            all_y_coords.extend([edge['v1_world'].y, edge['v2_world'].y])
        
        y_min = min(all_y_coords)
        y_max = max(all_y_coords)
        
        
        interpolated_points = []
        
        # Create evenly spaced points across the Y range
        for i in range(num_points):
            if num_points == 1:
                target_y = (y_min + y_max) / 2
            else:
                t = i / (num_points - 1)
                target_y = y_min + t * (y_max - y_min)
            
            # Find the edge segment that contains this Y position
            best_point = None
            for edge in edges:
                v1, v2 = edge['v1_world'], edge['v2_world']
                edge_y_min = min(v1.y, v2.y)
                edge_y_max = max(v1.y, v2.y)
                
                # If target Y is within this edge's Y range
                if edge_y_min <= target_y <= edge_y_max:
                    # Interpolate along this edge
                    if abs(v2.y - v1.y) > 0.001:  # Avoid division by zero
                        t_edge = (target_y - v1.y) / (v2.y - v1.y)
                        t_edge = max(0, min(1, t_edge))  # Clamp to [0,1]
                        best_point = v1 + t_edge * (v2 - v1)
                        break
            
            # If no edge contains this Y, find closest edge endpoint
            if best_point is None:
                min_dist = float('inf')
                for edge in edges:
                    for vertex in [edge['v1_world'], edge['v2_world']]:
                        dist = abs(vertex.y - target_y)
                        if dist < min_dist:
                            min_dist = dist
                            best_point = vertex
            
            if best_point:
                interpolated_points.append(best_point)
        
        return interpolated_points
    
    # Create interpolated points for top and bottom edges
    num_stitches = 10
    top_points = create_interpolated_points(top_edges, num_stitches)
    bottom_points = create_interpolated_points(bottom_edges, num_stitches)
    
    
    # Create vertical stitches connecting corresponding points
    num_connections = min(len(top_points), len(bottom_points))
    
    for i in range(num_connections):
        top_point = top_points[i]
        bottom_point = bottom_points[i]
        
        
        all_spring_verts.extend([top_point, bottom_point])
        all_spring_edges.append([vert_index, vert_index + 1])
        vert_index += 2
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (light blue for sleeve cuff horizontal)
    mat = bpy.data.materials.new(name=f"SewingSpring_SleeveCuff_Horizontal_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.5, 0.8, 1, 1)  # Light blue
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    
    
    # Add cloth physics
    if not any(mod.type == 'CLOTH' for mod in cuff_obj.modifiers):
        cloth_mod = cuff_obj.modifiers.new(name="Cloth", type='CLOTH')
        cloth_mod.settings.quality = 5
        cloth_mod.settings.mass = 0.3
        cloth_mod.settings.tension_stiffness = 15
        cloth_mod.settings.compression_stiffness = 15
        cloth_mod.settings.shear_stiffness = 5
        cloth_mod.settings.bending_stiffness = 0.5
        cloth_mod.settings.use_sewing_springs = True
        cloth_mod.settings.sewing_force_max = 0.5

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
    
    mirror_line = find_mirror_line_and_visualize(coordinates, "sleeve")
    if mirror_line:
        
        aligned_coords = align_mirror_line_to_y_axis(coordinates, mirror_line)
        return aligned_coords
    else:
        return coordinates

def align_mirror_line_to_y_axis(coordinates, mirror_line):
    line_start, line_end = mirror_line
    
    mirror_dx = line_end[0] - line_start[0]
    mirror_dy = line_end[1] - line_start[1]
    current_angle = math.atan2(mirror_dy, mirror_dx)
    
    target_angle = 0
    rotation_needed = target_angle - current_angle

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

def setup_hood_to_panel_connection():
    """Connect hood bottom edge to front and back panel neck curves"""
    
    
    # Find hood, front panel, and back panel
    hood_objects = []
    front_panel = None
    back_panel = None
    
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "_hood_" in obj_name and obj.data and obj.data.vertices and not obj.name.startswith("SewingSpring"):
            hood_objects.append(obj)
        elif "_front_panel" in obj_name and not obj.name.startswith("SewingSpring"):
            front_panel = obj
        elif "_back_panel" in obj_name and not obj.name.startswith("SewingSpring"):
            back_panel = obj
    
    if not hood_objects or not front_panel or not back_panel:
        return
    
    # Find neckline curves on panels (reuse existing logic)
    front_neckline = find_neckline_curve(front_panel)
    if not front_neckline:
        return
    
    back_neckline = find_neckline_curve(back_panel)
    if not back_neckline:
        return
    
    
    # Process each hood with proper mirroring logic
    for hood_obj in hood_objects:
        # Find hood bottom edge (runs along Y, might curve in Z)
        hood_bottom_edges = find_hood_bottom_edge(hood_obj)
        if not hood_bottom_edges:
            continue
        
        
        # Determine if this is left hood (-Y) or right hood (+Y)
        hood_avg_y = sum(edge['avg_y'] for edge in hood_bottom_edges) / len(hood_bottom_edges)
        is_left_hood = hood_avg_y < 0
        
        
        # Split hood bottom edge into outer and inner halves
        outer_hood_edges, inner_hood_edges = split_hood_bottom_edge_vertically(hood_bottom_edges)
        
        if not outer_hood_edges or not inner_hood_edges:
            continue
        
        
        if is_left_hood:
            # Left hood (-Y): outer (-Y) to front panel -Y half, inner (-Y) to back panel -Y half
            front_neckline_half = [edge for edge in front_neckline if ((edge[1].y + edge[2].y) / 2) < 0]  # -Y half
            back_neckline_half = [edge for edge in back_neckline if ((edge[1].y + edge[2].y) / 2) < 0]   # -Y half
            
            
            # Outer hood edges (most -Y) connect to front panel -Y half
            create_hood_to_panel_springs(hood_obj, outer_hood_edges, front_panel, front_neckline_half, "front-left")
            # Inner hood edges (least -Y) connect to back panel -Y half  
            create_hood_to_panel_springs(hood_obj, inner_hood_edges, back_panel, back_neckline_half, "back-left")
        else:
            # Right hood (+Y): outer (+Y) to front panel +Y half, inner (+Y) to back panel +Y half
            front_neckline_half = [edge for edge in front_neckline if ((edge[1].y + edge[2].y) / 2) >= 0]  # +Y half
            back_neckline_half = [edge for edge in back_neckline if ((edge[1].y + edge[2].y) / 2) >= 0]   # +Y half
            
            
            # For right hood, the split is reversed: first half (least +Y) goes to back, second half (most +Y) goes to front
            # Inner hood edges (least +Y) connect to back panel +Y half
            create_hood_to_panel_springs(hood_obj, outer_hood_edges, back_panel, back_neckline_half, "back-right")
            # Outer hood edges (most +Y) connect to front panel +Y half  
            create_hood_to_panel_springs(hood_obj, inner_hood_edges, front_panel, front_neckline_half, "front-right")
    

def create_debug_stitch_at_edge(edge_data, name):
    """Create a visual debug stitch to mark an edge location"""
    
    # Create a new mesh for the debug stitch
    stitch_mesh = bpy.data.meshes.new(f"DebugStitch_{name}")
    stitch_obj = bpy.data.objects.new(f"DebugStitch_{name}", stitch_mesh)
    
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(stitch_obj)
    else:
        bpy.context.collection.objects.link(stitch_obj)
    
    # Create vertices and edges for the debug stitch
    verts = []
    edges = []
    
    # Use the edge endpoints
    v1_world = edge_data['v1_world']
    v2_world = edge_data['v2_world']
    
    # Add the edge vertices
    verts.append((v1_world.x, v1_world.y, v1_world.z))
    verts.append((v2_world.x, v2_world.y, v2_world.z))
    
    # Create edge connecting the vertices
    edges.append([0, 1])
    
    # Create the mesh
    stitch_mesh.from_pydata(verts, edges, [])
    stitch_mesh.update()
    

def setup_sleeve_to_panel_connection():
    """Connect sleeve vertical edges to panel sleeve holes"""
    
    
    # Find sleeve objects
    sleeve_objects = []
    for obj in bpy.data.objects:
        obj_name = obj.name.lower()
        if "_sleeve_" in obj_name and not "_cuff_" in obj_name and obj.data and obj.data.vertices and not obj.name.startswith("SewingSpring"):
            sleeve_objects.append(obj)
    
    
    if not sleeve_objects:
        return
    
    # Process each sleeve
    for sleeve_obj in sleeve_objects:
        
        # Step 1: Find sleeve side edge starting point
        sleeve_side_start = find_sleeve_side_start_edge(sleeve_obj)
        
        if not sleeve_side_start:
            continue
        
        
        # DEBUG: Add visual stitch to mark the starting edge
        create_debug_stitch_at_edge(sleeve_side_start, f"START_{sleeve_obj.name}")
        
        # Step 2: Collect the full sleeve side edge with 60° Y tolerance
        full_sleeve_edge = collect_sleeve_side_edges(sleeve_obj, sleeve_side_start)
        
        if not full_sleeve_edge:
            continue
        
        
        
        # Step 3: Split sleeve edge in half along Z axis
        bottom_sleeve_edges, top_sleeve_edges = split_sleeve_edge_by_z(full_sleeve_edge)
        
        if not bottom_sleeve_edges or not top_sleeve_edges:
            continue
        
        
        # Step 4: Find sleeve hole curves on front and back panels
        front_panel = None
        back_panel = None
        
        for obj in bpy.data.objects:
            obj_name = obj.name.lower()
            if "_front_panel" in obj_name and not obj.name.startswith("SewingSpring"):
                front_panel = obj
            elif "_back_panel" in obj_name and not obj.name.startswith("SewingSpring"):
                back_panel = obj
        
        
        if not front_panel or not back_panel:
            continue
        
        # Determine which side this sleeve is on by checking its Y position
        sleeve_y_side = 'positive' if sleeve_side_start['avg_y'] > 0 else 'negative'
        
        # Find sleeve hole curves (vertical along Z with Y tolerance) on the same side
        front_sleeve_curve = find_sleeve_hole_curve(front_panel, sleeve_y_side)
        back_sleeve_curve = find_sleeve_hole_curve(back_panel, sleeve_y_side)
    
        
        if not front_sleeve_curve or not back_sleeve_curve:
           
            continue
        
        
        
        # Create actual spring connections
        create_sleeve_to_panel_springs(sleeve_obj.name, bottom_sleeve_edges, front_sleeve_curve, front_panel, "front")
        
        create_sleeve_to_panel_springs(sleeve_obj.name, top_sleeve_edges, back_sleeve_curve, back_panel, "back")
    

def create_sleeve_to_panel_springs(sleeve_name, sleeve_edges, panel_curve_edges, panel_obj, panel_side):
    """Create sewing springs between sleeve edges and panel sleeve hole curve"""
    
    if not sleeve_edges or not panel_curve_edges:
        return
    
    
    
    # Create spring object
    spring_name = f"SewingSpring_Sleeve_{sleeve_name}_to_{panel_side.title()}Panel"
    spring_mesh = bpy.data.meshes.new(spring_name)
    spring_obj = bpy.data.objects.new(spring_name, spring_mesh)
    
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    vert_index = 0
    
    # Convert panel curve edges from tuples to dictionary format to match sleeve edges
    panel_edges = []
    for edge_data in panel_curve_edges:
        # Panel curve is a tuple: (edge, v1, v2, length, avg_z)
        edge, v1, v2, length, avg_z = edge_data
        panel_edges.append({
            'v1_world': v1,
            'v2_world': v2,
            'avg_z': avg_z,
            'avg_y': (v1.y + v2.y) / 2,
            'length': length
        })
    
    # Create horizontal stitch points along Y axis
    def create_horizontal_stitch_points(edges, num_points=6):
        if not edges:
            return []
        
        # Find Y range of the edges
        all_y_coords = []
        for edge in edges:
            all_y_coords.extend([edge['v1_world'].y, edge['v2_world'].y])
        
        if not all_y_coords:
            return []
            
        min_y = min(all_y_coords)
        max_y = max(all_y_coords)
        y_range = max_y - min_y
        
        if y_range == 0:
            # All points at same Y, use center points
            center_points = []
            for edge in edges[:num_points]:
                center = (edge['v1_world'] + edge['v2_world']) / 2
                center_points.append(center)
            return center_points
        
        # Create evenly spaced Y coordinates
        stitch_points = []
        for i in range(num_points):
            if num_points == 1:
                target_y = (min_y + max_y) / 2
            else:
                target_y = min_y + (i / (num_points - 1)) * y_range
            
            # Find the edge closest to this Y coordinate
            best_edge = None
            best_distance = float('inf')
            
            for edge in edges:
                edge_center_y = (edge['v1_world'].y + edge['v2_world'].y) / 2
                distance = abs(edge_center_y - target_y)
                if distance < best_distance:
                    best_distance = distance
                    best_edge = edge
            
            if best_edge:
                # Use center of the best edge
                center = (best_edge['v1_world'] + best_edge['v2_world']) / 2
                stitch_points.append(center)
        
        return stitch_points
    
    # Sort both edge sets by Z coordinate (height) to get proper spatial order
    sleeve_edges_sorted = sorted(sleeve_edges, key=lambda e: e['avg_z'])
    panel_edges_sorted = sorted(panel_edges, key=lambda e: e['avg_z'])
    
    # Create more stitches for better distribution
    num_stitches = max(8, min(len(sleeve_edges_sorted), len(panel_edges_sorted)))
    sleeve_points = []
    panel_points = []
    
    # Get evenly spaced points from sorted sleeve edges
    for i in range(num_stitches):
        if len(sleeve_edges_sorted) == 1:
            edge = sleeve_edges_sorted[0]
        else:
            edge_index = int(i * (len(sleeve_edges_sorted) - 1) / (num_stitches - 1))
            edge = sleeve_edges_sorted[edge_index]
        center = (edge['v1_world'] + edge['v2_world']) / 2
        sleeve_points.append(center)
    
    # Get evenly spaced points from sorted panel edges  
    for i in range(num_stitches):
        if len(panel_edges_sorted) == 1:
            edge = panel_edges_sorted[0]
        else:
            edge_index = int(i * (len(panel_edges_sorted) - 1) / (num_stitches - 1))
            edge = panel_edges_sorted[edge_index]
        center = (edge['v1_world'] + edge['v2_world']) / 2
        panel_points.append(center)
    
    if len(sleeve_points) != len(panel_points):
        min_points = min(len(sleeve_points), len(panel_points))
        sleeve_points = sleeve_points[:min_points]
        panel_points = panel_points[:min_points]
    
    # Check which order minimizes total distance to prevent crossover
    if len(sleeve_points) > 1 and len(panel_points) > 1:
        total_dist_normal = sum((sleeve_points[i] - panel_points[i]).length for i in range(len(sleeve_points)))
        total_dist_reversed = sum((sleeve_points[i] - panel_points[-(i+1)]).length for i in range(len(sleeve_points)))
        
        if total_dist_reversed < total_dist_normal:
            panel_points.reverse()
    
    # Create spring connections
    for i in range(len(sleeve_points)):
        sleeve_point = sleeve_points[i]
        panel_point = panel_points[i]
        
        # Add vertices
        all_spring_verts.extend([sleeve_point, panel_point])
        
        # Add edge connecting them
        all_spring_edges.append([vert_index, vert_index + 1])
        vert_index += 2
        
    
    # Create the mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    

def find_sleeve_side_start_edge(sleeve_obj):
    """Find the starting edge: lowest Z, closest to Y=0, runs mostly vertical on Z"""
    
    if not sleeve_obj.data or not sleeve_obj.data.edges:
        return None
    
    mesh = sleeve_obj.data
    bpy.context.view_layer.objects.active = sleeve_obj
    sleeve_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bm.edges.ensure_lookup_table()
    
    # First pass: find ALL valid vertical edges and their Z values
    valid_edges = []
    
    for edge in bm.edges:
        v1 = sleeve_obj.matrix_world @ edge.verts[0].co
        v2 = sleeve_obj.matrix_world @ edge.verts[1].co
        edge_vector = v2 - v1
        
        # Check if edge runs mostly vertical on Z
        z_component = abs(edge_vector.z)
        y_component = abs(edge_vector.y)
        x_component = abs(edge_vector.x)
        
        # CONDITION 1: Edge must be more vertical (Z) than horizontal (Y)
        if z_component <= y_component:
            continue  # Skip horizontal edges
        
        # CONDITION 2: Original criteria - edge runs mostly vertical on Z
        if z_component > 0.02 and z_component > x_component:
            min_z = min(v1.z, v2.z)  # Lowest Z (bottom of sleeve)
            avg_y = abs((v1.y + v2.y) / 2)  # Distance from Y=0
            
            valid_edges.append({
                'v1_world': v1,
                'v2_world': v2,
                'avg_y': (v1.y + v2.y) / 2,
                'min_z': min_z,
                'z_component': z_component,
                'y_distance': avg_y
            })
            
    
    if not valid_edges:
        bpy.ops.object.mode_set(mode='OBJECT')
        return None
    
    # Find the absolute lowest Z among all valid edges
    lowest_z = min(edge['min_z'] for edge in valid_edges)
    
    # Filter edges that are at or very close to the lowest Z (within 0.005 tolerance)
    z_tolerance = 0.005
    lowest_z_edges = [edge for edge in valid_edges if edge['min_z'] <= lowest_z + z_tolerance]
    
    
    # Among the lowest Z edges, pick the one closest to Y=0
    best_edge = min(lowest_z_edges, key=lambda e: e['y_distance'])
    
    
    bpy.ops.object.mode_set(mode='OBJECT')
    

    
    return best_edge

def collect_sleeve_side_edges(sleeve_obj, start_edge_data):
    """Collect connected edges moving UP on Z until diagonal change > 60° towards Y axis"""
    
    if not sleeve_obj.data or not sleeve_obj.data.edges:
        return None
    
    mesh = sleeve_obj.data
    bpy.context.view_layer.objects.active = sleeve_obj
    sleeve_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    
    
    # Find the start edge in the current bmesh context
    start_edge = None
    start_v1_world = start_edge_data['v1_world']
    start_v2_world = start_edge_data['v2_world']
    
    # Find the corresponding edge in current bmesh
    for edge in bm.edges:
        v1 = sleeve_obj.matrix_world @ edge.verts[0].co
        v2 = sleeve_obj.matrix_world @ edge.verts[1].co
        
        min_z = min(v1.z, v2.z)
        
        # Check if this matches our start edge (within tolerance)
        if ((v1 - start_v1_world).length < 0.001 and (v2 - start_v2_world).length < 0.001) or \
           ((v1 - start_v2_world).length < 0.001 and (v2 - start_v1_world).length < 0.001):
            start_edge = edge
            break
    
    if not start_edge:
        bpy.ops.object.mode_set(mode='OBJECT')
        return None
    
    # Start from the found edge
    sleeve_edges = []
    current_edge = start_edge
    visited_edges = set()
    
    # Debug: show actual starting edge Z
    start_v1 = sleeve_obj.matrix_world @ start_edge.verts[0].co
    start_v2 = sleeve_obj.matrix_world @ start_edge.verts[1].co
    start_avg_z = (start_v1.z + start_v2.z) / 2
    
    # Store debug stitch data for later creation (after we exit edit mode)
    collection_start_data = {
        'v1_world': start_v1,
        'v2_world': start_v2,
        'min_z': start_avg_z,
        'name': f"COLLECT_{sleeve_obj.name}"
    }
    
    def get_edge_vector(edge):
        v1 = sleeve_obj.matrix_world @ edge.verts[0].co
        v2 = sleeve_obj.matrix_world @ edge.verts[1].co
        return v2 - v1
    
    def angle_between_vectors(v1, v2):
        dot_product = v1.dot(v2)
        mag1 = v1.length
        mag2 = v2.length
        if mag1 == 0 or mag2 == 0:
            return 0
        cos_angle = max(-1, min(1, dot_product / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))
    
    while current_edge and current_edge not in visited_edges:
        visited_edges.add(current_edge)
        
        # Add current edge to sleeve edges
        v1 = sleeve_obj.matrix_world @ current_edge.verts[0].co
        v2 = sleeve_obj.matrix_world @ current_edge.verts[1].co
        current_vector = get_edge_vector(current_edge)
        edge_data = {
            'v1_world': v1,
            'v2_world': v2,
            'avg_z': (v1.z + v2.z) / 2,
            'avg_y': (v1.y + v2.y) / 2,
            'length': current_vector.length
        }
        sleeve_edges.append(edge_data)
        
        
        # Find next connected edge that moves UP on Z
        next_edge = None
        current_avg_z = (v1.z + v2.z) / 2
        
        # Collect ALL connected edges that go UP on Z
        candidates = []
        for vert in current_edge.verts:
            for connected_edge in vert.link_edges:
                if connected_edge == current_edge or connected_edge in visited_edges:
                    continue
                
                # Get the Z position of this connected edge
                connected_v1 = sleeve_obj.matrix_world @ connected_edge.verts[0].co
                connected_v2 = sleeve_obj.matrix_world @ connected_edge.verts[1].co
                connected_avg_z = (connected_v1.z + connected_v2.z) / 2
                
                # Only consider edges that move UP on Z gradually (not big jumps)
                z_diff = connected_avg_z - current_avg_z
                if z_diff > 0:
                    if z_diff < 0.1:  # Gradual UP movement, not big jumps
                        # Calculate angle between current and next edge
                        next_vector = get_edge_vector(connected_edge)
                        angle_change = angle_between_vectors(current_vector, next_vector)
                        perpendicular_angle = min(angle_change, 180 - angle_change)
                        
                        candidates.append({
                            'edge': connected_edge,
                            'angle': perpendicular_angle,
                            'z': connected_avg_z
                        })
        
        # Pick the best candidate (smallest angle change)
        if candidates:
            best_candidate = min(candidates, key=lambda c: c['angle'])
            
            # If best angle > 60°, we stop
            if best_candidate['angle'] > 60.0:
                next_edge = None
            else:
                next_edge = best_candidate['edge']
        else:
            next_edge = None
        
        # Move to next edge or stop
        current_edge = next_edge
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create debug stitch for collection start point
    if 'collection_start_data' in locals():
        create_debug_stitch_at_edge(collection_start_data, collection_start_data['name'])
    
    return sleeve_edges if sleeve_edges else None

def split_sleeve_edge_by_z(sleeve_edges):
    """Split sleeve edges in half along Z axis"""
    
    if not sleeve_edges:
        return None, None
    
    # Sort edges by Z position
    sorted_edges = sorted(sleeve_edges, key=lambda e: e['avg_z'])
    
    # Split in half by count
    mid_index = len(sorted_edges) // 2
    
    bottom_edges = sorted_edges[:mid_index]  # Lower Z (front panel)
    top_edges = sorted_edges[mid_index:]     # Higher Z (back panel)
    
    if bottom_edges:
        bottom_z_range = f"{min(e['avg_z'] for e in bottom_edges):.3f} to {max(e['avg_z'] for e in bottom_edges):.3f}"
    
    if top_edges:
        top_z_range = f"{min(e['avg_z'] for e in top_edges):.3f} to {max(e['avg_z'] for e in top_edges):.3f}"
    
    return bottom_edges, top_edges

def find_sleeve_hole_curve(panel_obj, sleeve_y_side):
    """
    Find the armhole curve on a panel using simple bottom-up edge following
    """
    
    mesh = panel_obj.data
    if not mesh.vertices:
        return None
    
    # Convert sleeve_y_side to numeric sign for side detection
    y_sign = 1 if sleeve_y_side == 'positive' else -1
    
    # STEP 1: Find the bottom horizontal running part of the panel
    
    # Find all horizontal edges with lowest Z values
    all_world_verts = [panel_obj.matrix_world @ v.co for v in mesh.vertices]
    min_z_global = min(v.z for v in all_world_verts)
    max_z_global = max(v.z for v in all_world_verts)
    garment_height = max_z_global - min_z_global
    z_tolerance = garment_height * 0.02  # Within 2% of garment height from bottom
    connection_tolerance = garment_height * 0.001  # Connection tolerance scales with garment size
    
    horizontal_edges = []
    for edge in mesh.edges:
        v1 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
        v2 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
        
        edge_vector = v2 - v1
        edge_length = edge_vector.length
        avg_z = (v1.z + v2.z) / 2
        
        if edge_length == 0:
            continue
            
        # Check if edge runs horizontal on Y (not vertical on Z)
        y_component = abs(edge_vector.y)
        z_component = abs(edge_vector.z)
        is_horizontal = y_component > z_component
        
        # Check if edge is near the bottom
        is_at_bottom = abs(avg_z - min_z_global) < z_tolerance
        
        if is_horizontal and is_at_bottom:
            horizontal_edges.append({
                'edge': edge,
                'v1': v1,
                'v2': v2,
                'avg_y': (v1.y + v2.y) / 2,
                'avg_z': avg_z,
                'length': edge_length
            })
    
    if not horizontal_edges:
        return None
    
    
    # STEP 2: Find the ENDS of the horizontal part (leftmost and rightmost VERTICES)
    all_vertices = []
    for edge_data in horizontal_edges:
        all_vertices.extend([edge_data['v1'], edge_data['v2']])
    
    # Find the leftmost and rightmost vertices
    left_end_vertex = min(all_vertices, key=lambda v: v.y)
    right_end_vertex = max(all_vertices, key=lambda v: v.y)
    
    
    # STEP 3: Find the starting vertical edge on the specified side
    if y_sign > 0:
        # Positive side - use right end vertex
        target_vertex = right_end_vertex
        side_name = "right"
    else:
        # Negative side - use left end vertex  
        target_vertex = left_end_vertex
        side_name = "left"
    
    
    # Find edge that goes UP from the target vertex
    starting_vertical_edge = None
    best_z_component = 0
    
    for edge in mesh.edges:
        v1 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[0]].co
        v2 = panel_obj.matrix_world @ mesh.vertices[edge.vertices[1]].co
        
        # Check if this edge connects to the target vertex
        connects_to_vertex = (
            (v1 - target_vertex).length < connection_tolerance or (v2 - target_vertex).length < connection_tolerance
        )
        
        if connects_to_vertex:
            edge_vector = v2 - v1
            edge_length = edge_vector.length
            
            if edge_length == 0:
                continue
                
            # Check if edge moves UP (positive Z direction) and is mostly vertical
            z_component = abs(edge_vector.z)
            y_component = abs(edge_vector.y)
            
            # Determine which vertex is the target and check if edge goes UP from it
            if (v1 - target_vertex).length < 0.01:
                # v1 is target, check if v2 is higher
                moves_up = v2.z > v1.z
            else:
                # v2 is target, check if v1 is higher
                moves_up = v1.z > v2.z
                
            is_mostly_vertical = z_component > y_component
            
            
            # Must move upward and be mostly vertical
            if moves_up and is_mostly_vertical and z_component > best_z_component:
                best_z_component = z_component
                starting_vertical_edge = (edge, v1, v2)
    
    if not starting_vertical_edge:
        return None
    
    
    # Create debug marker for the starting vertical edge
    debug_mesh = bpy.data.meshes.new(f"DEBUG_VERTICAL_START_{panel_obj.name}_{sleeve_y_side}")
    debug_obj = bpy.data.objects.new(f"DEBUG_VERTICAL_START_{panel_obj.name}_{sleeve_y_side}", debug_mesh)
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(debug_obj)
    else:
        bpy.context.collection.objects.link(debug_obj)
    
    # Create sphere at the starting vertical edge midpoint
    edge, v1, v2 = starting_vertical_edge
    midpoint = (v1 + v2) / 2
    verts = [midpoint]
    debug_mesh.from_pydata(verts, [], [])
    debug_mesh.update()
    
    bottom_edge = starting_vertical_edge
    
    # STEP 2: Follow edges upward until we hit a 35° curve (armhole start)
    vertical_edges = [bottom_edge]
    current_edge, current_v1, current_v2 = bottom_edge
    processed_edges = {current_edge}
    
    # Start from the top vertex of the bottom edge
    current_top = current_v1 if current_v1.z > current_v2.z else current_v2
    previous_vector = current_v2 - current_v1
    
    
    # Follow vertical edges upward
    max_iterations = 50
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        found_next = False
        
        for next_edge in mesh.edges:
            if next_edge in processed_edges:
                continue
                
            nv1 = panel_obj.matrix_world @ mesh.vertices[next_edge.vertices[0]].co
            nv2 = panel_obj.matrix_world @ mesh.vertices[next_edge.vertices[1]].co
            
            # Check if this edge connects to our current top vertex
            # Use same connection tolerance as before (scales with garment)
            connects_to_top = (nv1 - current_top).length < connection_tolerance or (nv2 - current_top).length < connection_tolerance
            
            if connects_to_top:
                edge_vector = nv2 - nv1
                edge_length = edge_vector.length
                
                if edge_length == 0:
                    continue
                
                # Calculate angle change between previous edge and this edge
                if previous_vector.length > 0:
                    prev_norm = previous_vector.normalized()
                    curr_norm = edge_vector.normalized()
                    dot_product = max(-1.0, min(1.0, prev_norm.dot(curr_norm)))
                    angle_change = math.degrees(math.acos(abs(dot_product)))
                    
                    
                    # If angle > 35°, this is the start of the armhole
                    if angle_change > 35:
                        avg_z = (nv1.z + nv2.z) / 2
                        armhole_start_edge = (next_edge, nv1, nv2, edge_length, avg_z)
                        break
                
                # Continue vertical trace
                vertical_edges.append((next_edge, nv1, nv2))
                processed_edges.add(next_edge)
                current_edge = next_edge
                current_v1, current_v2 = nv1, nv2
                current_top = nv1 if nv1.z > nv2.z else nv2
                previous_vector = edge_vector
                found_next = True
                break
        
        if not found_next:
            break
    
    # Check if we found an armhole start
    if 'armhole_start_edge' not in locals():
        return None
    
    
    # STEP 3: Follow the armhole curve until we hit a 60° angle change (armhole end)
    armhole_edges = [armhole_start_edge]
    current_edge, current_v1, current_v2, _, _ = armhole_start_edge
    processed_edges.add(current_edge)
    
    # Start from the endpoint of the armhole start edge (highest Z)
    current_endpoint = current_v1 if current_v1.z > current_v2.z else current_v2
    previous_vector = current_v2 - current_v1
    
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        found_next = False
        
        for next_edge in mesh.edges:
            if next_edge in processed_edges:
                continue
                
            nv1 = panel_obj.matrix_world @ mesh.vertices[next_edge.vertices[0]].co
            nv2 = panel_obj.matrix_world @ mesh.vertices[next_edge.vertices[1]].co
            
            # Check if this edge connects to our current endpoint
            connects_to_current = (nv1 - current_endpoint).length < 0.01 or (nv2 - current_endpoint).length < 0.01
            
            if connects_to_current:
                edge_vector = nv2 - nv1
                edge_length = edge_vector.length
                
                if edge_length == 0:
                    continue
                
                # Calculate angle change between current edge and next edge
                if previous_vector.length > 0:
                    prev_norm = previous_vector.normalized()
                    curr_norm = edge_vector.normalized()
                    dot_product = max(-1.0, min(1.0, prev_norm.dot(curr_norm)))
                    angle_change = math.degrees(math.acos(abs(dot_product)))
                    
                    
                    # If angle > 60°, we've reached the end of the armhole
                    if angle_change > 60:
                        break
                
                # Continue armhole trace
                avg_z = (nv1.z + nv2.z) / 2
                armhole_edges.append((next_edge, nv1, nv2, edge_length, avg_z))
                processed_edges.add(next_edge)
                current_edge = next_edge
                current_v1, current_v2 = nv1, nv2
                current_endpoint = nv1 if nv1.z > nv2.z else nv2
                previous_vector = edge_vector
                found_next = True
                break
        
        if not found_next:
            break
    
    
    if len(armhole_edges) < 2:
        return None
    
    # Create debug visualization at armhole start
    if armhole_edges:
        debug_mesh = bpy.data.meshes.new(f"DEBUG_ARMHOLE_START_{panel_obj.name}_{sleeve_y_side}")
        debug_obj = bpy.data.objects.new(f"DEBUG_ARMHOLE_START_{panel_obj.name}_{sleeve_y_side}", debug_mesh)
        if "FashionSynth" in bpy.data.collections:
            bpy.data.collections["FashionSynth"].objects.link(debug_obj)
        else:
            bpy.context.collection.objects.link(debug_obj)
        
        # Create sphere at armhole start
        start_edge = armhole_edges[0]
        midpoint = (start_edge[1] + start_edge[2]) / 2
        verts = [midpoint]
        debug_mesh.from_pydata(verts, [], [])
        debug_mesh.update()
    
    return armhole_edges


def find_hood_bottom_edge(hood_obj):
    """Find the complete bottom horizontal edge group by following connected edges until hitting a corner"""
    
    if not hood_obj.data or not hood_obj.data.edges:
        return None
    
    mesh = hood_obj.data
    bpy.context.view_layer.objects.active = hood_obj
    hood_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    
    
    # Step 1: Find the lowest Z level (bottom of hood)
    all_z_coords = []
    for edge in bm.edges:
        v1 = hood_obj.matrix_world @ edge.verts[0].co
        v2 = hood_obj.matrix_world @ edge.verts[1].co
        all_z_coords.extend([v1.z, v2.z])
    
    min_z = min(all_z_coords)
    max_z = max(all_z_coords)
    hood_height = max_z - min_z
    bottom_z_threshold = min_z + (hood_height * 0.1)  # Look within 10% of hood height from bottom
    
    
    # Step 2: Find starting edge properly - longest vertical edge, then its lowest perpendicular Y edge
    
    # First, find the longest vertical edge (runs in Z direction)
    vertical_edges = []
    for edge in bm.edges:
        v1 = hood_obj.matrix_world @ edge.verts[0].co
        v2 = hood_obj.matrix_world @ edge.verts[1].co
        edge_vector = v2 - v1
        
        z_component = abs(edge_vector.z)
        y_component = abs(edge_vector.y)
        x_component = abs(edge_vector.x)
        
        # Check if edge is mostly vertical (Z dominant)
        if z_component > 0.1 and z_component > y_component and z_component > x_component:
            vertical_edges.append({
                'edge': edge,
                'length': edge_vector.length,
                'v1_world': v1,
                'v2_world': v2
            })
    
    if not vertical_edges:
        bpy.ops.object.mode_set(mode='OBJECT')
        return None
    
    # Find the longest vertical edge
    longest_vertical = max(vertical_edges, key=lambda e: e['length'])
    
    # Step 3: Find perpendicular Y edges connected to this vertical edge that are at bottom level
    start_edge = None
    lowest_z = float('inf')
    
    for vert in longest_vertical['edge'].verts:
        for connected_edge in vert.link_edges:
            if connected_edge == longest_vertical['edge']:
                continue
                
            cv1 = hood_obj.matrix_world @ connected_edge.verts[0].co
            cv2 = hood_obj.matrix_world @ connected_edge.verts[1].co
            cavg_z = (cv1.z + cv2.z) / 2
            
            # Check if this edge is at bottom level and runs in Y direction
            if cavg_z <= bottom_z_threshold:
                cedge_vector = cv2 - cv1
                cy_component = abs(cedge_vector.y)
                cz_component = abs(cedge_vector.z)
                cx_component = abs(cedge_vector.x)
                
                # Must be mostly horizontal in Y direction
                if cy_component > 0.02 and cy_component > cz_component and cy_component > cx_component:
                    # This is a horizontal bottom edge - use the one with lowest Z
                    if cavg_z < lowest_z:
                        lowest_z = cavg_z
                        start_edge = connected_edge
    
    if not start_edge:
        bpy.ops.object.mode_set(mode='OBJECT')
        return None
    
    
    # Step 3: Follow connected edges until hitting a corner
    bottom_edges = []
    current_edge = start_edge
    visited_edges = set()
    
    def get_edge_vector(edge):
        v1 = hood_obj.matrix_world @ edge.verts[0].co
        v2 = hood_obj.matrix_world @ edge.verts[1].co
        return v2 - v1
    
    def angle_between_vectors(v1, v2):
        # Calculate angle between two vectors in degrees
        dot_product = v1.dot(v2)
        mag1 = v1.length
        mag2 = v2.length
        if mag1 == 0 or mag2 == 0:
            return 0
        cos_angle = max(-1, min(1, dot_product / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))
    
    current_vector = get_edge_vector(current_edge)
    
    while current_edge and current_edge not in visited_edges:
        visited_edges.add(current_edge)
        
        # Add current edge to bottom edges
        v1 = hood_obj.matrix_world @ current_edge.verts[0].co
        v2 = hood_obj.matrix_world @ current_edge.verts[1].co
        edge_data = {
            'edge': current_edge,
            'v1_world': v1,
            'v2_world': v2,
            'avg_z': (v1.z + v2.z) / 2,
            'avg_x': (v1.x + v2.x) / 2,
            'avg_y': (v1.y + v2.y) / 2,
            'length': current_vector.length
        }
        bottom_edges.append(edge_data)
        
        
        # Find next connected edge at bottom level
        next_edge = None
        next_vector = None
        candidates = []
        
        for vert in current_edge.verts:
            vert_world = hood_obj.matrix_world @ vert.co
            
            for connected_edge in vert.link_edges:
                if connected_edge == current_edge or connected_edge in visited_edges:
                    continue
                
                # Check if connected edge has horizontal movement
                cv1 = hood_obj.matrix_world @ connected_edge.verts[0].co
                cv2 = hood_obj.matrix_world @ connected_edge.verts[1].co
                cavg_z = (cv1.z + cv2.z) / 2
                
                connected_vector = get_edge_vector(connected_edge)
                cy_component = abs(connected_vector.y)
                
                
                # Must have significant Y movement to be part of bottom edge
                if cy_component > 0.01:
                    angle_change = angle_between_vectors(current_vector, connected_vector)
                    
                    candidates.append({
                        'edge': connected_edge,
                        'vector': connected_vector,
                        'angle_change': angle_change,
                        'y_component': cy_component,
                        'avg_z': cavg_z
                    })
                    
        
        if candidates:
            # Choose the candidate with smallest angle change
            best_candidate = min(candidates, key=lambda c: c['angle_change'])
            angle_change = best_candidate['angle_change']
            
            
            # If angle change > 60°, we've hit a corner - stop
            if angle_change > 60.0:
                break
            else:
                next_edge = best_candidate['edge']
                next_vector = best_candidate['vector']
        else:
            break
        
        current_edge = next_edge
        if next_vector:
            current_vector = next_vector
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    
    return bottom_edges if bottom_edges else None

def split_hood_bottom_edge_vertically(bottom_edges):
    """Split hood bottom edges by length (not just position) into front and back halves"""
    
    if not bottom_edges:
        return None, None
    
    # Sort edges by Y position to ensure proper order
    sorted_edges = sorted(bottom_edges, key=lambda e: e['avg_y'])
    
    # Calculate total length of hood bottom edge
    total_length = sum(edge['length'] for edge in sorted_edges)
    half_length = total_length / 2
    
    
    # Split by cumulative length (not just Y position)
    front_edges = []
    back_edges = []
    current_length = 0
    
    for i, edge in enumerate(sorted_edges):
        current_length += edge['length']
        
        if current_length <= half_length:
            front_edges.append(edge)
        else:
            back_edges.append(edge)
    
    # Get Y ranges for verification
    if front_edges:
        front_y_min = min(e['avg_y'] for e in front_edges)
        front_y_max = max(e['avg_y'] for e in front_edges)
    
    if back_edges:
        back_y_min = min(e['avg_y'] for e in back_edges)
        back_y_max = max(e['avg_y'] for e in back_edges)
    
    
    return front_edges, back_edges

def create_hood_to_panel_springs(hood_obj, hood_edges, panel_obj, panel_neckline, side_name):
    """Create sewing springs between hood edges and panel neckline"""
    
    
    # Create spring object
    spring_name = f"SewingSpring_Hood_To_{side_name.title()}Panel_{hood_obj.name}"
    spring_mesh = bpy.data.meshes.new(spring_name)
    spring_obj = bpy.data.objects.new(spring_name, spring_mesh)
    # Add to FashionSynth collection
    if "FashionSynth" in bpy.data.collections:
        bpy.data.collections["FashionSynth"].objects.link(spring_obj)
    else:
        bpy.context.collection.objects.link(spring_obj)
    
    all_spring_verts = []
    all_spring_edges = []
    vert_index = 0
    
    # Convert panel neckline to same format as hood edges
    panel_edges = []
    for edge_data in panel_neckline:
        # Panel neckline is a tuple: (edge, v1, v2, length, avg_z)
        edge, v1, v2, length, avg_z = edge_data
        panel_edges.append({
            'v1_world': v1,
            'v2_world': v2,
            'avg_y': (v1.y + v2.y) / 2,
            'length': length
        })
    
    # Use same interpolation approach as sleeve connections
    def create_interpolated_points(edges, num_points=8):
        edges.sort(key=lambda e: min(e['v1_world'].y, e['v2_world'].y))
        
        all_y_coords = []
        for edge in edges:
            all_y_coords.extend([edge['v1_world'].y, edge['v2_world'].y])
        
        y_min = min(all_y_coords)
        y_max = max(all_y_coords)
        
        interpolated_points = []
        
        for i in range(num_points):
            if num_points == 1:
                target_y = (y_min + y_max) / 2
            else:
                t = i / (num_points - 1)
                target_y = y_min + t * (y_max - y_min)
            
            best_point = None
            for edge in edges:
                v1, v2 = edge['v1_world'], edge['v2_world']
                edge_y_min = min(v1.y, v2.y)
                edge_y_max = max(v1.y, v2.y)
                
                if edge_y_min <= target_y <= edge_y_max:
                    if abs(v2.y - v1.y) > 0.001:
                        t_edge = (target_y - v1.y) / (v2.y - v1.y)
                        t_edge = max(0, min(1, t_edge))
                        best_point = v1 + t_edge * (v2 - v1)
                        break
            
            if best_point is None:
                min_dist = float('inf')
                for edge in edges:
                    for vertex in [edge['v1_world'], edge['v2_world']]:
                        dist = abs(vertex.y - target_y)
                        if dist < min_dist:
                            min_dist = dist
                            best_point = vertex
            
            if best_point:
                interpolated_points.append(best_point)
        
        return interpolated_points
    
    # Create interpolated points for hood and panel edges
    num_stitches = 6
    hood_points = create_interpolated_points(hood_edges, num_stitches)
    panel_points = create_interpolated_points(panel_edges, num_stitches)
    
    
    # Create springs connecting hood to panel
    num_connections = min(len(hood_points), len(panel_points))
    
    for i in range(num_connections):
        hood_point = hood_points[i]
        panel_point = panel_points[i]
        
        
        all_spring_verts.extend([hood_point, panel_point])
        all_spring_edges.append([vert_index, vert_index + 1])
        vert_index += 2
    
    # Create mesh
    spring_mesh.from_pydata(all_spring_verts, all_spring_edges, [])
    spring_mesh.update()
    
    # Add material (unique color for hood connections)
    mat = bpy.data.materials.new(name=f"SewingSpring_Hood_To_Panel_Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.4, 1, 1)  # Purple
    spring_obj.data.materials.append(mat)
    
    # Set display
    spring_obj.display_type = 'WIRE'
    spring_obj.show_wire = True
    

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
        
        # Reset sleeve counter to fix positioning on subsequent loads
        if hasattr(create_mesh_from_coordinates, 'sleeve_counter'):
            create_mesh_from_coordinates.sleeve_counter = 0
        
        defaults = get_garment_defaults(props.garment_type)
        if not defaults:
            self.report({'ERROR'}, f"No defaults found for {props.garment_type}")
            return {'CANCELLED'}
        
        # Create FashionSynth collection if it doesn't exist
        if "FashionSynth" not in bpy.data.collections:
            fashion_collection = bpy.data.collections.new("FashionSynth")
            bpy.context.scene.collection.children.link(fashion_collection)
        
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
        for obj in bpy.data.objects:
            if "sleeve_cuff" in obj.name.lower():
                position_sleeve_cuff_next_to_sleeve(obj)
        
        # Set up sewing connections after all pieces are positioned
        setup_hood_center_seam()
        setup_sleeve_cuff_seams()
        setup_front_back_panel_seams()
        setup_waist_band_seam()
        setup_pocket_seam()
        setup_neck_binding_seam()
        setup_shoulder_seams()
        setup_sleeve_horizontal_seams()
        setup_sleeve_cuff_horizontal_seams()
        setup_hood_to_panel_connection()
        setup_sleeve_to_panel_connection()
        
        return {'FINISHED'}

class FASHIONSYNTH_OT_load_custom(Operator):
    bl_idname = "fashionsynth.load_custom"
    bl_label = "Load Custom Files"
    bl_description = "Load custom SVG files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.fashionsynth_props
        
        # Reset sleeve counter to fix positioning on subsequent loads
        if hasattr(create_mesh_from_coordinates, 'sleeve_counter'):
            create_mesh_from_coordinates.sleeve_counter = 0
        
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
        
        return {'FINISHED'}

class FASHIONSYNTH_OT_clear_scene(Operator):
    bl_idname = "fashionsynth.clear_scene"
    bl_label = "Clear Scene"
    bl_description = "Clear all objects from scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Reset sleeve counter when clearing scene
        if hasattr(create_mesh_from_coordinates, 'sleeve_counter'):
            create_mesh_from_coordinates.sleeve_counter = 0
        
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)
        
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