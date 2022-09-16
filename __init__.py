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
import sys
import os 
blend_dir = os.path.basename(bpy.data.filepath)
if blend_dir not in sys.path:
   sys.path.append(blend_dir)
from panels import SynthRunPromptPanel, SynthPatternDetectionPanel, SynthPatternMeshesPanel, SynthTexturesGeneratePanel, SynthIRLSewingPanel, SynthInputPrompt, SynthUserInputs
import SynthInstallPackages 
sys.path += [r"Users/devdesign/Documents/Blender Scripting/fashionsynth/panels"]

import panels as panels
#from SynthRunPromptPanel import SynthRunPromptPanel
    
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