import pyMeow as pm
from variables import *
from offsets import *
from functions import FNameDecrypt, Engine, Mesh
import threading
import time
from gameStruct import *
from skeleton import Skeleton

entity_list = []
entity_lock = threading.Lock()

proc = pm.open_process(GAME_NAME)
print("Process ID:", proc["pid"])

base_address = pm.get_module(proc, GAME_NAME)["base"]
print("Base Address:", hex(base_address))

pm.overlay_init(title="Unreal ESP", fps=120)

def update_entities():
    global entity_list

    while True:
        try:
            new_entities = []

            GameData.GWorld = pm.r_uint64(proc, base_address + GWORLD_OFFSET)
            print("GWorld Address:", hex(GameData.GWorld))
            if GameData.GWorld == 0:
                continue
            GameData.GameInstance = pm.r_uint64(proc, GameData.GWorld + OFFSET_OWNING_GAME_INSTANCE)
            print("GameInstance Address:", hex(GameData.GameInstance))
            if GameData.GameInstance == 0:
                continue
            GameData.LocalPlayerArray = pm.r_uint64(proc, GameData.GameInstance + OFFSET_LOCAL_PLAYERS)
            print("LocalPlayerArray Address:", hex(GameData.LocalPlayerArray))
            if GameData.LocalPlayerArray == 0:
                continue
            GameData.LocalPlayer = pm.r_uint64(proc, GameData.LocalPlayerArray)
            print("LocalPlayer Address:", hex(GameData.LocalPlayer))
            if GameData.LocalPlayer == 0:
                continue
            GameData.LocalPlayerController = pm.r_uint64(proc, GameData.LocalPlayer + OFFSET_PLAYER_CONTROLLER)
            print("LocalPlayerController Address:", hex(GameData.LocalPlayerController))
            if GameData.LocalPlayerController == 0:
                continue
            GameData.LocalPlayerPawn = pm.r_uint64(proc, GameData.LocalPlayerController + OFFSET_ACKNOWLEDGED_PAWN)
            print("LocalPlayerPawn Address:", hex(GameData.LocalPlayerPawn))
            if GameData.LocalPlayerPawn == 0:
                continue
            GameData.LocalPlayerRoot = pm.r_uint64(proc, GameData.LocalPlayerPawn + OFFSET_ROOT_COMPONENT)
            print("LocalPlayerRoot Address:", hex(GameData.LocalPlayerRoot))
            if GameData.LocalPlayerRoot == 0:
                continue
            GameData.PersistentLevel = pm.r_uint64(proc, GameData.GWorld + OFFSET_PERSISTENT_LEVEL)
            print("PersistentLevel Address:", hex(GameData.PersistentLevel))
            if GameData.PersistentLevel == 0:
                continue
            GameData.ActorArray = pm.r_uint64(proc, GameData.PersistentLevel + OFFSET_ACTOR_ARRAY)
            print("ActorArray Address:", hex(GameData.ActorArray))
            if GameData.ActorArray == 0:
                continue
            GameData.ActorCount = pm.r_uint(proc, GameData.PersistentLevel + OFFSET_ACTOR_COUNT)
            print("ActorCount:", GameData.ActorCount)
            if GameData.ActorCount == 0:
                continue

            FName = FNameDecrypt(proc, base_address, GNAMES_OFFSET, pm)

            for i in range(GameData.ActorCount):
                actor_pawn = pm.r_uint64(proc, GameData.ActorArray + (i * 0x8))
                if actor_pawn == GameData.LocalPlayerPawn:
                    continue
                actor_id = pm.r_int(proc, actor_pawn + OFFSET_ACTOR_ID)
                actor_name = FName.GetNameFromFName(actor_id)

                if is_relevant_entity(actor_name):
                    entity = Entity()
                    entity.actor_id = actor_id
                    entity.actor_name = actor_name
                    entity.actor_pawn = actor_pawn
                    entity.actor_state = pm.r_uint64(proc, actor_pawn + OFFSET_PLAYER_STATE)
                    entity.actor_mesh = pm.r_uint64(proc, actor_pawn + OFFSET_ACTOR_MESH)
                    new_entities.append(entity)

            with entity_lock:
                entity_list = new_entities

        except Exception as e:
            print("Erro ao atualizar entidades:", e)

        time.sleep(0.1)  # 10 updates por segundo

threading.Thread(target=update_entities, daemon=True).start()

while pm.overlay_loop():
    pm.begin_drawing()
    mesh = Mesh()

    with entity_lock:
        for entity in entity_list:
            if GameData.LocalPlayerController is None:
                continue
            camera_manager = pm.r_uint64(proc, GameData.LocalPlayerController + OFFSET_PLAYER_CAMERA_MANAGER)
            bone_pos = mesh.get_bone_with_rotation(proc, entity.actor_mesh, 0, pm)
            head_pos = mesh.get_bone_with_rotation(proc, entity.actor_mesh, Skeleton.Bones.head, pm)
            bottomBox = Engine.world_to_screen(proc, camera_manager, bone_pos, pm.overlay_width(), pm.overlay_height(), pm)
            headBox = Engine.world_to_screen(proc, camera_manager, head_pos, pm.overlay_width(), pm.overlay_height(), pm)

            if bottomBox.z <= 0 or headBox.z <= 0:
                continue

            boxColor = pm.get_color("white")
            boxThickness = 1.5
            boxHeight = bottomBox.y - headBox.y
            boxWidth = boxHeight / 2.5
            boxX = bottomBox.x - (boxWidth / 2)
            boxY = bottomBox.y - boxHeight
            pm.draw_rectangle(boxX, boxY, boxWidth, boxHeight, boxColor)
            pm.draw_rectangle_lines(boxX, boxY, boxWidth, boxHeight, boxColor, boxThickness)
            pm.draw_text(headBox.x, headBox.y, entity.actor_name, pm.get_color("white"), 1.5)
                
            

    pm.end_drawing()
    

