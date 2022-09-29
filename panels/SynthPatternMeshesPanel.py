import bpy

class SynthPatternMeshesPanel(bpy.types.Panel):
    bl_label="Pattern Meshes Panel"
    bl_idname="SYNTH_PT_Meshes"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Fashion Synth"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text="Pattern Meshes")
        
        # function here that imports the mesh with stitching into the scene i.e the operator of add pattern