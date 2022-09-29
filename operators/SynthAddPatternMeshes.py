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

def addMesh(array, name, collection_name):
    
    newVerts = []
    for i in range(len(array)):
        if i % 2 == 0:
            x = array[i]/200
            y = array[i+1]/200
            value = mathutils.Vector((x, y, 0))
            newVerts.append(value)
    
    name = "newMesh"
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections[collection_name]
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
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return new_mesh

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

def addStitching(marked_seams_mesh):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    obj_mesh = marked_seams_mesh.data
    obj_edges = bmesh.from_edit_mesh(obj_mesh).edges
    obj_edges.ensure_lookup_table() 
    selectAll(obj_edges)
    
    bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED_ALTERNATE', ngon_method='BEAUTY')
    
    bpy.ops.mesh.tris_convert_to_quads()
    
    stitched_mesh = bpy.ops.mesh.subdivide(number_cuts=5)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return stitched_mesh

def addConnections(stitch, connected_pattern):
    selected_verts = {}
    verts_between_edges = {}
    boundary_array = []
    
    count = 0
    for i in range(len(stitch)):
        
        if i % 4 == 0:
            # create tuple
            selected_verts[i] = (stitch[i]/200, stitch[i+1]/200, stitch[i+2]/200, stitch[i+3]/200)
        
        if i % 2 == 0:
            verts_between_edges[count] = (stitch[i]/200, stitch[i+1]/200)
            count += 1
    
    vert_boundaries_first_mesh = []
    vert_boundaries_second_mesh = []
    for key in verts_between_edges:
        if key % 2 == 0:
            x, y = verts_between_edges[key]
            vert_boundaries_first_mesh.append(x)
            vert_boundaries_first_mesh.append(y)
        else:
            x, y = verts_between_edges[key]
            vert_boundaries_second_mesh.append(x)
            vert_boundaries_second_mesh.append(y)
        
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    obj_mesh = connected_pattern.data
    obj_verts = bmesh.from_edit_mesh(obj_mesh).verts
    obj_verts.ensure_lookup_table()
    unSelectAll(obj_verts)
    
    # get the outer bounds and connect them
    for key in selected_verts:
        vert_indexes = []
        x1,y1,x2,y2 = selected_verts[key]
        boundary_array.append(x1)
        boundary_array.append(y1)
        boundary_array.append(x2)
        boundary_array.append(y2)
    
        for vert in obj_verts:
            if (np.round(vert.co.x, decimals=3) == x1 and np.round(vert.co.y, decimals=3) == y1) or (np.round(vert.co.x, decimals=3) == x2 and np.round(vert.co.y, decimals=3) == y2):
                vert_indexes.append(vert.index)
        bmesh.from_edit_mesh(obj_mesh).edges.new((obj_verts[vert_indexes[0]],obj_verts[vert_indexes[1]]))
    
    # order values
    count = 0
    for vert in vert_boundaries_first_mesh:
        if count % 4 == 0:
            min_x_1 = np.minimum(vert_boundaries_first_mesh[count], vert_boundaries_first_mesh[count+2])
            max_x_1 = np.maximum(vert_boundaries_first_mesh[count], vert_boundaries_first_mesh[count+2])
            min_y_1 = np.minimum(vert_boundaries_first_mesh[count+1], vert_boundaries_first_mesh[count+3])
            max_y_1 = np.maximum(vert_boundaries_first_mesh[count+1], vert_boundaries_first_mesh[count+3])
    
    for vert in vert_boundaries_second_mesh:
        if count % 4 == 0:
            min_x_2 = np.minimum(vert_boundaries_second_mesh[count], vert_boundaries_second_mesh[count+2])
            max_x_2 = np.maximum(vert_boundaries_second_mesh[count], vert_boundaries_second_mesh[count+2])
            min_y_2 = np.minimum(vert_boundaries_second_mesh[count+1], vert_boundaries_second_mesh[count+3])
            max_y_2 = np.maximum(vert_boundaries_second_mesh[count+1], vert_boundaries_second_mesh[count+3])
    
    print(min_x_1, max_x_1, min_y_1, max_y_1)
    print(min_x_2, max_x_2, min_y_2, max_y_2)
    print(boundary_array)
    
    vert_indexes_first = []
    vert_indexes_second = []
    
    x_dominant = 0
    y_dominant = 0
    
    for vert in obj_verts:
        # first mesh values
        if (np.round(vert.co.x, decimals=3) <= max_x_1 and np.round(vert.co.x, decimals=3) >= min_x_1) and (np.round(vert.co.y, decimals=3) <= max_y_1 and np.round(vert.co.y, decimals=3) >= min_y_1):
            # remove boundaries
            is_boundary_vertex = False
            for arr in range(len(boundary_array)):
                if arr % 2 == 0:
                    if ((np.round(vert.co.x, decimals=3) == boundary_array[arr]) and (np.round(vert.co.y, decimals=3) == boundary_array[arr+1])):
                        is_boundary_vertex = True
                        print(vert.co.x, vert.co.y)
            
            if is_boundary_vertex == False:
                vert_indexes_first.append(vert.index)
        
        # second mesh values
        if (np.round(vert.co.x, decimals=3) <= max_x_2 and np.round(vert.co.x, decimals=3) >= min_x_2) and (np.round(vert.co.y, decimals=3) <= max_y_2 and np.round(vert.co.y, decimals=3) >= min_y_2):
            # remove boundaries
            is_boundary_vertex = False
            for arr in range(len(boundary_array)):
                if arr % 2 == 0:
                    if ((np.round(vert.co.x, decimals=3) == boundary_array[arr]) and (np.round(vert.co.y, decimals=3) == boundary_array[arr+1])):
                        is_boundary_vertex = True
                        print(vert.co.x, vert.co.y)
            
            if is_boundary_vertex == False:
                vert_indexes_second.append(vert.index)
               
    print(vert_indexes_first)
    print(vert_indexes_second, "\n\n")
    
    z_equal = 0
    for vertex_ind in range(len(vert_indexes_first)):
        if (vertex_ind % 2 == 0 and vertex_ind != len(vert_indexes_first)-1):
            if (obj_verts[vert_indexes_first[vertex_ind]].co.z == obj_verts[vert_indexes_first[vertex_ind+1]].co.z):
                z_equal += 1
        if (len(vert_indexes_first) % 2 != 0) and (vertex_ind == len(vert_indexes_first)-2):
                z_equal += 1
    
    rotated = False
    if z_equal == np.ceil(len(vert_indexes_first)/2).astype(np.int64):
        bpy.ops.object.mode_set(mode='OBJECT')
        # rotate entire object on global
        connected_pattern.rotation_euler[0] = 90
        rotated = True
        print("rotated", rotated)
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        obj_mesh = connected_pattern.data
        obj_verts = bmesh.from_edit_mesh(obj_mesh).verts
        obj_verts.ensure_lookup_table()
        unSelectAll(obj_verts)
    
    np.sort(vert_indexes_first)
    print("last", vert_indexes_first, "\n\n")
    
    # sort via z index
    global_obj_first_array = []
    global_obj_second_array = []
    for vertex_ind in range(len(vert_indexes_first)):
