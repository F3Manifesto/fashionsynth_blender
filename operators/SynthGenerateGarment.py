import bpy
import os
import urllib.request
import json
from bpy.types import Operator
from ..constants.garment_defaults import get_garment_defaults, ipfs_to_gateway_url
from ..utils.svg_processor import get_coordinates_from_ipfs, get_coordinates_from_file
from ..utils.mesh_creator import create_mesh_from_coordinates, markSeam, addStitching
from ..utils.pattern_layout import arrange_pattern_layout

class SynthGenerateGarment(Operator):
    bl_idname = "synth.generate_garment"
    bl_label = "Generate Garment"
    bl_description = "Generate a 3D garment from SVG patterns"
    
    def execute(self, context):
        props = context.scene.synth_garment_props
        
        print(f"Generating {props.garment_type}...")
        print(f"Using Coin Op SVGs: {props.use_default_svgs}")
        
        if props.use_default_svgs:
            self.generate_with_defaults(props.garment_type)
        else:
            self.generate_with_custom_svgs(props)
            
        return {'FINISHED'}
    
    def generate_with_defaults(self, garment_type):
        print("="*50)
        print("STARTING GENERATE WITH DEFAULTS")
        print("="*50)
        
        # Get IPFS-based defaults for the garment type
        defaults = get_garment_defaults(garment_type)
        print(f"Got {len(defaults)} parts for {garment_type}")
        
        if not defaults:
            self.report({'ERROR'}, f"No default patterns found for {garment_type}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Generating {garment_type} with IPFS default patterns...")
        
        # Create collection for this garment
        collection_name = f"{garment_type}_pattern"
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        
        # Process each part
        total_pieces = 0
        created_meshes = []
        panel_meshes = []
        pocket_meshes = []
        sleeve_meshes = []
        cuff_meshes = []
        waistband_meshes = []
        hood_meshes = []
        
        for part_index, (part_name, part_data) in enumerate(defaults.items()):
            ipfs_hash = part_data.get("ipfs", "")
            quantity = part_data.get("quantity", 1)
            display_name = part_data.get("display_name", part_name.replace("_", " ").title())
            description = part_data.get("description", f"{display_name} pattern piece")
            
            print(f"\nProcessing: {display_name} ({part_name})")
            print(f"  IPFS: {ipfs_hash}")
            print(f"  Quantity: {quantity}")
            print(f"  Description: {description}")
            
            # Convert IPFS to gateway URL
            gateway_url = ipfs_to_gateway_url(ipfs_hash)
            print(f"  Gateway URL: {gateway_url}")
            
            # Get coordinates from IPFS SVG
            coordinates = get_coordinates_from_ipfs(ipfs_hash, gateway_url)
            
            # If IPFS fails, try with test coordinates
            if not coordinates and part_name == "front_panel":
                print(f"  Using test coordinates for {part_name}")
                # Simple rectangle for testing
                coordinates = [0, 0, 100, 0, 100, 150, 0, 150]
            
            if not coordinates:
                print(f"  WARNING: Could not get coordinates for {part_name}, creating placeholder")
                # Create placeholder cube if no coordinates
                for i in range(quantity):
                    bpy.ops.mesh.primitive_plane_add()
                    obj = bpy.context.active_object
                    obj.name = f"{garment_type}_{part_name}_{i+1}"
                    obj.location.x = part_index * 3
                    obj.location.y = i * 2
                    created_meshes.append(obj)
            else:
                # Create mesh from coordinates
                for i in range(quantity):
                    mesh_name = f"{garment_type}_{part_name}_{i+1}"
                    mesh_obj = create_mesh_from_coordinates(
                        coordinates, 
                        mesh_name, 
                        collection_name
                        # Auto-detect scale factor based on coordinate values
                    )
                    
                    if mesh_obj:
                        # Apply seam marking
                        markSeam(mesh_obj)
                        
                        # Add stitching detail (optional, comment out if too slow)
                        # addStitching(mesh_obj, subdivisions=2)
                        
                        created_meshes.append(mesh_obj)
                        
                        if part_name == 'front_panel' or part_name == 'back_panel':
                            panel_meshes.append((mesh_obj, part_name, i))
                        elif part_name == 'pocket':
                            pocket_meshes.append((mesh_obj, part_name, i))
                        elif part_name == 'sleeve_cuff':
                            cuff_meshes.append((mesh_obj, part_name, i))
                        elif part_name == 'sleeve':
                            sleeve_meshes.append((mesh_obj, part_name, i))
                        elif part_name == 'waist_band':
                            waistband_meshes.append((mesh_obj, part_name, i))
                        elif part_name == 'hood':
                            hood_meshes.append((mesh_obj, part_name, i))
                        
                        total_pieces += 1
                    else:
                        print(f"  ERROR: Could not create mesh for {mesh_name}")
        
        # Apply intelligent panel positioning first
        if panel_meshes:
            print("\nApplying intelligent panel positioning...")
            self.position_panels_intelligently(panel_meshes)
        
        # Position pockets on front panel
        if pocket_meshes and panel_meshes:
            print("\nPositioning pockets on front panel...")
            self.position_pockets_on_front_panel(pocket_meshes, panel_meshes)
        
        if sleeve_meshes:
            print("\nPositioning sleeves...")
            self.position_sleeves(sleeve_meshes)
        
        if cuff_meshes and sleeve_meshes:
            print("\nPositioning cuffs under sleeves...")
            self.position_cuffs_under_sleeves(cuff_meshes, sleeve_meshes)
        
        if waistband_meshes and panel_meshes:
            print("\nPositioning waistband under front panel...")
            self.position_waistband_under_front_panel(waistband_meshes, panel_meshes)
        
        if hood_meshes:
            print("\nPositioning hood pieces side by side...")
            self.position_hood_pieces_together(hood_meshes)
        
        remaining_meshes = []
        for m in created_meshes:
            is_panel = any('panel' in m.name for _, part_name, _ in panel_meshes)
            is_pocket = any('pocket' in m.name for _, part_name, _ in pocket_meshes)
            is_sleeve = any('sleeve' in m.name for _, part_name, _ in sleeve_meshes)
            is_cuff = any('cuff' in m.name for _, part_name, _ in cuff_meshes)
            is_waistband = any('waist' in m.name for _, part_name, _ in waistband_meshes)
            is_hood = any('hood' in m.name for _, part_name, _ in hood_meshes)
            if not (is_panel or is_pocket or is_sleeve or is_cuff or is_waistband or is_hood):
                remaining_meshes.append(m)
        
        if remaining_meshes:
            print("\nApplying layout for remaining pieces...")
            arrange_pattern_layout(remaining_meshes, garment_type)
        
        self.report({'INFO'}, f"Created {garment_type} with {total_pieces} pieces from IPFS patterns")
        print(f"\nTotal meshes created: {len(created_meshes)}")
    
    def position_panels_intelligently(self, panel_meshes):
        """Position front and back panels front-to-back (not side-to-side)"""
        print(f"Positioning {len(panel_meshes)} panels front-to-back")
        
        front_panels = []
        back_panels = []
        
        # Separate front and back panels
        for mesh_obj, part_name, index in panel_meshes:
            if 'front' in part_name.lower():
                front_panels.append((mesh_obj, index))
            elif 'back' in part_name.lower():
                back_panels.append((mesh_obj, index))
        
        print(f"Found {len(front_panels)} front panels, {len(back_panels)} back panels")
        
        front_y_pos = -1.0
        for i, (mesh_obj, index) in enumerate(front_panels):
            mesh_obj.location.x = 0
            mesh_obj.location.y = front_y_pos
            mesh_obj.location.z = i * 0.5
            
            mesh_obj.rotation_euler[0] = 0
            mesh_obj.rotation_euler[1] = 0 
            mesh_obj.rotation_euler[2] = 0
            
            print(f"Positioned front panel {mesh_obj.name} at (0, {mesh_obj.location.y}, {mesh_obj.location.z})")
        
        back_y_pos = 1.0
        for i, (mesh_obj, index) in enumerate(back_panels):
            mesh_obj.location.x = 0
            mesh_obj.location.y = back_y_pos
            mesh_obj.location.z = i * 0.5
            
            mesh_obj.rotation_euler[0] = 0
            mesh_obj.rotation_euler[1] = 0
            mesh_obj.rotation_euler[2] = 0
            
            print(f"Positioned back panel {mesh_obj.name} at (0, {mesh_obj.location.y}, {mesh_obj.location.z})")
        
        print("Panel positioning complete!")
    
    def position_pockets_on_front_panel(self, pocket_meshes, panel_meshes):
        # BLENDER COORDINATE SYSTEM:
        # X = left(-) / right(+)
        # Y = front(-) / back(+) 
        # Z = down(-) / up(+)
        print(f"Positioning {len(pocket_meshes)} pockets on front panel")
        
        front_panel_mesh = None
        for mesh_obj, part_name, index in panel_meshes:
            if 'front' in part_name.lower():
                front_panel_mesh = mesh_obj
                break
        
        if not front_panel_mesh:
            print("No front panel found for pocket positioning")
            return
        
        print(f"Front panel location: {front_panel_mesh.location}")
        
        for i, (mesh_obj, part_name, index) in enumerate(pocket_meshes):
            mesh_obj.location.x = front_panel_mesh.location.x
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
                
                print(f"Panel bottom: {panel_bottom_world_z:.2f}")
                print(f"Pocket bottom: {pocket_bottom_world_z:.2f}")  
                print(f"Pocket center: {pocket_center_z:.2f}")
            else:
                mesh_obj.location.z = front_panel_mesh.location.z + 0.5
            
            mesh_obj.rotation_euler[0] = 0
            mesh_obj.rotation_euler[1] = 0
            mesh_obj.rotation_euler[2] = 0
            
            print(f"Positioned pocket {mesh_obj.name} at ({mesh_obj.location.x:.2f}, {mesh_obj.location.y:.2f}, {mesh_obj.location.z:.2f})")
        
        print("Pocket positioning complete!")
    
    def position_sleeves(self, sleeve_meshes):
        # BLENDER COORDINATE SYSTEM:
        # X = left(-) / right(+)
        # Y = front(-) / back(+) 
        # Z = down(-) / up(+)
        print(f"Positioning {len(sleeve_meshes)} sleeves")
        
        for i, (mesh_obj, part_name, index) in enumerate(sleeve_meshes):
            if i == 0:
                mesh_obj.location.x = -4.0
            else:
                mesh_obj.location.x = 4.0
            
            mesh_obj.location.y = 0
            mesh_obj.location.z = 2.0
            
            mesh_obj.rotation_euler[0] = 0
            mesh_obj.rotation_euler[1] = 0
            mesh_obj.rotation_euler[2] = 0
            
            print(f"Positioned sleeve {mesh_obj.name} at ({mesh_obj.location.x}, {mesh_obj.location.y}, {mesh_obj.location.z})")
        
        print("Sleeve positioning complete!")
    
    def position_cuffs_under_sleeves(self, cuff_meshes, sleeve_meshes):
        # BLENDER COORDINATE SYSTEM:
        # X = left(-) / right(+)
        # Y = front(-) / back(+) 
        # Z = down(-) / up(+)
        print(f"Positioning {len(cuff_meshes)} cuffs under {len(sleeve_meshes)} sleeves")
        
        for i, (cuff_mesh, cuff_part_name, cuff_index) in enumerate(cuff_meshes):
            if cuff_part_name == "sleeve_cuff" and i < len(sleeve_meshes):
                sleeve_mesh, sleeve_part_name, sleeve_index = sleeve_meshes[i]
                
                cuff_mesh.location.x = sleeve_mesh.location.x
                cuff_mesh.location.y = sleeve_mesh.location.y
                
                sleeve_verts = sleeve_mesh.data.vertices
                cuff_verts = cuff_mesh.data.vertices
                
                if sleeve_verts and cuff_verts:
                    sleeve_min_z = min(v.co.z for v in sleeve_verts)
                    sleeve_bottom_world_z = sleeve_mesh.location.z + sleeve_min_z
                    
                    cuff_max_z = max(v.co.z for v in cuff_verts)
                    
                    gap_between_sleeve_and_cuff = 0.05
                    cuff_top_world_z = sleeve_bottom_world_z - gap_between_sleeve_and_cuff
                    cuff_center_z = cuff_top_world_z - cuff_max_z
                    
                    cuff_mesh.location.z = cuff_center_z
                else:
                    cuff_mesh.location.z = sleeve_mesh.location.z - 1.0
                
                cuff_mesh.rotation_euler[0] = 0
                cuff_mesh.rotation_euler[1] = 0
                cuff_mesh.rotation_euler[2] = 0
                
                print(f"Aligned cuff {cuff_mesh.name} longest edge under sleeve {sleeve_mesh.name} bottom")
            else:
                cuff_mesh.location.x = 0
                cuff_mesh.location.y = 0
                cuff_mesh.location.z = -2.0
                
                print(f"No matching sleeve for cuff {cuff_mesh.name}, positioned at origin")
        
        print("Cuff positioning complete!")
    
    def position_waistband_under_front_panel(self, waistband_meshes, panel_meshes):
        # BLENDER COORDINATE SYSTEM:
        # X = left(-) / right(+)
        # Y = front(-) / back(+) 
        # Z = down(-) / up(+)
        print(f"Positioning {len(waistband_meshes)} waistbands under front panel")
        
        front_panel_mesh = None
        for mesh_obj, part_name, index in panel_meshes:
            if 'front' in part_name.lower():
                front_panel_mesh = mesh_obj
                break
        
        if not front_panel_mesh:
            print("No front panel found for waistband positioning")
            return
        
        for i, (waistband_mesh, waistband_part_name, waistband_index) in enumerate(waistband_meshes):
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
                
                print(f"Front panel bottom: {front_panel_bottom_world_z:.2f}")
                print(f"Waistband top aligned: {waistband_top_world_z:.2f}")
                print(f"Waistband center: {waistband_center_z:.2f}")
            else:
                waistband_mesh.location.z = front_panel_mesh.location.z - 1.0
            
            waistband_mesh.rotation_euler[0] = 0
            waistband_mesh.rotation_euler[1] = 0
            waistband_mesh.rotation_euler[2] = 0
            
            print(f"Aligned waistband {waistband_mesh.name} longest edge under front panel bottom")
        
        print("Waistband positioning complete!")
    
    def position_hood_pieces_together(self, hood_meshes):
        # BLENDER COORDINATE SYSTEM:
        # X = left(-) / right(+)
        # Y = front(-) / back(+) 
        # Z = down(-) / up(+)
        print(f"Positioning {len(hood_meshes)} hood pieces side by side")
        
        if len(hood_meshes) < 2:
            print("Need at least 2 hood pieces to position together")
            return
        
        first_hood = hood_meshes[0][0]
        second_hood = hood_meshes[1][0]
        
        first_hood.location.y = 6.0
        first_hood.location.z = 0
        second_hood.location.y = 6.0
        second_hood.location.z = 0
        
        first_hood_verts = first_hood.data.vertices
        second_hood_verts = second_hood.data.vertices
        
        if first_hood_verts and second_hood_verts:
            first_hood_max_x = max(v.co.x for v in first_hood_verts)
            second_hood_min_x = min(v.co.x for v in second_hood_verts)
            
            gap_between_pieces = 0.01
            
            first_hood_right_edge_world = first_hood.location.x + first_hood_max_x
            second_hood_left_edge_world_target = first_hood_right_edge_world + gap_between_pieces
            second_hood_center_x = second_hood_left_edge_world_target - second_hood_min_x
            
            first_hood.location.x = 0
            second_hood.location.x = second_hood_center_x
            
            print(f"First hood right edge: {first_hood_right_edge_world:.2f}")
            print(f"Second hood left edge target: {second_hood_left_edge_world_target:.2f}")
            print(f"Hood pieces gap: {gap_between_pieces:.2f}")
        else:
            first_hood.location.x = -2.0
            second_hood.location.x = 2.0
        
        first_hood.rotation_euler[0] = 0
        first_hood.rotation_euler[1] = 0
        first_hood.rotation_euler[2] = 0
        
        second_hood.rotation_euler[0] = 0
        second_hood.rotation_euler[1] = 0
        second_hood.rotation_euler[2] = 3.14159
        
        print(f"Positioned hood pieces with straight edges touching")
        print("Hood positioning complete!")
    
    def generate_with_custom_svgs(self, props):
        garment_type = props.garment_type
        
        if garment_type == "hoodie":
            svg_paths = {
                "front": props.hoodie_front_svg,
                "back": props.hoodie_back_svg,
                "sleeve_left": props.hoodie_sleeve_left_svg,
                "sleeve_right": props.hoodie_sleeve_right_svg,
                "hood": props.hoodie_hood_svg,
                "pocket": props.hoodie_pocket_svg
            }
        elif garment_type == "tshirt":
            svg_paths = {
                "front": props.tshirt_front_svg,
                "back": props.tshirt_back_svg,
                "sleeve_left": props.tshirt_sleeve_left_svg,
                "sleeve_right": props.tshirt_sleeve_right_svg
            }
        
        # Validate that SVG files exist
        missing_files = []
        for part, path in svg_paths.items():
            if not path or not os.path.exists(path):
                missing_files.append(part)
        
        if missing_files:
            self.report({'ERROR'}, f"Missing SVG files for: {', '.join(missing_files)}")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Generating {garment_type} with custom SVGs...")
        # TODO: Implement custom SVG processing

def register():
    bpy.utils.register_class(SynthGenerateGarment)

def unregister():
    bpy.utils.unregister_class(SynthGenerateGarment)