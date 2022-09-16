import bpy
import tempfile


class SynthUserInputs(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(
        name="Enter Prompt", default="", description="A close up center front view 2012 studio photograph of an orange and black racing bomber jacket with logo patches")
    main: bpy.props.EnumProperty(name="Select the Main Fashion Item", default="wm.jacket", description="Choose from the Pattern Options", items=[
                                 ("wm.jacket", "Jacket", "This is Jacket"), ("wm.skirt", "Skirt", "This is Skirt")])
    scale: bpy.props.FloatProperty(
        name="Enter Guidance Scale", default=10, min=6)
    steps: bpy.props.FloatProperty(
        name="Enter Number of Steps", default=75, max=200, min=50)
    init: bpy.props.BoolProperty(
        name="Do you have an input image?", default=False)
    path: bpy.props.StringProperty(
        name="Save Images Path", description="Specify Save Path", subtype="DIR_PATH", default=tempfile.gettempdir())
