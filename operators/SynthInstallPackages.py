import bpy
from panels.SynthUserInputs import SynthUserInputs

class SynthInstallPackages(bpy.types.Operator):
    bl_label = "Install Packages"
    bl_idname = "wm.installpackages"
    
    def execute(self,context):
        bpy.types.Scene.input_tool = bpy.props.PointerProperty(
            type=SynthUserInputs
        )
        
        return {"FINISHED"}