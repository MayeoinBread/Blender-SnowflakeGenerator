bl_info = {"name":"Snowflake Generator",
           "author":"Eoin Brennan (Mayeoin Bread)",
           "version":(1,3),
           "blender":(2,7,4),
           "location":"View3D > Add > Mesh",
           "description":"Adds a randomly generated snowflake",
           "warning":"",
           "wiki_url":"",
           "tracker_url":"",
           "category":"Add Mesh"}

import bpy
import bmesh
from mathutils import Vector
from math import pi, sin, cos, asin, acos, atan
from bpy.props import IntProperty, BoolProperty
from random import *

##
# Panel for "3D" snowflake in tool panel
# Creates bezier circle for bevel object, scaling this will change snowflake arm diameter
##
class SnowflakePanel(bpy.types.Panel):
    bl_label = "Snowflake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    
    @classmethod
    def poll(self, context):
        if context.object and context.object.type=='MESH' and 'Snowflake' in context.object.name:
            return context.object is not None
        
    def draw(self, context):
        layout = self.layout
        layout.operator("snowflake.curve")

class OBJECT_OT_CurveButton(bpy.types.Operator):
    bl_idname = "snowflake.curve"
    bl_label = "Convert snowflake to curve"
    @classmethod
    def poll(self, context):
        if context.object and context.object.type=='MESH':
            return len(context.object.type)
    ##
    # If snowflake mesh selected: duplicate, convert to curve and add bevel (bezier circle)
    ##
    def execute(self, context):
        bName = "SnowflakeBevel"
        bpy.ops.object.duplicate()
        bpy.ops.object.convert(target='CURVE')
        cName = bpy.context.object.data.name
        if bpy.data.objects.get(bName) == None:
            bpy.ops.curve.primitive_bezier_circle_add(
                radius=0.08,
                view_align=False,
                enter_editmode=False,
                location=(4.0,0.0,0.0),
                rotation=(0.0,0.0,0.0))
            ob = bpy.context.object
            ob.show_name=True
            ob.name = bName
            ob.data.name = bName
        bpy.data.curves[cName].bevel_object = bpy.data.objects.get(bName)
        return{'FINISHED'}

