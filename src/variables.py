GAME_WINDOW = "UnrealWindow"
GAME_NAME = "Bodycam-Win64-Shipping.exe"

relevant_actors = set("ALS_AnimMan_CharacterBP_C")

class GameData:
    GWorld = None
    GameInstance = None
    LocalPlayerArray = None
    LocalPlayer = None
    LocalPlayerController = None
    LocalPlayerPawn = None
    LocalPlayerRoot = None
    PersistentLevel = None
    ActorArray = None
    ActorCount = None

class Entity():
    def __init__(self):
        self.actor_id = None
        self.actor_name = None
        self.actor_pawn = None
        self.actor_state = None
        self.actor_mesh = None


def string_starts_with(string, prefix):
    return string[:len(prefix)] == prefix

def is_relevant_entity(actor_name):
    return any(string_starts_with(actor_name, prefix) for prefix in relevant_actors)

