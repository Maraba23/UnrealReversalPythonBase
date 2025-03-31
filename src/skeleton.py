class Skeleton():
    class Bones:
        head = 62
        neck_01 = 61
        clavicle_r = 34
        upperarm_r = 35
        hand_r = 98
        clavicle_l = 6
        upperarm_l = 7
        hand_l = 97
        spine_03 = 4
        spine_02 = 3
        spine_01 = 2
        pelvis = 1
        thigh_r = 73
        calf_r = 74
        foot_r = 94
        ball_r = 78
        thigh_l = 64
        calf_l = 65
        foot_l = 93
        ball_l = 69

    bone_pairs = [
        (Bones.head, Bones.neck_01),
        (Bones.neck_01, Bones.clavicle_r),
        (Bones.clavicle_r, Bones.upperarm_r),
        (Bones.upperarm_r, Bones.hand_r),
        (Bones.neck_01, Bones.clavicle_l),
        (Bones.clavicle_l, Bones.upperarm_l),
        (Bones.upperarm_l, Bones.hand_l),
        (Bones.neck_01, Bones.spine_03),
        (Bones.spine_03, Bones.spine_02),
        (Bones.spine_02, Bones.spine_01),
        (Bones.spine_01, Bones.pelvis),
        (Bones.pelvis, Bones.thigh_r),
        (Bones.thigh_r, Bones.calf_r),
        (Bones.calf_r, Bones.foot_r),
        (Bones.foot_r, Bones.ball_r),
        (Bones.pelvis, Bones.thigh_l),
        (Bones.thigh_l, Bones.calf_l),
        (Bones.calf_l, Bones.foot_l),
        (Bones.foot_l, Bones.ball_l)
    ]

    @staticmethod
    def draw_skeleton(pm, proc, mesh_ptr, camera_manager, screen_width, screen_height, color=None, thickness=1.5):
        from functions import Mesh, Engine
        if color is None:
            color = pm.get_color("white")

        mesh = Mesh()
        bone_cache = {}

        for bone1, bone2 in Skeleton.bone_pairs:
            if bone1 not in bone_cache:
                bone_cache[bone1] = mesh.get_bone_with_rotation(proc, mesh_ptr, bone1, pm)
            if bone2 not in bone_cache:
                bone_cache[bone2] = mesh.get_bone_with_rotation(proc, mesh_ptr, bone2, pm)

        for bone1, bone2 in Skeleton.bone_pairs:
            pos1 = Engine.world_to_screen(proc, camera_manager, bone_cache[bone1], screen_width, screen_height, pm)
            pos2 = Engine.world_to_screen(proc, camera_manager, bone_cache[bone2], screen_width, screen_height, pm)

            if pos1.x > 0 and pos1.y > 0 and pos2.x > 0 and pos2.y > 0:
                pm.draw_line(pos1.x, pos1.y, pos2.x, pos2.y, color, thickness)
