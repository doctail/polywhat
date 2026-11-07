"""Realistic pedestrians from MPFB 2 (MakeHuman for Blender, CC0 assets) on the 'cmu_mb' rig,
animated with CMU mocap (BVH) baked by bone direction, clothes/hair painted by body zone.
MPFB must be installed as a Blender extension (tools/city/install_mpfb.py does it).

    H = HumanFactory(coll)
    P = H.make(seed, walker_bvh=None)   -> dict(root, arm, action, h, rnd)  (same shape as people.make_person)
The pose helpers in people.py (make_idle, look_up, cover, hold_pose) work on these rigs too.
"""
import math, random, os
import bpy, addon_utils
from mathutils import Vector, Matrix, Quaternion

addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
import people as PP

SKIN = [(0.80, 0.58, 0.45), (0.62, 0.42, 0.30), (0.42, 0.27, 0.17), (0.90, 0.70, 0.56), (0.28, 0.18, 0.12), (0.72, 0.52, 0.38)]
HAIR = [(0.02, 0.015, 0.01), (0.10, 0.06, 0.03), (0.28, 0.17, 0.08), (0.04, 0.04, 0.04), (0.45, 0.32, 0.18), (0.55, 0.53, 0.5)]
TOPS = [(0.03, 0.03, 0.035), (0.55, 0.55, 0.57), (0.06, 0.09, 0.2), (0.4, 0.05, 0.04), (0.75, 0.72, 0.64), (0.12, 0.2, 0.12),
        (0.85, 0.85, 0.83), (0.25, 0.16, 0.09), (0.5, 0.38, 0.22), (0.18, 0.25, 0.4), (0.6, 0.12, 0.25)]
BOTS = [(0.03, 0.04, 0.07), (0.08, 0.11, 0.2), (0.18, 0.18, 0.2), (0.3, 0.26, 0.19), (0.04, 0.04, 0.04), (0.45, 0.42, 0.36)]
SHOES = [(0.02, 0.02, 0.02), (0.8, 0.8, 0.78), (0.2, 0.12, 0.06), (0.05, 0.05, 0.06)]

ZONE = {  # dominant bone -> zone
    'LowerBack': 'top', 'Spine': 'top', 'Spine1': 'top', 'LeftShoulder': 'top', 'RightShoulder': 'top',
    'LeftArm': 'top', 'RightArm': 'top', 'LeftForeArm': 'sleeve', 'RightForeArm': 'sleeve',
    'Hips': 'bot', 'LHipJoint': 'bot', 'RHipJoint': 'bot', 'LeftUpLeg': 'bot', 'RightUpLeg': 'bot',
    'LeftLeg': 'leg', 'RightLeg': 'leg', 'LeftFoot': 'shoe', 'RightFoot': 'shoe', 'LeftToeBase': 'shoe', 'RightToeBase': 'shoe',
}
_mats = {}
def mat(rgb, rough=0.75, sss=0.0, sheen=0.3):
    k = (tuple(round(c, 3) for c in rgb), rough, sss)
    if k not in _mats:
        m = bpy.data.materials.new('hm'); b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
        b.inputs['Sheen Weight'].default_value = sheen
        if sss: b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2)
        _mats[k] = m
    return _mats[k]

def _own(o, coll):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    coll.objects.link(o)

