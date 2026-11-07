"""Pedestrians: CMU mocap (BVH) skeletons dressed as simple clothed mannequins.
Build people BEFORE the city (bpy.ops imports get slow in a big scene), then place them.

  P = make_person(bvh_path, seed)            -> dict(root=empty, arm=armature, ...)
  pose_stand(P), pose_look_up(P, frame, amount), pose_cover(P, frame)  (keyframed, for idle people)
  walkers keep their mocap; cut_after(P, frame) freezes them and lets you add a cover pose.
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion

SCALE = 0.056444          # CMU BVH units -> metres
SKIN = [(0.85, 0.64, 0.5), (0.62, 0.43, 0.3), (0.42, 0.27, 0.17), (0.93, 0.76, 0.62), (0.3, 0.2, 0.13)]
TOPS = [(0.05, 0.05, 0.06), (0.6, 0.6, 0.62), (0.08, 0.12, 0.25), (0.45, 0.06, 0.05), (0.75, 0.72, 0.62),
        (0.15, 0.25, 0.15), (0.9, 0.9, 0.88), (0.3, 0.2, 0.12), (0.55, 0.42, 0.25)]
BOTS = [(0.04, 0.05, 0.08), (0.1, 0.13, 0.22), (0.22, 0.22, 0.24), (0.35, 0.3, 0.22), (0.05, 0.05, 0.05)]
_mats = {}
def _mat(rgb, rough=0.7):
    k = (tuple(round(c, 3) for c in rgb), rough)
    if k not in _mats:
        m = bpy.data.materials.new('ppl'); b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
        b.inputs['Sheen Weight'].default_value = 0.3
        _mats[k] = m
    return _mats[k]

# bone -> (radius at head, radius at tail, part) ; part decides the material
BODY = {
    'LeftUpLeg': (0.085, 0.06, 'bot'), 'RightUpLeg': (0.085, 0.06, 'bot'),
    'LeftLeg': (0.06, 0.045, 'bot'), 'RightLeg': (0.06, 0.045, 'bot'),
    'LeftFoot': (0.05, 0.045, 'shoe'), 'RightFoot': (0.05, 0.045, 'shoe'),
    'LowerBack': (0.15, 0.15, 'top'), 'Spine': (0.15, 0.16, 'top'), 'Spine1': (0.16, 0.13, 'top'),
    'Neck': (0.05, 0.05, 'skin'), 'Neck1': (0.05, 0.05, 'skin'),
    'LeftArm': (0.055, 0.045, 'top'), 'RightArm': (0.055, 0.045, 'top'),
    'LeftForeArm': (0.045, 0.035, 'sleeve'), 'RightForeArm': (0.045, 0.035, 'sleeve'),
    'LeftHand': (0.04, 0.03, 'skin'), 'RightHand': (0.04, 0.03, 'skin'),
}

def _capsule(name, length, r0, r1, mat, seg=10):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for k, (z, r) in enumerate([(-r0 * 0.6, r0 * 0.55), (0, r0), (length, r1), (length + r1 * 0.6, r1 * 0.55)]):
        ring = [bm.verts.new((r * math.cos(a), z, r * math.sin(a) * 0.85)) for a in [i * 2 * math.pi / seg for i in range(seg)]]
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(seg): bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    return me

def _sphere(name, r, mat, sy=1.15):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=r)
    for v in bm.verts: v.co.y *= sy
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat); return me

def make_person(bvh, seed, coll, fps=30):
    rnd = random.Random(seed)
    before = set(bpy.data.objects)
    bpy.ops.import_anim.bvh(filepath=bvh, global_scale=SCALE, frame_start=-1, use_fps_scale=True,
                            update_scene_fps=False, rotate_mode='QUATERNION', axis_forward='-Z', axis_up='Y')
    arm = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
    for uc in list(arm.users_collection): uc.objects.unlink(arm)
    coll.objects.link(arm)
    h = rnd.uniform(0.93, 1.07)
    root = bpy.data.objects.new('person', None); coll.objects.link(root)
    arm.parent = root; arm.scale = (h,) * 3
    skin = _mat(rnd.choice(SKIN), 0.55); top = _mat(rnd.choice(TOPS)); bot = _mat(rnd.choice(BOTS))
    sleeve = top if rnd.random() < 0.7 else skin
    shoe = _mat((0.03, 0.03, 0.03), 0.4)
    hair = _mat(rnd.choice([(0.03, 0.02, 0.015), (0.15, 0.08, 0.03), (0.35, 0.22, 0.1), (0.05, 0.05, 0.05)]), 0.5)
    mats = dict(top=top, bot=bot, skin=skin, sleeve=sleeve, shoe=shoe)
    girth = rnd.uniform(0.9, 1.15)
    for b in arm.data.bones:
        if b.name in BODY:
            r0, r1, part = BODY[b.name]
            L = max(b.length, 0.02)
            me = _capsule(b.name, L, r0 * girth, r1 * girth, mats[part])
        elif b.name == 'Head':
            me = _sphere('head', 0.105, skin)
        else:
            continue
        o = bpy.data.objects.new('p_' + b.name, me); coll.objects.link(o)
        if b.name in ('LowerBack', 'Spine', 'Spine1'): o.scale = (1.55, 1.0, 1.05)
        o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = b.name
        # bone-parented children sit at the bone TAIL; move them back to the head, along bone Y
        o.location = (0, -b.length, 0)
        if b.name == 'Head':
            o.location = (0, -b.length + 0.06, 0.01)
            hr = bpy.data.objects.new('p_hair', _sphere('hair', 0.11, hair, 1.0)); coll.objects.link(hr)
            hr.parent = arm; hr.parent_type = 'BONE'; hr.parent_bone = 'Head'; hr.location = (0, -b.length + 0.09, -0.015)
            hr.scale = (1.0, 0.75, 1.0)
    act = arm.animation_data.action
    return dict(root=root, arm=arm, action=act, h=h, rnd=rnd)

# --------------------------------------------------------------------------- posing helpers
def _pb(P, name): return P['arm'].pose.bones[name]

def _aim(P, name, direction, frame):
    """rotate a pose bone so it points along `direction` (armature space), keyframe it"""
    arm = P['arm']; bpy.context.view_layer.update()
    pb = _pb(P, name)
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    M = pb.matrix.copy(); loc = M.to_translation()
    R = q.to_matrix().to_4x4() @ Matrix.Translation(-loc) @ M
    pb.matrix = Matrix.Translation(loc) @ R
    pb.keyframe_insert('rotation_quaternion', frame=frame)

def _turn(P, name, axis, deg, frame):
    arm = P['arm']; bpy.context.view_layer.update()
    pb = _pb(P, name); M = pb.matrix.copy(); loc = M.to_translation()
    R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    pb.matrix = Matrix.Translation(loc) @ R @ Matrix.Translation(-loc) @ M
    pb.keyframe_insert('rotation_quaternion', frame=frame)

def _frame_axes(P):
    """facing / up / right in armature space, from the rest skeleton"""
    bones = P['arm'].data.bones
    up = (bones['Head'].head_local - bones['Hips'].head_local).normalized()
    right = (bones['RightUpLeg'].head_local - bones['LeftUpLeg'].head_local)
    right = (right - up * right.dot(up)).normalized()
    fwd = up.cross(right).normalized()
    toe = bones['LeftToeBase'].tail_local - bones['LeftFoot'].head_local
    if toe.dot(fwd) < 0: fwd = -fwd; right = -right
    return fwd, up, right

def freeze_at(P, src_frame, from_frame):
    """drop all mocap keys after from_frame and hold the pose of src_frame"""
    act = P['action']
    sc = bpy.context.scene; sc.frame_set(src_frame)
    vals = {}
    for pb in P['arm'].pose.bones:
        vals[pb.name] = (pb.location.copy(), pb.rotation_quaternion.copy())
    for fc in act.fcurves if hasattr(act, 'fcurves') else []:
        pts = [k for k in fc.keyframe_points if k.co.x > from_frame]
        for k in reversed(pts): fc.keyframe_points.remove(k)
    _clear_after(P, from_frame)
    for pb in P['arm'].pose.bones:
        pb.location, pb.rotation_quaternion = vals[pb.name]
        pb.keyframe_insert('location', frame=from_frame); pb.keyframe_insert('rotation_quaternion', frame=from_frame)

def _fcurves(act):
    if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
    out = []   # Blender 4.4+/5.x layered actions
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out

def _clear_after(P, frame):
    for fc in _fcurves(P['action']):
        pts = [i for i, k in enumerate(fc.keyframe_points) if k.co.x > frame]
        for i in reversed(pts): fc.keyframe_points.remove(fc.keyframe_points[i])

def _clear_all(P):
    for fc in _fcurves(P['action']):
        while len(fc.keyframe_points): fc.keyframe_points.remove(fc.keyframe_points[0])

def hold_pose(P, src_frame, frame):
    """key the mocap pose of src_frame at `frame` (after clearing later keys)"""
    sc = bpy.context.scene; sc.frame_set(src_frame)
    vals = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in P['arm'].pose.bones}
    _clear_after(P, frame - 0.5)
    for pb in P['arm'].pose.bones:
        pb.location, pb.rotation_quaternion = vals[pb.name]
        pb.keyframe_insert('location', frame=frame); pb.keyframe_insert('rotation_quaternion', frame=frame)

def make_idle(P, src_frame=2):
    """turn a walker into a standing person: keep only one mocap pose, legs together, arms down"""
    sc = bpy.context.scene; sc.frame_set(src_frame)
    vals = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in P['arm'].pose.bones}
    _clear_all(P)
    for pb in P['arm'].pose.bones:
        pb.location, pb.rotation_quaternion = vals[pb.name]
    hips = _pb(P, 'Hips'); hips.location.x = 0; hips.location.z = 0
    for pb in P['arm'].pose.bones:
        if pb.name.startswith(('Left', 'Right', 'LHip', 'RHip')): pb.rotation_quaternion = Quaternion()
    for pb in P['arm'].pose.bones:
        pb.keyframe_insert('location', frame=1); pb.keyframe_insert('rotation_quaternion', frame=1)
    fwd, up, right = _frame_axes(P)
    sgn = P['rnd'].choice([-1, 1])
    _aim(P, 'LeftArm', -up * 1.0 - right * 0.18 + fwd * 0.05, 1)
    _aim(P, 'RightArm', -up * 1.0 + right * 0.18 + fwd * 0.05, 1)
    _aim(P, 'LeftForeArm', -up * 1.0 + fwd * 0.25, 1)
    _aim(P, 'RightForeArm', -up * 1.0 + fwd * 0.25 + right * 0.05 * sgn, 1)
    _aim(P, 'LeftUpLeg', -up - right * 0.04, 1); _aim(P, 'RightUpLeg', -up + right * 0.04, 1)
    _aim(P, 'LeftLeg', -up, 1); _aim(P, 'RightLeg', -up, 1)
    _aim(P, 'LeftFoot', -up * 0.35 + fwd, 1); _aim(P, 'RightFoot', -up * 0.35 + fwd, 1)

def look_up(P, frame, deg=35, point=False):
    fwd, up, right = _frame_axes(P)
    _turn(P, 'Neck', right, -deg * 0.4, frame); _turn(P, 'Head', right, -deg * 0.6, frame)
    if point:
        _aim(P, 'RightArm', up * 0.9 + fwd * 0.8 + right * 0.1, frame); _aim(P, 'RightForeArm', up * 1.0 + fwd * 0.6, frame)

def cover(P, frame, lean=40):
    """duck and cover: hunch forward, forearms over the head, knees bent a little"""
    fwd, up, right = _frame_axes(P)
    _turn(P, 'LowerBack', right, lean * 0.5, frame); _turn(P, 'Spine', right, lean * 0.5, frame)
    _turn(P, 'Neck', right, 25, frame)
    bpy.context.view_layer.update()
    _aim(P, 'LeftArm', up * 0.7 + fwd * 0.6 - right * 0.5, frame); _aim(P, 'RightArm', up * 0.7 + fwd * 0.6 + right * 0.5, frame)
    _aim(P, 'LeftForeArm', right * 0.9 + up * 0.35, frame); _aim(P, 'RightForeArm', -right * 0.9 + up * 0.35, frame)
