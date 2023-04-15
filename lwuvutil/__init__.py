bl_info = {
    "name": "Lightweight UV Utility toolkit",
    "author": "Koekto-code",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "UV Editor > UV",
    "description": "Currently has operator for uniform UV aligning",
    "warning": "",
    "doc_url": "",
    "category": "UV",
}

import bpy
import bmesh

def uvoper1(self, context):
    obj = context.active_object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    uv_layer = bm.loops.layers.uv.active # .verify()
    
    # whether a vertex, edge or face has any UV loops selected
    def atleast1loop(link_loops):
        for loop in link_loops:
            if loop[uv_layer].select:
                return True
        return False
    
    # at least 1 loop 'with edge' selected
    def atleast1loopwe(link_loops):
        for loop in link_loops:
            if loop[uv_layer].select and loop[uv_layer].select_edge:
                return True
        return False
    
    # returns index of vertex of R that touches S
    def connected(r, s):
        rv = r.verts
        sv = s.verts
        if rv[0] == sv[0] or rv[0] == sv[1]:
            return 0
        if rv[1] == sv[0] or rv[1] == sv[1]:
            return 1
        return None
    
    # get all selected edges that match selected UV loops
    esel = [e for e in bm.edges \
        if e.select and e.is_valid and atleast1loopwe(e.link_loops)]
    
    vsel = [v for v in bm.verts \
        if v.select and v.is_valid and atleast1loop(v.link_loops)]
    
    # avoid division by 0
    if len(vsel) < 2:
        return {'CANCELLED'}
    
    # find two edges that have only 1 connection with other edge
    edge_beg = None; edge_beg_n = None
    edge_end = None; edge_end_n = None
    
    for ie, e in enumerate(esel):
        print("new")
        conns = 0 # connection counter
        edgesel = None
        edgenum = None
        for iee, ee in enumerate(esel):
            if e is ee:
                continue
            c = connected(e, ee)
            print("connected:", c)
            if not c is None:
                conns += 1
                if conns == 2:
                    print("both!")
                    break
                edgesel = ie
                edgenum = c
        if conns == 2:
            continue
        
        if edge_beg is None:
            edge_beg = edgesel
            edge_beg_n = edgenum
        elif edge_end is None:
            edge_end = edgesel
            edge_end_n = edgenum
        else:
            self.report({'ERROR'}, "More than 2 singly-connected UV edges in selection")
            return {'CANCELLED'}
    
    if edge_beg is None or edge_end is None:
        self.report({'ERROR'}, "Invalid UV selection")
        return {'CANCELLED'}
    
    ebv = esel[edge_beg].verts[1 - edge_beg_n]
    eev = esel[edge_end].verts[1 - edge_end_n]
    
    def ve_next(vert, edge):
        oth = edge.other_vert(vert)
        for e in esel:
            if e is edge:
                continue
            if oth in e.verts:
                fnextEdge = edge
                return oth, e
        return None
        
    # starting UV coordinate
    ebvluvs = [l[uv_layer] for l in ebv.link_loops if l[uv_layer].select]
    ebvluvs = (ebvluvs[0].uv.x, ebvluvs[0].uv.y)
    
    # ending UV coordinate
    eevluvs = [l[uv_layer] for l in eev.link_loops if l[uv_layer].select]
    eevluvs = (eevluvs[0].uv.x, eevluvs[0].uv.y)
    
    # uniform stepping vector
    stepx = (eevluvs[0] - ebvluvs[0]) / (len(vsel) - 1)
    stepy = (eevluvs[1] - ebvluvs[1]) / (len(vsel) - 1)
    
    iter_v = esel[edge_beg].verts[1 - edge_beg_n]
    iter_e = esel[edge_beg]
    iter_ind = 0
    while True:
        for l in iter_v.link_loops:
            luv = l[uv_layer]
            if luv.select:
                luv.uv.x = ebvluvs[0] + stepx * iter_ind
                luv.uv.y = ebvluvs[1] + stepy * iter_ind
        
        res = ve_next(iter_v, iter_e)
        if res is None:
            break
        iter_v, iter_e = res
        iter_ind += 1
    
    bmesh.update_edit_mesh(me)
    return {'FINISHED'}


class AlignOperator(bpy.types.Operator):
    """UV Operator description"""
    bl_idname = "lwuvutil.align_operator"
    bl_label = "Align uniformly"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        return uvoper1(self, context)


def menu_func(self, context):
    self.layout.operator(AlignOperator.bl_idname, text="Align uniformly")

def register():
    bpy.utils.register_class(AlignOperator)
    bpy.types.IMAGE_MT_uvs.append(menu_func)

def unregister():
    bpy.utils.unregister_class(AlignOperator)
    bpy.types.IMAGE_MT_uvs.remove(menu_func)

if __name__ == "__main__":
    register()

