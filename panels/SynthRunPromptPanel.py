import bpy

class SynthRunPromptPanel(bpy.types.Panel):
    bl_label="Run Synth Panel"
    bl_idname="SYNTH_PT_Run"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Fashion Synth"
    
    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool
        
        row = layout.row()       
        row.label(text="Conduct Synthesis", icon="SORTTIME")
        row = layout.row()  
        row.prop(input_tool, "prompt")
        
        row = layout.row()
        row.prop(input_tool, "main")
        
        row = layout.row()
        row.prop(input_tool, "scale")
        
        row = layout.row()
        row.prop(input_tool, "steps")
        
        row = layout.row()
        row.prop(input_tool, "init")
        
        layout.separator()
        
        layout.operator("wm.inputprompt", text="Synth")
        
        layout.separator()