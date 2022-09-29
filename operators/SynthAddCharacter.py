import bpy
import os 

path_file = os.path.join(os.path.dirname(bpy.data.filepath), "/Users/devdesign/Documents/BlenderScripting/fashionsynth/operators/Character.fbx")

class SynthAnimation(bpy.types.Panel):
    bl_label="Animation"
    bl_idname="READ_PT_Animation"
    bl_space_type = "VIEW_3D"
    bl_region_type="UI"
    bl_category="Animation"

    def draw(self, context):
        layout = self.layout 
        
        row = layout.row()
        row.label(text="Add Character")
        row.operator("wm.addcharacter")

class SynthAddCharacter(bpy.types.Operator):
    bl_label = "Add Character"
    bl_idname = "wm.addcharacter"
    
    def execute(self,context):
        
        bpy.ops.import_scene.fbx( filepath=path_file )

        return {"FINISHED"}
    
def register():
    bpy.utils.register_class(SynthAddCharacter)
    bpy.utils.register_class(SynthAnimation)
    
def unregister():
    bpy.utils.unregister_class(SynthAddCharacter)
    bpy.utils.unregister_class(SynthAnimation)
    
if __name__ == "__main__":
    register()
#    unregister()