#        bpy.context.window.scene.transform_orientation_slots[0].type = 'GLOBAL'
        global_obj_first = connected_pattern.matrix_world @ obj_verts[vert_indexes_first[vertex_ind]].co
        global_obj_second = connected_pattern.matrix_world @ obj_verts[vert_indexes_second[vertex_ind]].co
        print("first", global_obj_first.z)
        global_obj_first_array.append({"g_z": global_obj_first.z, "index": vert_indexes_first[vertex_ind]})
        print("second", global_obj_second.z)
        global_obj_second_array.append({"g_z": global_obj_second.z, "index": vert_indexes_second[vertex_ind]})
        
        if vertex_ind == len(vert_indexes_first)-1:
            global_obj_first_array = sorted(global_obj_first_array, key=lambda k: k['g_z'])
            global_obj_second_array = sorted(global_obj_second_array, key=lambda k: k['g_z'])
            
            ordered_indexes_first = []
            ordered_indexes_second = []
            for index in global_obj_first_array:
                ordered_indexes_first.append(index["index"])
            
            for index in global_obj_second_array:
                ordered_indexes_second.append(index["index"])
            
            for vertex_ind in range(len(ordered_indexes_first)):
                bmesh.from_edit_mesh(obj_mesh).edges.new((obj_verts[ordered_indexes_first[vertex_ind]],obj_verts[ordered_indexes_second[vertex_ind]]))
    
    if (rotated == True):
        selectAll(obj_verts)
        connected_pattern.rotation_euler[0] = 0
        unSelectAll(obj_verts)
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        bpy.ops.object.mode_set(mode='OBJECT')
        
    
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
        
        array1 = [1086, 733, 1099, 739, 1112, 758, 1114, 802, 1096, 844, 1061, 876, 1023, 784, 1033, 778, 1038, 753, 1049, 738]
        
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
        
        array14 = [548, 98, 657, 68, 688, 83, 776, 68, 882, 97, 877, 202, 905, 237, 905, 436, 528, 437, 524, 238, 556, 200]
        
        array15 = [373, 63, 493, 97, 477, 188, 482, 215, 515, 238, 512, 437, 311, 436, 310, 136, 357, 119]
        
        array16 = [219, 63, 235, 119, 282, 136, 281, 436, 80, 437, 79, 237, 110, 215, 115, 188, 99, 97]
        
        meshArray = [array1, array2, array3, array4, array5, array6, array7, array8, array9, array10, array11, array12, array13, array14, array15, array16]
        
