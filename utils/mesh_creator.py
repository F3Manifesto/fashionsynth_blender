import bpy
import bmesh
import mathutils
import math

def selectAll(vertices):
    for vert in vertices:
        vert.select = True

def unSelectAll(vertices):
    for vert in vertices:
        vert.select = False

def detect_bottom_and_fold_edges(coordinates):
    """Detect shortest edge (bottom) and longest edge (fold line) with required rotations
    
    In Blender mapping: SVG X -> Blender X, SVG Y -> Blender Z
    We want shortest edge to face DOWN on Blender Z-axis (negative Z)
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
        print("Less than 2 straight edges found, using defaults")
        return 'svg_horizontal', 'svg_vertical', 0
    
    shortest_edge = min(straight_edges, key=lambda x: x[1])
    bottom_orientation, bottom_length, _, _ = shortest_edge
    
    longest_edge = max(straight_edges, key=lambda x: x[1])
    fold_orientation, fold_length, _, _ = longest_edge
    
    print(f"SHORTEST edge (bottom): {bottom_orientation}, length: {bottom_length:.2f}")
    print(f"LONGEST edge (fold line): {fold_orientation}, length: {fold_length:.2f}")
    
 
    rotation_needed = 0
    if bottom_orientation == 'svg_vertical':
        rotation_needed = 90
        fold_orientation = 'svg_horizontal' if fold_orientation == 'svg_vertical' else 'svg_vertical'
        bottom_orientation = 'svg_horizontal'  
    
    print(f"Rotation needed: {rotation_needed}° to make shortest edge horizontal (bottom)")
    return bottom_orientation, fold_orientation, rotation_needed

def rotate_coordinates(coordinates, rotation_degrees):
    """Rotate coordinates by specified degrees around center"""
    if rotation_degrees == 0:
        return coordinates
    
    print(f"Rotating coordinates by {rotation_degrees} degrees")
    
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
        print(f"Bottom edge found: length {max_length}")
        return longest_horizontal_line
    return None

def orient_pocket_coordinates(coordinates, part_name):
    if 'pocket' not in part_name.lower():
        return coordinates
    
    print(f"Orienting pocket for {part_name}")
    
    bottom_orientation, fold_orientation, rotation_needed = detect_bottom_and_fold_edges(coordinates)
    
    if rotation_needed != 0:
        coordinates = rotate_coordinates(coordinates, rotation_needed)
        print(f"Rotated pocket {rotation_needed}° to make shortest edge the bottom")
    
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
            print(f"Shortest edge was at top in SVG, flipped 180° for Blender")
        else:
            print(f"Shortest edge was at bottom in SVG, no flip needed")
    
    print(f"Pocket orientation complete - shortest edge facing down in Blender")
    return coordinates

def orient_sleeve_coordinates(coordinates, part_name):
    if 'sleeve' not in part_name.lower() or 'cuff' in part_name.lower():
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
    
    print(f"Orienting cuff for {part_name}")
    
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
        print("Less than 2 straight edges found for cuff")
        return coordinates
    
    longest_edge = max(straight_edges, key=lambda x: x[1])
    longest_orientation, longest_length, p1, p2 = longest_edge
    
    print(f"LONGEST cuff edge: {longest_orientation}, length: {longest_length:.2f}")
    
    rotation_needed = 0
    if longest_orientation == 'svg_vertical':
        rotation_needed = 90
        print(f"Longest edge is vertical, rotating 90° to make it horizontal (bottom)")
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
            print(f"Longest edge was at top in SVG, flipped 180° for Blender")
        else:
            print(f"Longest edge was at bottom in SVG, no flip needed")
    
    print(f"Cuff orientation complete - longest edge facing down in Blender")
    return coordinates

def orient_waistband_coordinates(coordinates, part_name):
    if 'waist' not in part_name.lower():
        return coordinates
    
    print(f"Orienting waistband for {part_name}")
    
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
        
        print(f"LONGEST edge (waistband opening): {longest_orientation}, length: {longest_length:.2f}")
        
        if longest_orientation == 'svg_vertical':
            coordinates = rotate_coordinates(coordinates, 90)
            print(f"Rotated waistband 90° to make longest edge horizontal")
        
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
                print(f"Longest edge was at bottom, flipped 180° to face down in Blender")
            else:
                print(f"Longest edge was at top, will face down in Blender")
    
    print(f"Waistband orientation complete - longest edge facing down in Blender")
    return coordinates

def create_full_panel_coordinates(coordinates, part_name):
    """Create full panel by mirroring - ONLY FOR PANELS"""
    if 'panel' not in part_name.lower():
        if 'pocket' in part_name.lower():
            return orient_pocket_coordinates(coordinates, part_name)
        elif 'sleeve' in part_name.lower():
            return orient_sleeve_coordinates(coordinates, part_name)
        elif 'cuff' in part_name.lower():
            return orient_cuff_coordinates(coordinates, part_name)
        elif 'waist' in part_name.lower():
            return orient_waistband_coordinates(coordinates, part_name)
        elif 'hood' in part_name.lower():
            return orient_pocket_coordinates(coordinates, part_name)
        return coordinates
    
    print(f"Creating full panel for {part_name}")
    
    bottom_orientation, fold_orientation, rotation_needed = detect_bottom_and_fold_edges(coordinates)
    
    if rotation_needed != 0:
        coordinates = rotate_coordinates(coordinates, rotation_needed)
        print(f"Rotated panel {rotation_needed}° to make shortest edge the bottom")
    
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
        
        print(f"LONGEST edge (fold line): {longest_orientation}, length: {longest_length:.2f}")
        
        if longest_orientation == 'horizontal':
            fold_y = (longest_p1[1] + longest_p2[1]) / 2
            print(f"Mirroring across HORIZONTAL fold line at y={fold_y}")
            
            mirrored_points = []
            for x, y in points:
                mirrored_y = 2 * fold_y - y
                mirrored_points.append((x, mirrored_y))
        else:
            fold_x = (longest_p1[0] + longest_p2[0]) / 2
            print(f"Mirroring across VERTICAL fold line at x={fold_x}")
            
            mirrored_points = []
            for x, y in points:
                mirrored_x = 2 * fold_x - x
                mirrored_points.append((mirrored_x, y))
    else:
        print("Not enough straight edges found for mirroring")
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
            print(f"Shortest edge was at top, flipped panel 180° for Blender")
        else:
            print(f"Shortest edge was at bottom, no flip needed")
    
    print(f"Original points: {len(points)}, Full panel points: {len(full_points)}")
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
        print(f"Not enough coordinates for {part_name}: {len(coordinates)}")
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
        print(f"Auto-detected scale factor: {scale_factor} (max coord: {max_coord})")
    

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
        
        print(f"Centering mesh - offset: ({center_x:.2f}, 0, {center_z:.2f})")
        
        for v in newVerts:
            v.x -= center_x
            v.z -= center_z
    
    print(f"Creating mesh '{part_name}' with {len(newVerts)} vertices")
    
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
    
    try:
        bpy.ops.mesh.mark_seam(clear=False)
    except:
        print("Could not mark seams")
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return mesh_obj

def addStitching(mesh_obj, subdivisions=5):
    """
    Add stitching by subdividing mesh
    """
    if not mesh_obj:
        return None
        
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    try:
        bpy.ops.mesh.subdivide(number_cuts=subdivisions)
    except Exception as e:
        print(f"Could not add stitching: {e}")
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return mesh_obj