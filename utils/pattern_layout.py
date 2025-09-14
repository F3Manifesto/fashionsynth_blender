"""
Professional pattern layout system for garment pieces
"""
import bpy
import mathutils

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
    
    print(f"\nArranging {len(created_meshes)} pieces in professional pattern layout...")
    
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
    
    print(f"Part groups: {list(part_groups.keys())}")
    
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
    
    print(f"Grid spacing: X={spacing_x:.2f}, Z={spacing_z:.2f}")
    
    positioned_parts = set()
    
    for part_name, meshes in part_groups.items():
        layout_rule = None
        
        if part_name in layout_rules:
            layout_rule = layout_rules[part_name]
        elif f"{part_name}_1" in layout_rules:
            layout_rule = layout_rules[f"{part_name}_1"]
        elif f"{part_name}_2" in layout_rules:
            layout_rule = layout_rules[f"{part_name}_2"]
        elif "sleeve" in part_name and part_name != "sleeve_cuff":
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
                
                print(f"Positioned {mesh.name} at ({mesh.location.x:.2f}, {mesh.location.z:.2f})")
        else:
            print(f"No layout rule for {part_name}, using fallback position")
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
    
    print("Pattern layout complete!")

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