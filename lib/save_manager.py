import json
import os

SAVE_FILE = "game_save.json"

def save_game(data):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False

def load_game():
    if not file_exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Load error: {e}")
        return None

def file_exists(filename):
    try:
        os.stat(filename)
        return True
    except OSError:
        return False

def get_combined_state(clicker_game, zombie_game):
    return {
        "clicker": {
            "clicks": clicker_game.clicks,
            "gems": clicker_game.gems,
            "rebirths": clicker_game.rebirths,
            "owned_pets": clicker_game.owned_pets,
            "upgrades": clicker_game.upgrades,
            "total_clicks": clicker_game.total_clicks_ever,
            "achievements": clicker_game.achievements,
            "click_power": clicker_game.click_power
        },
        "zombie": {
            "money": zombie_game.money,
            "score": zombie_game.score,
            "day": zombie_game.day,
            "upgrades": {
                "damage": zombie_game.damage,
                "fire_rate": zombie_game.fire_rate,
                "max_hp": zombie_game.max_health
            }
        }
    }
