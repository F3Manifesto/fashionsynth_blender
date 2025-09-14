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
from .panels.SynthUserInputs import SynthUserInputs
from .panels.SynthGarmentUploadPanel import SynthGarmentUploadPanel, SynthGarmentProperties
from .operators.SynthInstallPackages import SynthInstallPackages
from .operators.SynthGenerateGarment import SynthGenerateGarment

classes = [
    SynthUserInputs,
    SynthGarmentProperties,
    SynthGarmentUploadPanel,
    SynthInstallPackages,
    SynthGenerateGarment
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=SynthUserInputs)
    bpy.types.Scene.synth_garment_props = bpy.props.PointerProperty(type=SynthGarmentProperties)
        
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.input_tool
    del bpy.types.Scene.synth_garment_props

if __name__ == "__main__":
    register()