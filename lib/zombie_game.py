import displayio
import time
import random
import terminalio
from adafruit_display_text import label

class ZombieShooterGame:
    def __init__(self, display, owned_pets=None, state=None, speaker=None):
        self.display = display
        self.speaker = speaker
        self.owned_pets = owned_pets if owned_pets else []

        self.player_x = 120
        self.player_y = 120
        self.player_health = 100
        self.max_health = 100 if not state else state.get("upgrades", {}).get("max_hp", 100)
        self.score = 0 if not state else state.get("score", 0)
        self.money = 0 if not state else state.get("money", 0)
        self.ammo = 30
        self.max_ammo = 50
        self.day = 1 if not state else state.get("day", 1)
        self.wave = 0
        self.wave_active = False
        self.is_night = False
        self.time_of_day = 0
        self.hunger = 100
        self.wood = 0
        self.metal = 0
        self.food = 5
        self.last_hunger = time.monotonic()
        self.last_spawn = time.monotonic()
        self.last_shot = 0

        self.pet_bonuses = self._calculate_pet_bonuses()
        if state and "upgrades" in state:
            self.damage = state["upgrades"].get("damage", 1 + self.pet_bonuses.get("dmg", 0))
            self.fire_rate = state["upgrades"].get("fire_rate", 0.5 * self.pet_bonuses.get("rate_mult", 1.0))
        else:
            self.damage = 1 + self.pet_bonuses.get("dmg", 0)
            self.fire_rate = 0.5 * self.pet_bonuses.get("rate_mult", 1.0)
        self.bullet_speed = 5
        self.move_speed = 10 + self.pet_bonuses.get("speed", 0)
        self.game_over = False
        self.show_menu = False
        self.zombies = []
        self.bullets = []

        self.upgrade_costs = {"damage": 50, "fire_rate": 60}
        self.recipes = {"medkit": {"food": 3}, "ammo": {"metal": 2}, "barricade": {"wood": 5}}

        self.root_group = displayio.Group()
        self.bg_group = displayio.Group()
        self.player_group = displayio.Group()
        self.zombie_group = displayio.Group()
        self.bullet_group = displayio.Group()
        self.ui_group = displayio.Group()
        self.menu_group = displayio.Group()
        self.root_group.append(self.bg_group); self.root_group.append(self.zombie_group); self.root_group.append(self.player_group); self.root_group.append(self.bullet_group); self.root_group.append(self.ui_group)

        self.zombie_sprites = []
        self.bullet_sprites = []
        self._init_graphics()

    def _calculate_pet_bonuses(self):
        bonuses = {"dmg": 0, "rate_mult": 1.0, "speed": 0, "regen": 0}
        for pet in self.owned_pets:
            r = pet["rarity"]
            if r == "common": bonuses["speed"] += 0.1
            elif r == "uncommon": bonuses["dmg"] += 0.5
            elif r == "rare": bonuses["rate_mult"] *= 0.95
            elif r == "epic": bonuses["regen"] += 0.05
            elif r == "legendary": bonuses["dmg"] += 2
        return bonuses

    def _create_sprite(self, width, height, color, group):
        b = displayio.Bitmap(width, height, 1); p = displayio.Palette(1); p[0] = color
        s = displayio.TileGrid(b, pixel_shader=p); group.append(s); return s

    def _init_graphics(self):
        self.player_body = self._create_sprite(12, 8, 0x0066CC, self.player_group)
        self.player_head = self._create_sprite(8, 8, 0xFFAA88, self.player_group)
        self.player_gun = self._create_sprite(6, 3, 0x333333, self.player_group)
        for _ in range(15):
            s = self._create_sprite(12, 10, 0x00AA00, self.zombie_group); s.hidden = True; self.zombie_sprites.append(s)
        for _ in range(15):
            s = self._create_sprite(3, 8, 0xFFFF00, self.bullet_group); s.hidden = True; self.bullet_sprites.append(s)
        self.hp_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=5, y=10); self.ui_group.append(self.hp_label)
        self.ammo_label = label.Label(terminalio.FONT, text="", color=0xFFFF00, x=5, y=30); self.ui_group.append(self.ammo_label)
        self.wave_label = label.Label(terminalio.FONT, text="", color=0xFF0000, x=150, y=10); self.ui_group.append(self.wave_label)

    def start_wave(self):
        self.wave += 1; self.wave_active = True; self.zombies_to_spawn = 5 + (self.wave * 3)

    def end_wave(self):
        self.wave_active = False; self.day += 1; self.wood += 5; self.metal += 2; self.food += 2

    def spawn_zombie(self):
        if self.zombies_to_spawn <= 0: return
        x, y = random.choice([(random.randint(10, 230), 10), (random.randint(10, 230), 230), (10, random.randint(10, 230)), (230, random.randint(10, 230))])
        self.zombies.append({"x": x, "y": y, "speed": 0.4 + (self.wave*0.05), "health": 2 + (self.wave//2), "worth": 5})
        self.zombies_to_spawn -= 1

    def render(self):
        if self.show_menu: return
        self.player_body.x, self.player_body.y = int(self.player_x - 6), int(self.player_y - 8)
        self.player_head.x, self.player_head.y = int(self.player_x - 4), int(self.player_y - 14)
        self.player_gun.x, self.player_gun.y = int(self.player_x + 4), int(self.player_y - 6)
        for i, s in enumerate(self.zombie_sprites): s.hidden = True
        for i, z in enumerate(self.zombies[:15]):
            s = self.zombie_sprites[i]; s.hidden = False; s.x, s.y = int(z["x"] - 6), int(z["y"] - 10)
        for i, s in enumerate(self.bullet_sprites): s.hidden = True
        for i, b in enumerate(self.bullets[:15]):
            s = self.bullet_sprites[i]; s.hidden = False; s.x, s.y = int(b["x"] - 1), int(b["y"] - 4)
        self.hp_label.text = f"HP: {int(self.player_health)}"; self.ammo_label.text = f"Ammo: {self.ammo}"; self.wave_label.text = f"W:{self.wave}" if self.wave_active else f"D:{self.day}"

    def update(self):
        if self.game_over or self.show_menu: return
        t = time.monotonic()
        if self.pet_bonuses["regen"] > 0: self.player_health = min(self.max_health, self.player_health + self.pet_bonuses["regen"]/60)
        if t - self.last_hunger > 10: self.hunger = max(0, self.hunger - 1); self.last_hunger = t
        if not self.wave_active:
            if t - self.last_spawn > 5: self.start_wave(); self.last_spawn = t
            return
        if self.zombies_to_spawn > 0 and t - self.last_spawn > 1.0: self.spawn_zombie(); self.last_spawn = t
        for b in self.bullets[:]:
            b["x"] += b["dx"] * self.bullet_speed; b["y"] += b["dy"] * self.bullet_speed
            if not (0 < b["x"] < 240 and 0 < b["y"] < 240): self.bullets.remove(b)
        for z in self.zombies[:]:
            dx, dy = self.player_x - z["x"], self.player_y - z["y"]
            dist = (dx**2 + dy**2)**0.5
            if dist > 5: z["x"] += (dx/dist)*z["speed"]; z["y"] += (dy/dist)*z["speed"]
            else: self.player_health -= 0.1
            for b in self.bullets[:]:
                if abs(b["x"]-z["x"]) < 10 and abs(b["y"]-z["y"]) < 10:
                    z["health"] -= self.damage; self.bullets.remove(b)
                    if self.speaker: self.speaker.play_hit()
                    if z["health"] <= 0: self.money += z["worth"]; self.score += z["worth"]; self.zombies.remove(z)
                    break
        if self.zombies_to_spawn == 0 and not self.zombies: self.end_wave()
        if self.player_health <= 0:
            if not self.game_over and self.speaker: self.speaker.play_game_over()
            self.game_over = True

    def shoot(self):
        if self.ammo <= 0 or self.show_menu: return
        t = time.monotonic()
        if t - self.last_shot > self.fire_rate:
            self.ammo -= 1; dx, dy = 0, -1
            if self.zombies:
                z = self.zombies[0]; ndx, ndy = z["x"] - self.player_x, z["y"] - self.player_y
                dist = (ndx**2 + ndy**2)**0.5
                if dist > 0: dx, dy = ndx/dist, ndy/dist
            self.bullets.append({"x": self.player_x, "y": self.player_y, "dx": dx, "dy": dy}); self.last_shot = t
            if self.speaker: self.speaker.play_shoot()

    def toggle_menu(self):
        self.show_menu = not self.show_menu
        if self.show_menu:
            while len(self.menu_group) > 0: self.menu_group.pop()
            b = displayio.Bitmap(240, 240, 1); p = displayio.Palette(1); p[0] = 0x0a0a1a; self.menu_group.append(displayio.TileGrid(b, pixel_shader=p))
            self.menu_group.append(label.Label(terminalio.FONT, text=f"SHOP W:{self.wood} M:{self.metal} ${self.money}", color=0xFFFFFF, x=20, y=30))
            self.menu_group.append(label.Label(terminalio.FONT, text="[A] DMG [B] Rate [X] Barr [UP] Med [DN] Ammo", color=0x00FF00, x=10, y=60))
            self.display.root_group = self.menu_group
        else: self.display.root_group = self.root_group

    def craft(self, k):
        r = self.recipes.get(k)
        if all(getattr(self, res) >= amt for res, amt in r.items()):
            for res, amt in r.items(): setattr(self, res, getattr(self, res)-amt)
            if k == "medkit": self.player_health = min(self.max_health, self.player_health+30)
            elif k == "ammo": self.ammo += 20
            if self.speaker: self.speaker.play_buy()
            self.toggle_menu(); self.toggle_menu()

    def buy_upgrade(self, k):
        c = self.upgrade_costs.get(k)
        if self.money >= c:
            self.money -= c
            if k == "damage": self.damage += 1
            elif k == "fire_rate": self.fire_rate *= 0.9
            self.upgrade_costs[k] = int(c*1.5)
            if self.speaker: self.speaker.play_buy()
            self.toggle_menu(); self.toggle_menu()

    def move_up(self): self.player_y = max(10, self.player_y - self.move_speed)
    def move_down(self): self.player_y = min(230, self.player_y + self.move_speed)
    def move_left(self): self.player_x = max(10, self.player_x - self.move_speed)
    def move_right(self): self.player_x = min(230, self.player_x + self.move_speed)
    def restart(self):
        self.__init__(self.display, self.owned_pets, speaker=self.speaker)
        self.display.root_group = self.root_group
