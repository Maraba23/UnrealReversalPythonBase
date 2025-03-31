import math
import ctypes
from math import sqrt
import struct

M_PI = math.pi

def _powf(a, b): return a ** b

def _sinf(x): return math.sin(x)
def _cosf(x): return math.cos(x)

def abs_val(t): return abs(t)

def fast_sqrt(x):
    u = ctypes.union(float=x)
    i = ctypes.cast(ctypes.pointer(u), ctypes.POINTER(ctypes.c_int)).contents
    i = (i.value >> 1) + 0x1FC00000
    u = ctypes.cast(ctypes.pointer(i), ctypes.POINTER(ctypes.c_float)).contents
    x = u.value
    x = x + x / x
    return 0.25 * x + x / x

def custom_cosf(x):
    cos_sign_tbl = [1, -1, -1, 1]
    cos_off_tbl = [0.0, -M_PI / 2., 0, -M_PI / 2.]
    quadrant = int(x * (2. / M_PI))
    x -= quadrant * (M_PI / 2.)
    quadrant &= 0x3
    x += cos_off_tbl[quadrant]
    x2 = -(x * x)
    result = 0
    result += 1. / math.factorial(8)
    result *= x2
    result += 1. / math.factorial(6)
    result *= x2
    result += 1. / math.factorial(4)
    result *= x2
    result += 1. / math.factorial(2)
    result *= x2
    result += 1
    result *= cos_sign_tbl[quadrant]
    return result

def custom_sinf(x):
    sin_off_tbl = [0.0, -M_PI / 2., 0, -M_PI / 2.]
    sin_sign_tbl = [1, -1, -1, 1]
    quadrant = int(x * (2. / M_PI))
    x -= quadrant * (M_PI / 2.)
    quadrant = (quadrant - 1) & 0x3
    x += sin_off_tbl[quadrant]
    x2 = -(x * x)
    result = 0
    result += 1. / math.factorial(8)
    result *= x2
    result += 1. / math.factorial(6)
    result *= x2
    result += 1. / math.factorial(4)
    result *= x2
    result += 1. / math.factorial(2)
    result *= x2
    result += 1
    result *= sin_sign_tbl[quadrant]
    return result

class Vector2:
    def __init__(self, x=0.0, y=0.0): self.x, self.y = x, y
    def __add__(self, v): return Vector2(self.x + v.x, self.y + v.y)
    def __sub__(self, v): return Vector2(self.x - v.x, self.y - v.y)
    def __mul__(self, val): return Vector2(self.x * val, self.y * val)
    def __truediv__(self, val): return Vector2(self.x / val, self.y / val)
    def dot(self, v): return self.x * v.x + self.y * v.y
    def length(self): return sqrt(self.x ** 2 + self.y ** 2)
    def zero(self): return abs(self.x) < 0.1 and abs(self.y) < 0.1
    def normalize(self): self.clamp(); return self
    def clamp(self):
        self.y = max(min(self.y, 180.0), -180.0)
        self.x = max(min(self.x, 89.0), -89.0)

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0): self.x, self.y, self.z = x, y, z
    def __add__(self, v): return Vector3(self.x + v.x, self.y + v.y, self.z + v.z)
    def __sub__(self, v): return Vector3(self.x - v.x, self.y - v.y, self.z - v.z)
    def __mul__(self, val): return Vector3(self.x * val, self.y * val, self.z * val)
    def __truediv__(self, val): return Vector3(self.x / val, self.y / val, self.z / val)
    def dot(self, v): return self.x * v.x + self.y * v.y + self.z * v.z
    def length(self): return sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    def zero(self): return abs(self.x) < 0.1 and abs(self.y) < 0.1 and abs(self.z) < 0.1
    def normalize(self, tol=1e-6):
        length = self.length()
        if length > tol:
            return self / length
        return self
    def clamp(self):
        self.y = max(min(self.y, 180.0), -180.0)
        self.x = max(min(self.x, 89.0), -89.0)
        self.z = 0

class FVector(Vector3):
    def Size(self): return self.length()
    def Normalize(self): return self.normalize()

class Quaternion:
    def __init__(self, x=0, y=0, z=0, w=0): self.x, self.y, self.z, self.w = x, y, z, w

def deg_to_rad(x): return x * (M_PI / 180.0)

class Matrix:
    def __init__(self):
        self.m = [[0.0 for _ in range(4)] for _ in range(4)]

    @staticmethod
    def from_rotation(origin: Vector3, rotation: Vector3):
        pitch = deg_to_rad(rotation.x)
        yaw   = deg_to_rad(rotation.y)
        roll  = deg_to_rad(rotation.z)

        SP, CP = custom_sinf(pitch), custom_cosf(pitch)
        SY, CY = custom_sinf(yaw), custom_cosf(yaw)
        SR, CR = custom_sinf(roll), custom_cosf(roll)

        mat = Matrix()
        mat.m[0][0] = CP * CY
        mat.m[0][1] = CP * SY
        mat.m[0][2] = SP
        mat.m[1][0] = SR * SP * CY - CR * SY
        mat.m[1][1] = SR * SP * SY + CR * CY
        mat.m[1][2] = -SR * CP
        mat.m[2][0] = -CR * SP * CY - SR * SY
        mat.m[2][1] = CR * SP * SY - SR * CY
        mat.m[2][2] = CR * CP
        mat.m[3][0], mat.m[3][1], mat.m[3][2] = origin.x, origin.y, origin.z
        mat.m[3][3] = 1.0
        return mat

class Transform:
    def __init__(self, rot: Quaternion, trans: Vector3, scale: Vector3):
        self.rotation = rot
        self.translation = trans
        self.scale = scale

    def to_matrix_with_scale(self):
        x2 = self.rotation.x + self.rotation.x
        y2 = self.rotation.y + self.rotation.y
        z2 = self.rotation.z + self.rotation.z

        xx2 = self.rotation.x * x2
        yy2 = self.rotation.y * y2
        zz2 = self.rotation.z * z2
        yz2 = self.rotation.y * z2
        wx2 = self.rotation.w * x2
        xy2 = self.rotation.x * y2
        wz2 = self.rotation.w * z2
        xz2 = self.rotation.x * z2
        wy2 = self.rotation.w * y2

        m = [[0.0 for _ in range(4)] for _ in range(4)]
        m[0][0] = (1.0 - (yy2 + zz2)) * self.scale.x
        m[0][1] = (xy2 + wz2) * self.scale.x
        m[0][2] = (xz2 - wy2) * self.scale.x
        m[0][3] = 0.0

        m[1][0] = (xy2 - wz2) * self.scale.y
        m[1][1] = (1.0 - (xx2 + zz2)) * self.scale.y
        m[1][2] = (yz2 + wx2) * self.scale.y
        m[1][3] = 0.0

        m[2][0] = (xz2 + wy2) * self.scale.z
        m[2][1] = (yz2 - wx2) * self.scale.z
        m[2][2] = (1.0 - (xx2 + yy2)) * self.scale.z
        m[2][3] = 0.0

        m[3][0] = self.translation.x
        m[3][1] = self.translation.y
        m[3][2] = self.translation.z
        m[3][3] = 1.0

        return Matrix(m)

