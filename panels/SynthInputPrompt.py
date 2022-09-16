import bpy
from constants import constants

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