class HumanFactory:
    def __init__(self, coll):
        self.coll = coll; self.baked = {}

    # ------------------------------------------------------------------ body
    def _human(self, rnd):
        m = TargetService.get_default_macro_info_dict()
        g = rnd.choice([0.0, 1.0]) * 0.85 + rnd.uniform(0.05, 0.12)       # mostly clearly male / female
        m.update(gender=g, age=rnd.uniform(0.35, 0.8), muscle=rnd.uniform(0.35, 0.65), weight=rnd.uniform(0.3, 0.75),
                 height=rnd.uniform(0.3, 0.75), proportions=rnd.uniform(0.4, 0.7))
        r = [rnd.random() for _ in range(3)]; s = sum(r)
        m['race'] = dict(african=r[0] / s, asian=r[1] / s, caucasian=r[2] / s)
        h = HumanService.create_human(mask_helpers=True, detailed_helpers=False, extra_vertex_groups=True,
                                      feet_on_ground=False, scale=0.1, macro_detail_dict=m)
        rig = HumanService.add_builtin_rig(h, 'cmu_mb', import_weights=True)
        for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'      # MPFB uses Euler; our keys are quaternions
        # feet on the ground: offset the rig object (the mesh follows as its child) -> pivots stay consistent
        foot = min(min(rig.data.bones[b].head_local.z, rig.data.bones[b].tail_local.z) for b in ('LeftFoot', 'LeftToeBase', 'RightFoot', 'RightToeBase'))
        import numpy as np
        co = np.empty(len(h.data.vertices) * 3, dtype=np.float32); h.data.vertices.foreach_get('co', co)
        self.lift = -float(co.reshape(-1, 3)[:, 2].min())
        return h, rig, g

    def _paint(self, h, rnd, female):
        me = h.data
        names = {g.index: g.name for g in h.vertex_groups}
        scalp = h.vertex_groups.get('scalp')
        dom, sc = [], []
        for v in me.vertices:
            best, bw, s_ = None, 0.0, 0.0
            for ge in v.groups:
                n = names[ge.group]
                if scalp is not None and ge.group == scalp.index: s_ = ge.weight
                elif n in ZONE or n in ('Head', 'Neck', 'Neck1') or 'Hand' in n or 'Thumb' in n or 'Finger' in n:
                    if ge.weight > bw: best, bw = n, ge.weight
            dom.append(best); sc.append(s_)
        skin_c = rnd.choice(SKIN)
        sleeves = rnd.random() < 0.7; shorts = rnd.random() < 0.12
        skirt = female and rnd.random() < 0.25
        top = rnd.choice(TOPS); bot = rnd.choice(BOTS) if not skirt else rnd.choice(TOPS)
        hair_long = female and rnd.random() < 0.7
        M = [mat(skin_c, 0.45, sss=0.15, sheen=0.0), mat(top), mat(bot), mat(rnd.choice(SHOES), 0.4), mat(rnd.choice(HAIR), 0.5, sheen=0.6)]
        for m_ in M: me.materials.append(m_)
        zmax = max(v.co.z for v in me.vertices)
        mi = []
        for p in me.polygons:
            vs = p.vertices; zones = {}
            for vi in vs:
                n = dom[vi]; z = ZONE.get(n, 'skin') if n else 'skin'
                if sc[vi] > 0.5: z = 'hair'
                zones[z] = zones.get(z, 0) + 1
            z = max(zones, key=zones.get)
            if z == 'sleeve': z = 'top' if sleeves else 'skin'
            if z == 'leg': z = 'skin' if shorts else 'bot'
            mi.append({'skin': 0, 'top': 1, 'bot': 2, 'shoe': 3, 'hair': 4}[z])
        me.polygons.foreach_set('material_index', mi)
        # long hair: paint the back of the neck too
        if hair_long:
            for p, d in zip(me.polygons, mi):
                c = p.center
                if d == 0 and dom[p.vertices[0]] in ('Neck', 'Neck1', 'Head') and c.y > 0.02: p.material_index = 4
        for p in me.polygons: p.use_smooth = True

    # ------------------------------------------------------------------ mocap: bake a BVH onto a cmu_mb rig by bone direction
    def bake(self, bvh, ref_rig):
        if bvh in self.baked: return self.baked[bvh]
        before = set(bpy.data.objects)
        bpy.ops.import_anim.bvh(filepath=bvh, global_scale=PP.SCALE, frame_start=-1, use_fps_scale=True,
                                update_scene_fps=False, rotate_mode='QUATERNION', axis_forward='-Z', axis_up='Y')
        src = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
        a0, a1 = src.animation_data.action.frame_range
        tgt = ref_rig
        # frame alignment: rest skeletons -> forward/up axes
        def axes(arm):
            b = arm.data.bones
            up = (b['Head'].head_local - b['Hips'].head_local).normalized()
            right = (b['RightUpLeg'].head_local - b['LeftUpLeg'].head_local); right = (right - up * right.dot(up)).normalized()
            fwd = up.cross(right).normalized()
            toe = b['LeftToeBase'].tail_local - b['LeftFoot'].head_local
            if toe.dot(fwd) < 0: fwd, right = -fwd, -right
            return Matrix((right, fwd, up)).transposed()
        Rs = (src.matrix_world.to_3x3() @ axes(src)); Rt = (tgt.matrix_world.to_3x3() @ axes(tgt))
        R = Rt @ Rs.inverted()                             # world(src) -> world(tgt) orientation
        leg_s = src.data.bones['LeftUpLeg'].length + src.data.bones['LeftLeg'].length
        leg_t = tgt.data.bones['LeftUpLeg'].length + tgt.data.bones['LeftLeg'].length
        ratio = leg_t / max(leg_s, 1e-6) * (tgt.matrix_world.to_scale().x / src.matrix_world.to_scale().x)
        act = bpy.data.actions.new('walk_' + os.path.basename(bvh))
        tgt.animation_data_create(); tgt.animation_data.action = act
        order = [b.name for b in tgt.data.bones if b.name in src.pose.bones]
        order.sort(key=lambda n: len(tgt.data.bones[n].parent_recursive))
        sc = bpy.context.scene
        sc.frame_set(int(a0) + 1); bpy.context.view_layer.update()
        hips0 = src.matrix_world @ src.pose.bones['Hips'].head
        tw = tgt.matrix_world; tinv = tw.inverted()
        rest_hips = tw @ tgt.pose.bones['Hips'].head
        for f in range(int(a0) + 1, int(a1) + 1):
            sc.frame_set(f); bpy.context.view_layer.update()
            for n in order:
                sp = src.pose.bones[n]; tp = tgt.pose.bones[n]
                dsrc = (src.matrix_world.to_3x3() @ (sp.tail - sp.head)).normalized()
                dwant = (R @ dsrc).normalized()
                if dsrc.length < 1e-6: continue
                cur = (tw.to_3x3() @ (tp.tail - tp.head)).normalized()
                q = cur.rotation_difference(dwant)
                Mw = tw @ tp.matrix; loc = Mw.to_translation()
                if n == 'Hips':
                    loc = rest_hips + R @ ((src.matrix_world @ sp.head) - hips0) * ratio
                    loc.z = rest_hips.z + (R @ ((src.matrix_world @ sp.head) - hips0) * ratio).z
                Mw2 = Matrix.Translation(loc) @ q.to_matrix().to_4x4() @ Matrix.Translation(-Mw.to_translation()) @ Mw
                Mw2.translation = loc
                tp.matrix = tinv @ Mw2
                bpy.context.view_layer.update()
                tp.keyframe_insert('rotation_quaternion', frame=f)
                if n == 'Hips': tp.keyframe_insert('location', frame=f)
        tgt.animation_data.action = None
        for pb in tgt.pose.bones: pb.matrix_basis = Matrix.Identity(4)
        bpy.data.objects.remove(src)
        self.baked[bvh] = (act, (a0, a1))
        return self.baked[bvh]

    # ------------------------------------------------------------------ public
    def make(self, seed, walker_bvh=None):
        rnd = random.Random(seed)
        h, rig, g = self._human(rnd)
        self._paint(h, rnd, female=g < 0.5)
        root = bpy.data.objects.new('person', None); self.coll.objects.link(root)
        for o in (h, rig): _own(o, self.coll)
        for o in h.children: _own(o, self.coll)
        rig.parent = root; rig.location = (0, 0, self.lift)
        rig.animation_data_create()
        if walker_bvh:
            act, rng = self.bake(walker_bvh, rig)
            a = act.copy(); rig.animation_data.action = a
        else:
            a = bpy.data.actions.new('idle'); rig.animation_data.action = a
            for pb in rig.pose.bones: pb.keyframe_insert('rotation_quaternion', frame=1)
        return dict(root=root, arm=rig, action=a, h=1.0, rnd=rnd, mesh=h)
