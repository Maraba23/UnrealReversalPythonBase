from gameStruct import *
from offsets import *

class FNameDecrypt():
    def __init__(self, process, base_address, gnames_offset, pm):
        self.process = process
        self.base_address = base_address
        self.gnames_offset = gnames_offset
        self.pm = pm

    def GetNameFromFName(self, fName: int) -> str:
        chunkOffset = (fName >> 16)
        nameOffset = fName & 0xFFFF
        name_pool_chunk_ptr = self.base_address + self.gnames_offset + ((chunkOffset + 2) * 8)
        name_pool_chunk = self.pm.r_uint64(self.process, name_pool_chunk_ptr)

        entry_offset = name_pool_chunk + (2 * nameOffset)
        name_entry = self.pm.r_int16(self.process, entry_offset)

        name_length = name_entry >> 6

        if name_length > 0:
            name_bytes = self.pm.r_bytes(self.process, entry_offset + 2, name_length)
            name = bytes(name_bytes).decode('utf-8', errors='ignore')
            return name
        else:
            return ""
        

class Engine():
    def world_to_screen(process, camera_manager, world_location, overlay_width, overlay_height, pm):
        camera_location = pm.r_vec3(process, camera_manager + OFFSET_CAMERA_CACHE_PRIVATE + 0x10)
        camera_rotation = pm.r_vec3(process, camera_manager + OFFSET_CAMERA_CACHE_PRIVATE + 0x1C)
        fov = pm.r_float(process, camera_manager + OFFSET_CAMERA_CACHE_PRIVATE + 0x30)

        rotation_matrix = Matrix.from_rotation(camera_location, camera_rotation)

        vAxisX = Vector3(rotation_matrix.m[0][0], rotation_matrix.m[0][1], rotation_matrix.m[0][2])
        vAxisY = Vector3(rotation_matrix.m[1][0], rotation_matrix.m[1][1], rotation_matrix.m[1][2])
        vAxisZ = Vector3(rotation_matrix.m[2][0], rotation_matrix.m[2][1], rotation_matrix.m[2][2])

        vDelta = world_location - camera_location

        vTransformed = Vector3(
            vDelta.dot(vAxisY),
            vDelta.dot(vAxisZ),
            vDelta.dot(vAxisX)
        )

        if vTransformed.z < 1.0:
            vTransformed.z = 1.0

        screen_center_x = overlay_width / 2.0
        screen_center_y = overlay_height / 2.0
        fov_rad = math.radians(fov) / 2.0

        screen_x = screen_center_x + vTransformed.x * (screen_center_x / math.tan(fov_rad)) / vTransformed.z
        screen_y = screen_center_y - vTransformed.y * (screen_center_x / math.tan(fov_rad)) / vTransformed.z

        return Vector3(screen_x, screen_y, 0)
    
class Mesh():
    def matrix_multiplication(self, a, b):
        result = [[0.0] * 4 for _ in range(4)]

        for i in range(4):
            for j in range(4):
                result[i][j] = sum(a.m[i][k] * b.m[k][j] for k in range(4))

        return Matrix(result)

    def get_ftransform(self, proc, addr, pm):
        data = pm.r_bytes(proc, addr, 0x30)
        if not data:
            return None

        x = struct.unpack('f', bytes(data[0:4]))[0]
        y = struct.unpack('f', bytes(data[4:8]))[0]
        z = struct.unpack('f', bytes(data[8:12]))[0]
        w = struct.unpack('f', bytes(data[12:16]))[0]
        trans_x = struct.unpack('f', bytes(data[16:20]))[0]
        trans_y = struct.unpack('f', bytes(data[20:24]))[0]
        trans_z = struct.unpack('f', bytes(data[24:28]))[0]
        scale_x = struct.unpack('f', bytes(data[32:36]))[0]
        scale_y = struct.unpack('f', bytes(data[36:40]))[0]
        scale_z = struct.unpack('f', bytes(data[44:48]))[0]

        rot = Quaternion(x, y, z, w)
        trans = Vector3(trans_x, trans_y, trans_z)
        scale = Vector3(scale_x, scale_y, scale_z)

        return Transform(rot, trans, scale)


    def get_bone_index(self, proc, mesh, index, pm):
        offsets = [0x0, 0x10, 0x18, 0x28]
        bone_array = 0

        for offset in offsets:
            bone_array_address = mesh + OFFSET_BONE_ARRAY + offset
            print(f"Mesh: {hex(mesh)} | Offset: {offset} | Address to read: {hex(bone_array_address)}")
            bone_array = pm.r_uint64(proc, mesh + OFFSET_BONE_ARRAY + offset)
            if 0x10000 < bone_array < 0x7FFFFFFFFFFF:
                break

        if not bone_array:
            return None

        addr = bone_array + (index * 0x60)  # ou 0x30 para outros jogos
        data = pm.r_bytes(proc, addr, 0x30)

        if data is None:
            return None

        # Parse Transform struct (quaternion + translation + scale)
        x = struct.unpack('f', bytes(data[0:4]))[0]
        y = struct.unpack('f', bytes(data[4:8]))[0]
        z = struct.unpack('f', bytes(data[8:12]))[0]
        w = struct.unpack('f', bytes(data[12:16]))[0]
        trans_x = struct.unpack('f', bytes(data[16:20]))[0]
        trans_y = struct.unpack('f', bytes(data[20:24]))[0]
        trans_z = struct.unpack('f', bytes(data[24:28]))[0]
        scale_x = struct.unpack('f', bytes(data[32:36]))[0]
        scale_y = struct.unpack('f', bytes(data[36:40]))[0]
        scale_z = struct.unpack('f', bytes(data[44:48]))[0]

        rot = Quaternion(x, y, z, w)
        trans = Vector3(trans_x, trans_y, trans_z)
        scale = Vector3(scale_x, scale_y, scale_z)

        return Transform(rot, trans, scale)

    def get_bone_with_rotation(self, proc, mesh, bone_id, pm):
        bone = self.get_bone_index(proc, mesh, bone_id, pm)
        if bone is None:
            return Vector3()

        # ComponentToWorld também é um f_transform
        component = self.get_ftransform(proc, mesh + OFFSET_COMPONENT_TO_WORLD, pm)
        if component is None:
            return Vector3()

        bone_matrix = bone.to_matrix_with_scale()
        component_matrix = component.to_matrix_with_scale()

        result = self.matrix_multiplication(bone_matrix, component_matrix)
        return Vector3(result.m[3][0], result.m[3][1], result.m[3][2])