class SnowflakeGen(bpy.types.Operator):
    """Snowflake Generator"""
    bl_idname = "mesh.snowflake"
    bl_label = "Snowflake"
    bl_options = {"REGISTER", "UNDO"}
    
    ##
    # User input
    ##
    # Outer rings
    numR = IntProperty(name="Number of rings", description="Number of internal rings in snowflake", default=1, min=0, max=2)
    # Circle vertices
    numV = IntProperty(name="Vertices", description="Number of vertices on base circle for snowflake", default=6, min=3, max=12)
    # Fill snowflake
    fill = BoolProperty(name="Fill center", description="Extend legs to center of snowflake", default=True)
    # Create full snowflake or just section
    fullS = BoolProperty(name="Full shape", description="Create a full snowflake, or just one sector", default=True)
        
    ##
    # Main function
    ##
    def execute(self, context):
        # Null values:
        nullP = (0.0,0.0,0.0)
        ##
        # New obj function
        ##
        def addObj():
            obj = bpy.context.object
            if obj != None:
                if obj.mode == "EDIT":
                    bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.delete()
            bpy.ops.object.add(type='MESH',
                enter_editmode=True,
                view_align=False,
                location=nullP,
                rotation=nullP)
            obj = bpy.context.object
            obj.name = "Snowflake"
            return obj
        ##
        # Select a vert
        ##
        def selVert(par):
            bm.verts.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts[par].select = True
        ##
        # Select an edge
        ##
        def selEdge(par):
            bm.edges.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges[par].select = True
        ##
        # Select last edge
        ##
        def selLasEdge():
            for e in bm.edges:
                bpy.ops.mesh.select_all(action='DESELECT')
                e.select = True
        ##
        # Extrude and move along vector
        ##
        def extMov(vec):
            bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":vec})
        ##
        # Rotate around Z-axis origin
        ##
        def rotate(ang):
            bpy.ops.transform.rotate(value=(-ang),
                axis=(0.0,0.0,0.1))
        ##
        # Subdivide selected edge
        ##
        def subdiv(num):
            if num > 0:
                bpy.ops.mesh.subdivide(number_cuts=num)
        ##
        # Total number of verts
        ##
        def numVerts():
            vco = 0
            for v in bm.verts:
                vco += 1
            return vco - 1
        ##
        # Total number of edges
        ##
        def numEdges():
            eco = 0
            for e in bm.edges:
                eco += 1
            return eco-1
        ##
        # Duplicate and move selection
        ##
        def dupMove(vec):
            bpy.ops.mesh.duplicate_move(TRANSFORM_OT_translate={"value":vec})
        ##
        # Extrude leg 1
        ##
        def extLeg(vert, length, minus):
            selVert(vert)
            if minus == 0:
                legVec = Vector(
                    (length*cos(pi/4),
                    length*sin(pi/4),
                    0.0))
                extMov(legVec)
            else:
                legVec = Vector(
                    (-length*cos(pi/4),
                    length*sin(pi/4),
                    0.0))
                extMov(legVec)
        ##
        # Extrude leg 2
        ##
        def extLeg2(vert, length, angle):
            selVert(vert)
            legVec = Vector((
                length*sin(angle),
                length*cos(angle),
                0.0))
            extMov(legVec)
        ##
        # Main running order
        ##
        bpy.context.space_data.pivot_point = 'CURSOR'
        bpy.ops.view3d.snap_cursor_to_center()
        obj = addObj()
        bm = bmesh.from_edit_mesh(obj.data)
        # Check for mesh, all we work with
        if obj.type == "MESH":
            if obj.mode == "OBJECT":
                bpy.ops.object.mode_set(mode="EDIT")
            if obj.mode == "EDIT":
                # Clear all verts, just in case mesh not empty
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='VERT')
                # Add circle (snowflake base)
                bpy.ops.mesh.primitive_circle_add(
                    vertices=self.numV,
                    radius=1.0,
                    fill_type='NOTHING',
                    location=nullP,
                    rotation=nullP,
                    view_align=False,
                    enter_editmode=True)
                ##
                # Variables...
                ##
                rnum = randint(0,1)
                [s1,s2] = [1,2] if rnum==0 else [2,1]
                fillC = self.fill
                fullSh = self.fullS
                vCount = 0
                oVerts = []
                rand1 = 2
                rando = uniform(0.2,1.0)*2
                nullV = Vector(nullP)
                randleg = randint(1,3)
                randInternal = randint(0,randleg)
                numRings = self.numR
                bName = "SFBez"
                ##
                # Store original verts
                ##
                bm.verts.ensure_lookup_table()
                for v in bm.verts:
                    vCount += 1
                    oVerts.append(v.index)
                # Remove first vert so whole edge is selected later on
                oVerts.pop(0)
                ##
                # Vectors for angles and edge length
                ##
                root = bm.verts[0].co
                x = bm.verts[1].co
                y = bm.verts[vCount-1].co
                # Length of arm
                d = ((root.x-x.x)**2 + (root.y-x.y)**2)**0.5
                x = x + root
                y = y + root
                # Vector dot product
                ab = (x.x*y.x) + (x.y*y.y) + (x.z*y.z)
                aa = ((x.x**2) + (x.y**2) + (x.z**2))**0.5
                bb = ((y.x**2) + (y.y**2) + (y.z**2))**0.5
                angle = acos(ab/(aa*bb))
                ##
                # Start making snowflakes!!
                ##
                # Extrude top vert upwards
                selVert(0)
                myVec = Vector((0.0,d*rando*2,0.0))
                extMov(myVec)
                # Subdivide new edge
                selLasEdge()
                subdiv(1)
                # Save d, randomise new d for legs
                dd = d
                d = d*uniform(0.4,1.0)
                # Position new vert
                bm.verts.ensure_lookup_table()
                lastVert = numVerts()
                bm.verts[lastVert].co.x = root.x
                bm.verts[lastVert].co.y = root.y + (vCount-1)*(d*rando*2)/vCount
                # Extrude right leg
                extLeg(lastVert,(4*dd/d)/vCount,0)
                # Extrude left leg
                bm.verts.ensure_lookup_table()
                extLeg(lastVert,(4*dd/d)/vCount,1)
                # Extrude outer ring
                ringEdge = numEdges() - 2
                length = ((4*dd/d)/vCount)
                if d < 0.6*dd:
                    mlva = []
                    lastEdge = numEdges()
                    selEdge(ringEdge-1)
                    subdiv(randleg)
                    bm.verts.ensure_lookup_table()
                    lastVert = numVerts()
                    for l in range(randleg):
                        mlva.append(lastVert-l)
                    hg = (4*dd/d)/vCount - len(mlva)*(d/2)
                    for l in range(len(mlva)):
                        bm.verts.ensure_lookup_table()
                        extLeg(mlva[l],hg,0)
                        bm.verts.ensure_lookup_table()
                        extLeg(mlva[l],hg,1)
                        hg = hg+d/2
                    s3 = 0
                else:
                    s3 = 1
                ##
                # Extrude rings
                ##
                lastEdge = numEdges()
                selEdge(ringEdge)
                subdiv(numRings)
                bm.verts.ensure_lookup_table()
                lastVert = numVerts()
                outerRingLoops = []
                for i in range(numRings):
                    outerRingLoops.append(lastVert-i)
                for j in range(len(outerRingLoops)):
                    selVert(outerRingLoops[j])
                    # Extrude and rotate
                    for i in range(rand1):
                        bm.verts.ensure_lookup_table()
                        extMov(nullV)
                        rotate(angle/rand1)
                    lastVert = numVerts()
                    ##
                    # If we're in the outer ring
                    ##
                    if j == 0:
                        # Select middle vert
                        selVert(lastVert-1)
                        upVec = Vector((0.0,dd*rando*2,0.0))
                        # Snap cursor to rotate around vert
                        bpy.ops.view3d.snap_cursor_to_selected()
                        # Extrude and rotate around vert
                        bm.verts.ensure_lookup_table()
                        extMov(upVec)
                        rotate(angle/2)
                        bpy.ops.view3d.snap_cursor_to_center()
                        selLasEdge()
                        hg = d/s1
                        if s3 == 0:
                            # We have legs on main leg
                            subdiv(s1)
                            bm.verts.ensure_lookup_table()
                            lastVert = numVerts()
                            extLeg2(lastVert,hg,angle/2+(pi/4))
                            bm.verts.ensure_lookup_table()
                            extLeg2(lastVert,hg,angle/2-(pi/4))
                            lastEdge = numEdges()
                            if s1 == 1:
                                if randInternal == 0:
                                    selEdge(lastEdge-2)
                                else:
                                    selEdge(lastEdge-3)
                            else:
                                if randInternal == 0:
                                    selEdge(lastEdge-4)
                                else:
                                    selEdge(lastEdge-3)
                            subdiv(randleg)
                            lastVert = numVerts()
                            mlvb=[]
                            for l in range(randleg):
                                bm.verts.ensure_lookup_table()
                                mlvb.append(lastVert-l)
                            randrev = randint(0,1)
                            if randrev == 1:
                                mlvb.reverse()
                            for l in range(len(mlvb)):
                                hg = hg-(d/(randleg+1))
                                extLeg2(mlvb[l],hg,(angle/2)+(pi/4))
                                extLeg2(mlvb[l],hg,(angle/2)-(pi/4))
                    ##
                    # If we're on the inner ring
                    ##
                    if j == 1:
                        # As above, but with 2 legs this time
                        selVert(lastVert-1)
                        upVec = Vector((0.0,dd*rando*2,0.0))
                        bpy.ops.view3d.snap_cursor_to_selected()
                        extMov(upVec)
                        rotate(2*angle/3)
                        selVert(lastVert-2)
                        bpy.ops.view3d.snap_cursor_to_selected()
                        extMov(upVec)
                        rotate(angle/3)
                        bpy.ops.view3d.snap_cursor_to_center()
                        lasEdg = numEdges()
                        lledg = lasEdg - 1
                        selEdge(lasEdg)
                        subdiv(s2)
                        mlvc = []
                        if s3 == 1:
                            lastVert = numVerts()
                            extLeg2(lastVert,(d/dd)/s1,angle/3+(pi/4))
                            extLeg2(lastVert,(d/dd)/s1,angle/3-(pi/4))
                        selEdge(lledg)
                        subdiv(s2)
                        if s3 == 1:
                            lastVert = numVerts()
                            extLeg2(lastVert,(d/dd)/s1,2*angle/3+(pi/4))
                            extLeg2(lastVert,(d/dd)/s1,2*angle/3-(pi/4))
                    rand1 = rand1+1
                ##
                # Select all new verts and duplicate
                ##
                bm.verts.ensure_lookup_table()
                if fullSh:
                    bpy.ops.mesh.select_all(action = 'SELECT')
                    for o in oVerts:
                        bm.verts[o].select = False
                    for i in range(vCount-1):
                        # Duplicate 'em around the origin
                        dupMove(nullV)
                        rotate(angle)
                        dupVert = []
                        dupEdge = []
                        for v in bm.verts:
                            if v.select:
                                dupVert.append(v.index)
                        for e in bm.edges:
                            if e.select:
                                dupEdge.append(e.index)
                        bpy.ops.mesh.select_all(action = 'DESELECT')
                        bm.verts.ensure_lookup_table()
                        bm.edges.ensure_lookup_table()
                        for r in range(len(dupVert)):
                            bm.verts[dupVert[r]].select = True
                        for r in range(len(dupEdge)):
                            bm.edges[dupEdge[r]].select = True
                else:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    for o in oVerts:
                        bm.verts[o].select = True
                    bpy.ops.mesh.delete(type='VERT')
                ##
                # Fill center?
                ##
                if fillC:
                    selVert(0)
                    if fullSh:
                        for o in oVerts:
                            bm.verts[o].select = True
                    extMov(nullV)
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
                # Remove doubles
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.object.mode_set(mode="OBJECT")
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(SnowflakeGen.bl_idname,text="Snowflake",icon="PLUGIN")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()