#        name = ["meshOne", "meshTwo", "meshThree", "meshFour", "meshFive", "meshSix", "meshSeven", "meshEight", "meshNine", "meshTen", "meshEleven", "meshTwelve", "meshThirteen", "meshFourteen", "meshFifteen", "meshSixteen"]
        
        # contour 1/2 connect 4 and 14, 6 and 12
        stitchPair1 = [282, 136, 310, 136, 281, 436, 311, 436]
        stitchPair2 = [515, 238, 524, 238, 512, 437, 528, 437]
        stitchPair3 = [79, 237, 905, 237, 80, 437, 905, 436]
        stitchPair4 = [62, 610, 357, 610, 108, 879, 312, 880]
        stitchPair5 = [657, 610, 362, 610, 612, 880, 408, 879]
        
        
        stitchArray = [stitchPair1, stitchPair2, stitchPair3, stitchPair4, stitchPair5]

        name = ["meshOne"]
        
        collection_name = 'bomberJacket'
        this_collection = bpy.data.collections.new(name=collection_name)
        
        scene_collection = bpy.context.scene.collection
        scene_collection.children.link(this_collection)
        
        for arr in meshArray:
            # call this individually in the main file and have it take in a dictionary? or do i create a seperate function out of this for loop above which takes in the array arguments and then passes them as values down here into ultimate arry?
            new_mesh = addMesh(arr, name, collection_name)
            
            new_mesh = context.object
          
            marked_seams_mesh = markSeam(new_mesh)
                        
            marked_seams_mesh = context.object
            
            stitched_mesh = addStitching(marked_seams_mesh)
            
            stitched_mesh = context.object
        
        # select and join all objects in collection
        for obj in bpy.data.collections[collection_name].all_objects:
            obj.select_set(True)
        
        bpy.ops.object.join()
        
        connected_pattern = context.object
        
        # traverse through stitching arrays
        for stitch in stitchArray:
            
            addConnections(stitch, connected_pattern)
        
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


