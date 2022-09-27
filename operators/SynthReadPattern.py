import bpy
import bmesh
import mathutils

def unselectAll(vertices):
    for vert in vertices:
        vert.select = False

def selectAll(vertices):
    for vert in vertices:
        vert.select = True
        
# need to itterate over this class def of pattern stitch placing each time the new canvas array for each contour
# always skip for array as that will be the box
# execute should take in an array 
    
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
        
        bpy.ops.mesh.primitive_plane_add()
        obj = context.object
        bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        bpy.ops.mesh.select_mode(type='VERT')
        obj_mesh = obj.data
        obj_vertices = bmesh.from_edit_mesh(obj_mesh).verts
        
        obj_vertices.ensure_lookup_table() 
        unselectAll(obj_vertices) 
        print(list(obj_vertices))
        
        for vert in range(len(obj_vertices)-1,0,-1):
            obj_vertices[vert].select = True
            bpy.ops.mesh.delete(type='VERT')
            
            obj_vertices.ensure_lookup_table() 
            unselectAll(obj_vertices) 
            
        obj_vertices[0].select = True 
        
        # second contour item examplea
        array = [1086, 733, 1099, 739, 1112, 758, 1114, 802, 1096, 844, 1061, 876, 1023, 784, 1033, 778, 1038, 753, 1049, 738]
        
        count = 0;
        for i in range(0,len(array)):
            
            # move the first vertex to first coordinates
            if i == 0:
                print("At 0")
                # convert to mm or scale another way?

                x = array[i]/1000
                y = array[i+1]/1000
                value = mathutils.Vector((x, y, 0))
                value = value.normalized()
                print(value, "+", count)
                bpy.ops.transform.translate(value=value)
                
                obj_vertices.ensure_lookup_table()
                unselectAll(obj_vertices)
                count += 1
            
            # move other coordinates
            if i % 2 == 0 and i != 0:
                
                x = array[i]/1000
                y = array[i+1]/1000
                value = mathutils.Vector((x, y, 0))
                value.normalized()
                
                obj_vertices[count-1].select = True 
                bpy.ops.mesh.duplicate_move()
                print(value, "+", count)
                bpy.ops.transform.translate(value=value)
                
                obj_vertices.ensure_lookup_table()
                unselectAll(obj_vertices)
                count += 1
            
        obj_vertices.ensure_lookup_table()
        selectAll(obj_vertices)
        bpy.ops.mesh.edge_face_add()
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
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


import bpy
import bmesh
import mathutils
import numpy as np

def selectAll(vertices):
    for vert in vertices:
        vert.select = True

def unSelectAll(vertices):
    for vert in vertices:
        vert.select = False

def distanceBetween(array):
    i = 0
    length = []
    for arr in range(len(array),0,-1):
        if i % 4 == 0 and i != len(array)-3 and i != len(array)-2 and i != len(array)-1:
            
            x = array[i] - array[i+2]
            x = abs(x)
            y = array[i+1] - array[i+3]
            y = abs(y)
            print("x= ",x," y= ",y, " i= ", i)
            distance = np.sqrt(np.square(x) + np.square(y))
            print("distance = ", distance)
            length.append(distance)
        
        elif i == len(array):
            x = array[i-2] - array[i]
            x = abs(x)
            y = array[0] - array[i-1]
            y = abs(y)
            print("x= ",x," y= ",y, " i= ", i)
            distance = np.sqrt(np.square(x) + np.square(y))
            print("distance = ", distance)
            length.append(distance)
        
        i += 1
        
    print(length)
    length.sort()
    second_max_len = length[-2]
    second_max_index = length.index(second_max_len)
    return second_max_index
        
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
    new_mesh = mesh.from_pydata(newVerts,[],[])
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    obj_mesh = obj.data
    obj_vertices = bmesh.from_edit_mesh(obj_mesh).verts
    
    obj_vertices.ensure_lookup_table()
    selectAll(obj_vertices)
    bpy.ops.mesh.edge_face_add()
    
    bpy.ops.mesh.select_mode(type='FACE')
    obj_mesh = obj.data
    obj_faces = bmesh.from_edit_mesh(obj_mesh).faces
    
    obj_faces.ensure_lookup_table()
    selectAll(obj_faces)
    # delete face as you will use fill_grid later
    new_mesh = bpy.ops.mesh.delete(type='ONLY_FACE')
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return new_mesh

def addStitching(new_arr):
    
    stitched_mesh = bpy.ops.mesh.subdivide(number_cuts=10)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return stitched_mesh
        
def markSeam(new_mesh):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    obj_mesh = new_mesh.data
    obj_edges = bmesh.from_edit_mesh(obj_mesh).edges
    obj_edges.ensure_lookup_table() 
    selectAll(obj_edges)
    
    marked_seams_mesh = bpy.ops.mesh.mark_seam(clear=False)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return marked_seams_mesh

def splitOdd(arr, marked_seams_mesh):
    bpy.ops.object.mode_set(mode='EDIT')
    obj_edges = bmesh.from_edit_mesh(marked_seams_mesh).edges
    print(len(arr))
    # check if odd number of edges before applying fill grid
    if len(arr)/2 % 2 != 0:
        # get distance between segments for applying grid later
        second_max_index = distanceBetween(arr)
        print(second_max_index, "second")
        # get the edge that is the second max length
        # cut the edge that is the second max length a loop cut
        new_obj = bpy.ops.mesh.loopcut(number_cuts=1, falloff='INVERSE_SQUARE', object_index=0, edge_index=second_max_index)
    
    obj_edges.ensure_lookup_table()
    selectAll(obj_edges)
    bpy.ops.mesh.fill_grid()
    
    new_mesh = bpy.ops.object.mode_set(mode='OBJECT')
    
    return new_mesh

#def unwrapAndSeperate(stitchedMesh):
#    bpy.ops.uv.smart_project(scale_to_bounds=True)
    
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
        
        ultimateArray = [array16]
        
#        name = ["meshOne", "meshTwo", "meshThree", "meshFour", "meshFive", "meshSix", "meshSeven", "meshEight", "meshNine", "meshTen", "meshEleven", "meshTwelve", "meshThirteen", "meshFourteen", "meshFifteen", "meshSixteen"]

        name = ["meshOne"]
        
        for arr in ultimateArray:
            # call this individually in the main file and have it take in a dictionary? or do i create a seperate function out of this for loop above which takes in the array arguments and then passes them as values down here into ultimate arry?
            new_mesh = addMesh(arr, name)
            
            new_mesh = context.object
          
            marked_seams_mesh = markSeam(new_mesh)
                        
            marked_seams_mesh = context.object.data
            
            new_mesh = splitOdd(arr, marked_seams_mesh)
            
            stitched_mesh = addStitching(new_mesh)
#            
#            stitched_mesh = context.object.data
#            
#            unwrapAndSeperate(stitched_mesh)
#            
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


