import bpy

class SynthIRLSewingPanel(bpy.types.Panel):
    bl_label="IRL Sewing Panel"
    bl_idname="SYNTH_PT_Sewing"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Fashion Synth"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text="IRL Sewing Patterns")