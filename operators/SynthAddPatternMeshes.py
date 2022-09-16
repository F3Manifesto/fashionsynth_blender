import bpy
import bmesh
import mathutils

def selectAll(vertices):
    for vert in vertices:
        vert.select = True
        
def addMesh(array, name):
        
    newVerts = []
    for i in range(len(array)):
        
        if i % 2 == 0:
            x = array[i]/1000
            y = array[i+1]/1000
            value = mathutils.Vector((x, y, 0))
            newVerts.append(value)
            
    name = "newMesh"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections["Collection"]
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(newVerts,[],[])
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    obj_mesh = obj.data
    obj_vertices = bmesh.from_edit_mesh(obj_mesh).verts
    
    obj_vertices.ensure_lookup_table()
    selectAll(obj_vertices)
    newMesh = bpy.ops.mesh.edge_face_add()
        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return newMesh

def addStitching(newMesh):
    
    
    
        
    
class SynthReadPattern(bpy.types.Panel):
    bl_label="Read Pattern"
    bl_idname="READ_PT_Pattern"
    bl_space_type = "VIEW_3D"
    bl_region_type="UI"
    bl_category="Read Pattern"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text="Add Jacket Pattern")
        row.operator("wm.patternstitch")
        

class SynthPatternStitch(bpy.types.Operator):
    bl_label = "Pattern Stitch"
    bl_idname = "wm.patternstitch"
    
    def execute(self, context):
        
        array1 = [1086, 733, 1099, 739, 1112, 758, 1114, 802, 1096, 844, 1061, 876,  1023, 784, 1033, 778, 1038, 753, 1049, 738]
        
        array2 = [849, 733, 886, 738, 898, 755, 902, 777, 912, 784, 874, 876, 842, 848, 822, 807, 819, 781, 824, 756, 836, 739]
        
        array3 = [749, 733, 786, 738, 798, 755, 802, 777, 818, 785, 779, 876, 744, 853, 722, 807, 719, 781, 724, 756, 736, 739]
        
        array4 = [992, 730, 1004, 735, 1016, 750, 1021, 793, 1004, 840, 969, 873, 927, 781, 937, 773, 943, 751, 955, 735]
        
        array5 = [1072, 650, 1152, 649, 1153, 703, 1073, 704]
        
        array6 = [944, 642, 1036, 641, 1037, 673, 945, 674]
        
        array7 = [696, 613, 742, 597, 766, 613, 844, 612, 860, 597, 906, 611, 863, 673, 825, 688, 782, 688, 750, 678, 722, 652]
        
        array8 = [944, 597, 1036, 596, 1037, 628, 945, 629]
        
        array9 = [1072, 554, 1152, 553, 1153, 607, 1073, 608]
        
        array10 = [456, 543, 550, 539, 657, 610, 612, 880, 408, 879, 362, 610]
        
        array11 = [156, 543, 250, 539, 357, 610, 312, 880, 108, 879, 62, 610]
        
        array12 = [1135, 78, 1088, 223, 1083, 428, 1026, 429, 1025, 135, 1071, 119, 1088, 68]
        
        array13 = [903, 78, 950, 68, 966, 118, 1013, 135, 1012, 429, 955, 428, 950, 224]
        
        array14 = [548, 98, 657, 68, 688, 83, 776, 68, 882, 97, 877, 202, 905, 237, 905, 436, 528, 437, 527, 237, 556, 200]
        
        array15 = [373, 63, 493, 97, 477, 188, 482, 215, 513, 237, 512, 437, 310, 436, 310, 136, 357, 119]
        
        array16 = [219, 63, 235, 119, 282, 136, 282, 436, 80, 437, 79, 237, 110, 215, 115, 188, 99, 97]
        
        ultimateArray = [array1, array2, array3, array4, array5, array6, array7, array8, array9, array10, array11, array12, array13, array14, array15, array16]
        
        name = ["meshOne", "meshTwo", "meshThree", "meshFour", "meshFive", "meshSix", "meshSeven", "meshEight", "meshNine", "meshTen", "meshEleven", "meshTwelve", "meshThirteen", "meshFourteen", "meshFifteen", "meshSixteen"]
        
        for arr in ultimateArray:
            newMesh = addMesh(arr, name)
            addStitching(newMesh)
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(SynthReadPattern)
    bpy.utils.register_class(SynthPatternStitch)
    
def unregister():
    bpy.utils.unregister_class(SynthReadPattern)
    bpy.utils.unregister_class(SynthPatternStitch)
    
if __name__ == "__main__":
    register()
#    unregister()


