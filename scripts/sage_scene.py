import math

import bpy
from mathutils import Vector

FT = 0.3048
SIDE_WALL = 5 / 12 * FT
FRONT_WALL = 6 / 12 * FT
SHARED_WALL = 11 / 12 * FT
BACK_WALL = 5 / 12 * FT
WALL_HEIGHT = 9.0 * FT
LIVING_X = 16.0 * FT
LIVING_WIDTH = 16.25 * FT
LIVING_DEPTH = (13 + 10 / 12) * FT
DINING_RIGHT_STEP = 1.49 * FT
DINING_WIDTH = LIVING_WIDTH + DINING_RIGHT_STEP
DINING_DEPTH = (11 + 10 / 12) * FT
DINING_LEFT_INSET = 0.59 * FT
DINING_LEFT_FRONT_JOG = -0.46 * FT
SHARED_OPENING_WIDTH = 9.13 * FT
SHARED_OPENING_LEFT = 3.25 * FT


def material(name, color):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    return value


def cube(name, location, scale, parent, material_value=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    target_collection = parent.users_collection[0]
    for source_collection in list(obj.users_collection):
        source_collection.objects.unlink(obj)
    target_collection.objects.link(obj)
    if material_value:
        obj.data.materials.append(material_value)
    return obj


def empty(name, parent=None, collection=None):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.parent = parent
    (collection or bpy.context.collection).objects.link(obj)
    return obj


def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, parent, collection, fov=75):
    data = bpy.data.cameras.new(name)
    data.type = "PERSP"
    data.sensor_fit = "VERTICAL"
    data.angle_y = math.radians(fov)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.parent = parent
    point_camera(obj, target)
    return obj
