bl_info = {
    "name": "FashionSynth",
    "author": "Emma-Jane MacKinnon-Lee",
    "version": (1, 0),
    "blender": (3, 2, 2),
    "location": "View3D > Sidebar > FashionSynth",
    "warning": "Testing in Prod",
    "wiki_url": "coinop.themanufactory.xyz",
    "category": "Development"
}

import sys
import os

addon_dir = os.path.dirname(os.path.realpath(__file__))
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

# Import everything from the working script
from script_complete import *
