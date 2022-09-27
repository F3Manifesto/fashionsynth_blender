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
import os
#from panels.SynthInputPrompt import SynthInputPrompt
#from panels.SynthPatternDetectionPanel import SynthPatternDetectionPanel
#from panels.SynthPatternMeshesPanel import SynthPatternMeshesPanel
#from panels.SynthTexturesGeneratePanel import SynthTexturesGeneratePanel
#from panels.SynthIRLSewingPanel import SynthIRLSewingPanel
#from panels.SynthInputPrompt import SynthInputPrompt
#import SynthInstallPackages

subfolders = next(os.walk('.'))[1]
print(subfolders)
#    
#classes = [SynthInstallPackages, SynthRunPromptPanel, SynthPatternDetectionPanel, SynthPatternMeshesPanel, SynthTexturesGeneratePanel, SynthIRLSewingPanel, SynthInputPrompt]
#bpy.utils.register_class(SynthUserInputs)

#def register():
#    
#    for cls in classes:
#        bpy.utils.register_class(cls)
#        
#    bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=SynthUserInputs)
#        
#def unregister():
#    for cls in classes:
#        bpy.utils.unregister_class(cls)
#    
#    del bpy.types.Scene.input_tool


#if __name__ == "__main__":
#    register()
##    unregister()