import bpy
from bpy.types import Panel, PropertyGroup
from bpy.props import EnumProperty, StringProperty, BoolProperty

class SynthGarmentProperties(PropertyGroup):
    garment_type: EnumProperty(
        name="Garment Type",
        description="Select the type of garment to create",
        items=[
            ("hoodie", "Hoodie", "Create a hoodie with hood, sleeves, front and back panels"),
            ("tshirt", "T-Shirt", "Create a t-shirt with sleeves, front and back panels")
        ],
        default="hoodie"
    )
    
    use_default_svgs: BoolProperty(
        name="Use Coin Op SVGs",
        description="Use built-in Coin Op SVG patterns for the selected garment",
        default=True
    )
    
    hoodie_front_svg: StringProperty(
        name="Front Panel SVG",
        description="Path to front panel SVG file",
        subtype="FILE_PATH"
    )
    
    hoodie_back_svg: StringProperty(
        name="Back Panel SVG", 
        description="Path to back panel SVG file",
        subtype="FILE_PATH"
    )
    
    hoodie_sleeve_left_svg: StringProperty(
        name="Left Sleeve SVG",
        description="Path to left sleeve SVG file", 
        subtype="FILE_PATH"
    )
    
    hoodie_sleeve_right_svg: StringProperty(
        name="Right Sleeve SVG",
        description="Path to right sleeve SVG file",
        subtype="FILE_PATH"
    )
    
    hoodie_hood_svg: StringProperty(
        name="Hood SVG",
        description="Path to hood SVG file",
        subtype="FILE_PATH"
    )
    
    hoodie_pocket_svg: StringProperty(
        name="Pocket SVG",
        description="Path to pocket SVG file",
        subtype="FILE_PATH"
    )
    
    tshirt_front_svg: StringProperty(
        name="Front Panel SVG",
        description="Path to front panel SVG file",
        subtype="FILE_PATH"
    )
    
    tshirt_back_svg: StringProperty(
        name="Back Panel SVG",
        description="Path to back panel SVG file", 
        subtype="FILE_PATH"
    )
    
    tshirt_sleeve_left_svg: StringProperty(
        name="Left Sleeve SVG",
        description="Path to left sleeve SVG file",
        subtype="FILE_PATH"
    )
    
    tshirt_sleeve_right_svg: StringProperty(
        name="Right Sleeve SVG", 
        description="Path to right sleeve SVG file",
        subtype="FILE_PATH"
    )

class SynthGarmentUploadPanel(Panel):
    bl_label = "Garment Upload"
    bl_idname = "SYNTH_PT_GarmentUpload" 
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Fashion Synth"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.synth_garment_props
        
        layout.prop(props, "garment_type")
        
        layout.prop(props, "use_default_svgs")
        
        if not props.use_default_svgs:
            layout.separator()
            layout.label(text="Upload Custom SVGs:")
            
            from ..constants.garment_defaults import get_garment_defaults
            defaults = get_garment_defaults(props.garment_type)
            
            for part_name, part_data in defaults.items():
                display_name = part_data.get("display_name", part_name.replace("_", " ").title())
                quantity = part_data.get("quantity", 1)
                description = part_data.get("description", f"{display_name} pattern piece")
                
                layout.label(text=f"{display_name} (Qty: {quantity})")
                
                prop_name = f"{props.garment_type}_{part_name}_svg"
                if hasattr(props, prop_name):
                    layout.prop(props, prop_name, text="SVG File")
        
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("synth.generate_garment", text="Generate Garment")

def register():
    bpy.utils.register_class(SynthGarmentProperties)
    bpy.utils.register_class(SynthGarmentUploadPanel)
    bpy.types.Scene.synth_garment_props = bpy.props.PointerProperty(type=SynthGarmentProperties)

def unregister():
    bpy.utils.unregister_class(SynthGarmentUploadPanel)
    bpy.utils.unregister_class(SynthGarmentProperties)
    del bpy.types.Scene.synth_garment_props