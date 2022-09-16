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


