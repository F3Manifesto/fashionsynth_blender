bl_info = {
    "name": "FashionSynth",
    "author": "Emma-Jane MacKinnon-Lee",
    "version": (1,0),
    "blender": (3,2,2),
    "location": "View3D > Sidebar > Fashion Synth",
    "warning": "Testing in Prod",
    "wiki_url": "diysynth.xyz",
    "Category": "Development"
}

import bpy
import importlib
import os
import tempfile
constants = os.path.join(os.path.dirname(bpy.data.filepath), "/Users/devdesign/Documents/Blender Scripting/fashionsynth/constants.py")


class SynthUserInputs(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(name="Enter Prompt", default="", description="A close up center front view 2012 studio photograph of an orange and black racing bomber jacket with logo patches")
    main: bpy.props.EnumProperty(name="Select the Main Fashion Item", default="wm.jacket", description="Choose from the Pattern Options", items=[("wm.jacket", "Jacket", "This is Jacket"), ("wm.skirt", "Skirt", "This is Skirt")])
    scale: bpy.props.FloatProperty(name="Enter Guidance Scale", default=10, min=6)
    steps: bpy.props.FloatProperty(name="Enter Number of Steps", default=75, max=200, min=50)
    init: bpy.props.BoolProperty(name="Do you have an input image?", default=False)
    path: bpy.props.StringProperty(name="Save Images Path", description="Specify Save Path", subtype="DIR_PATH", default=tempfile.gettempdir())


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
        
class SynthInputPrompt(bpy.types.Operator):
    bl_label="Input Prompt"
    bl_idname="wm.inputprompt"
    
    def execute(self, context):
        user_input = constants.UserInput(
            prompt = bpy.context.scene.input_tool.prompt,
            main = bpy.context.scene.input_tool.main,
            scale = bpy.context.scene.input_tool.scale,
            steps = bpy.context.scene.input_tool.steps,
            init = bpy.context.scene.input_tool.init,
            path = bpy.path.abspath(bpy.context.scene.input_tool.path),
        )
        
        if not user_input.prompt:
            self.report({"ERROR"}, "Make sure to enter a prompt!")
            return {"CANCELLED"}
        
        if not user_input.main:
            self.report({"ERROR"}, "Make sure to specify main pattern!")
            return {"CANCELLED"}
        
        return {'FINISHED'}
        
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
        
class SynthInstallPackages(bpy.types.Operator):
    bl_label = "Install Packages"
    bl_idname = "wm.installpackages"
    
    def execute(self,context):
        bpy.types.Scene.input_tool = bpy.props.PointerProperty(
            type=SynthUserInputs
        )
        
        return {"FINISHED"}
    
classes = [SynthInstallPackages, SynthRunPromptPanel, SynthPatternDetectionPanel, SynthPatternMeshesPanel, SynthTexturesGeneratePanel, SynthIRLSewingPanel, SynthInputPrompt]
bpy.utils.register_class(SynthUserInputs)

def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=SynthUserInputs)
        
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.input_tool


if __name__ == "__main__":
    register()
#    unregister()