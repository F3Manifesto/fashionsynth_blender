import bpy

class SynthPatternDetectionPanel(bpy.types.Panel):
    bl_label="Pattern Detection Panel"
    bl_idname="SYNTH_PT_Detection"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Fashion Synth"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text="Run Pattern Detection")