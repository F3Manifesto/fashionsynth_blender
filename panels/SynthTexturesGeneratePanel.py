import bpy

class SynthTexturesGeneratePanel(bpy.types.Panel):
    bl_label="Textures Panel"
    bl_idname="SYNTH_PT_Generate"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Fashion Synth"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text="Pattern Textures & Prints")