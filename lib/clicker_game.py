import displayio
import time
import random
import terminalio
from adafruit_display_text import label

# Pet categories with different rarities
PETS = {
    "common": [
        {"name": "Mouse", "emoji": "v.v", "mult": 1.2, "color": 0x888888},
        {"name": "Fish", "emoji": "<>", "mult": 1.3, "color": 0x4169E1},
        {"name": "Bird", "emoji": "^v^", "mult": 1.4, "color": 0x87CEEB},
        {"name": "Hamster", "emoji": "@.@", "mult": 1.25, "color": 0xDEB887},
    ],
    "uncommon": [
        {"name": "Cat", "emoji": "^.^", "mult": 1.8, "color": 0xFFB6C1},
        {"name": "Dog", "emoji": "o.o", "mult": 2.0, "color": 0xCD853F},
        {"name": "Rabbit", "emoji": "(v)", "mult": 1.9, "color": 0xFFC0CB},
        {"name": "Fox", "emoji": "^w^", "mult": 2.1, "color": 0xFF8C00},
    ],
    "rare": [
        {"name": "Wolf", "emoji": "O.O", "mult": 3.0, "color": 0x708090},
        {"name": "Tiger", "emoji": "=.=", "mult": 3.2, "color": 0xFFA500},
        {"name": "Bear", "emoji": "@^@", "mult": 3.5, "color": 0x8B4513},
        {"name": "Panda", "emoji": "0.0", "mult": 3.3, "color": 0x000000},
    ],
    "epic": [
        {"name": "Dragon", "emoji": "<O>", "mult": 5.0, "color": 0xFF0000},
        {"name": "Phoenix", "emoji": "^*^", "mult": 5.5, "color": 0xFF4500},
        {"name": "Griffin", "emoji": "}o{", "mult": 5.2, "color": 0xFFD700},
    ],
    "legendary": [
        {"name": "Unicorn", "emoji": ")^(", "mult": 8.0, "color": 0xFF69B4},
        {"name": "Pegasus", "emoji": "~^~", "mult": 9.0, "color": 0x87CEEB},
        {"name": "Deity", "emoji": "*O*", "mult": 12.0, "color": 0xFFD700},
    ]
}

GACHA_TIERS = {
    "basic": {"cost": 100, "rates": {"common": 70, "uncommon": 25, "rare": 5, "epic": 0, "legendary": 0}},
    "premium": {"cost": 500, "rates": {"common": 40, "uncommon": 35, "rare": 20, "epic": 4, "legendary": 1}},
    "ultra": {"cost": 2000, "rates": {"common": 20, "uncommon": 30, "rare": 30, "epic": 15, "legendary": 5}},
}

ACHIEVEMENTS = [
    {"name": "First Click", "req": 1, "type": "clicks", "reward": 10},
    {"name": "Hundred Club", "req": 100, "type": "clicks", "reward": 100},
    {"name": "Thousandaire", "req": 1000, "type": "clicks", "reward": 500},
    {"name": "Millionaire!", "req": 100000, "type": "clicks", "reward": 5000},
    {"name": "First Rebirth", "req": 1, "type": "rebirths", "reward": 1000},
    {"name": "Pet Collector", "req": 10, "type": "pets", "reward": 2000},
    {"name": "Legendary!", "req": 1, "type": "legendary", "reward": 5000},
]

class ClickerGame:
    def __init__(self, display, state=None):
        self.display = display
        self.group = displayio.Group()
        self.labels = {}

        if state:
            self.clicks = state.get('clicks', 0)
            self.gems = state.get('gems', 0)
            self.rebirths = state.get('rebirths', 0)
            self.owned_pets = state.get('owned_pets', [])
            self.upgrades = state.get('upgrades', [0, 0, 0])
            self.total_clicks_ever = state.get('total_clicks', 0)
            self.achievements = state.get('achievements', [False] * len(ACHIEVEMENTS))
            self.click_power = state.get('click_power', 1)
        else:
            self.clicks = 0
            self.gems = 0
            self.rebirths = 0
            self.owned_pets = []
            self.upgrades = [0, 0, 0]
            self.total_clicks_ever = 0
            self.achievements = [False] * len(ACHIEVEMENTS)
            self.click_power = 1

        self.upgrade_costs = [10, 50, 200]
        self.upgrade_cps = [1, 5, 20]
        self.upgrade_names = ["Auto", "Mega", "Ultra"]

        for i in range(3):
            for _ in range(self.upgrades[i]):
                self.upgrade_costs[i] = int(self.upgrade_costs[i] * 1.5)

        self.cps = sum(self.upgrades[i] * self.upgrade_cps[i] for i in range(3))

        self.current_screen = 0
        self.pet_scroll = 0
        self.combo = 0
        self.last_click_time = 0
        self.combo_mult = 1.0
        self.golden_click_active = False
        self.golden_click_time = 0
        self.last_golden_check = time.monotonic()
        self.last_pull_result = None

        self.total_multiplier = self.calculate_multiplier()
        self.last_time = time.monotonic()

    def calculate_multiplier(self):
        mult = 1.0 + (self.rebirths * 0.5)
        for pet in self.owned_pets:
            mult *= pet["mult"]
        mult *= self.combo_mult
        if self.golden_click_active: mult *= 10.0
        return mult

    def reset_progress(self):
        self.clicks = 0
        self.cps = 0
        self.upgrades = [0, 0, 0]
        self.upgrade_costs = [10, 50, 200]
        self.total_multiplier = self.calculate_multiplier()

    def update(self):
        current_time = time.monotonic()
        if current_time - self.last_time >= 1.0:
            income = int(self.cps * self.total_multiplier)
            self.clicks += income
            self.last_time = current_time
            if self.current_screen in [0, 1, 2]: self.update_labels_only()

        if current_time - self.last_click_time > 2.0:
            self.combo = 0; self.combo_mult = 1.0

        if current_time - self.last_golden_check > 45.0:
            self.last_golden_check = current_time
            if random.random() < 0.1:
                self.golden_click_active = True
                self.golden_click_time = current_time

        if self.golden_click_active and current_time - self.golden_click_time > 10.0:
            self.golden_click_active = False

        self.total_multiplier = self.calculate_multiplier()

    def click(self):
        self.clicks += int(self.click_power * self.total_multiplier)
        self.total_clicks_ever += 1
        self.combo = min(self.combo + 1, 50)
        self.combo_mult = 1.0 + (self.combo * 0.1)
        self.last_click_time = time.monotonic()
        self.check_achievements()
        self.update_labels_only()

    def check_achievements(self):
        for i, ach in enumerate(ACHIEVEMENTS):
            if not self.achievements[i]:
                unlocked = False
                if ach["type"] == "clicks" and self.total_clicks_ever >= ach["req"]: unlocked = True
                elif ach["type"] == "rebirths" and self.rebirths >= ach["req"]: unlocked = True
                elif ach["type"] == "pets" and len(self.owned_pets) >= ach["req"]: unlocked = True

                if unlocked:
                    self.achievements[i] = True
                    self.clicks += ach["reward"]
                    self.gems += 1

    def buy_upgrade(self, i):
        if self.clicks >= self.upgrade_costs[i]:
            self.clicks -= self.upgrade_costs[i]
            self.upgrades[i] += 1
            self.cps += self.upgrade_cps[i]
            self.upgrade_costs[i] = int(self.upgrade_costs[i] * 1.5)
            self.update_labels_only()

    def pull_gacha(self, tier):
        cost = GACHA_TIERS[tier]["cost"]
        if self.clicks < cost: return None
        self.clicks -= cost

        r = random.randint(1, 100); cum = 0; rarity = "common"
        for rar, rate in GACHA_TIERS[tier]["rates"].items():
            cum += rate
            if r <= cum: rarity = rar; break

        pet_data = random.choice(PETS[rarity])
        new_pet = {"name": pet_data["name"], "emoji": pet_data["emoji"], "mult": pet_data["mult"], "rarity": rarity, "color": pet_data["color"]}
        self.owned_pets.append(new_pet)
        self.total_multiplier = self.calculate_multiplier()
        self.render_screen()
        return new_pet

    def do_rebirth(self):
        if self.clicks >= 50000:
            self.rebirths += 1
            self.reset_progress()
            self.render_screen()

    def draw_rect(self, x, y, w, h, color):
        b = displayio.Bitmap(w, h, 1); p = displayio.Palette(1); p[0] = color
        s = displayio.TileGrid(b, pixel_shader=p, x=x, y=y)
        self.group.append(s)

    def update_labels_only(self):
        if self.current_screen == 0:
            if "clicks" in self.labels: self.labels["clicks"].text = f"${self.clicks}"
            if "mult" in self.labels: self.labels["mult"].text = f"x{self.total_multiplier:.1f}"
        elif self.current_screen == 1:
            if "money" in self.labels: self.labels["money"].text = f"${self.clicks}"
            for i in range(3):
                if f"cost{i}" in self.labels: self.labels[f"cost{i}"].text = f"${self.upgrade_costs[i]}"
                if f"lvl{i}" in self.labels: self.labels[f"lvl{i}"].text = f"L{self.upgrades[i]}"

    def render_screen(self):
        while len(self.group) > 0: self.group.pop()
        self.labels = {}
        self.draw_rect(0, 0, 240, 240, 0x0a0a1e)
        title = label.Label(terminalio.FONT, text=f"{self.screen_names()[self.current_screen]}", color=0xFFD700, x=80, y=15, scale=2)
        self.group.append(title)

        if self.current_screen == 0:
            self.labels["clicks"] = label.Label(terminalio.FONT, text=f"${self.clicks}", color=0xFFFFFF, x=40, y=80, scale=3)
            self.group.append(self.labels["clicks"])
            self.labels["mult"] = label.Label(terminalio.FONT, text=f"x{self.total_multiplier:.1f}", color=0x00FF00, x=40, y=120, scale=2)
            self.group.append(self.labels["mult"])
            self.group.append(label.Label(terminalio.FONT, text="[A] CLICK", color=0x888888, x=80, y=180))
        elif self.current_screen == 1:
            self.labels["money"] = label.Label(terminalio.FONT, text=f"${self.clicks}", color=0xFFFF00, x=10, y=40)
            self.group.append(self.labels["money"])
            for i in range(3):
                y = 60 + i*40
                self.draw_rect(10, y, 220, 35, 0x1f4e78)
                self.group.append(label.Label(terminalio.FONT, text=self.upgrade_names[i], color=0xFFFFFF, x=15, y=y+10))
                self.labels[f"lvl{i}"] = label.Label(terminalio.FONT, text=f"L{self.upgrades[i]}", color=0x00FF00, x=15, y=y+22)
                self.group.append(self.labels[f"lvl{i}"])
                self.labels[f"cost{i}"] = label.Label(terminalio.FONT, text=f"${self.upgrade_costs[i]}", color=0xFFFF00, x=100, y=y+15)
                self.group.append(self.labels[f"cost{i}"])
                self.group.append(label.Label(terminalio.FONT, text=f"[{['A','B','X'][i]}]", color=0xFFFFFF, x=190, y=y+15))
        elif self.current_screen == 2:
            self.group.append(label.Label(terminalio.FONT, text=f"${self.clicks}", color=0xFFFF00, x=10, y=40))
            tiers = ["basic", "premium", "ultra"]
            for i, t in enumerate(tiers):
                y = 60 + i*50
                cost = GACHA_TIERS[t]['cost']
                self.draw_rect(10, y, 220, 45, 0x4a0a4a)
                self.group.append(label.Label(terminalio.FONT, text=f"{t.upper()} ${cost} [{['Y','B','X'][i]}]", color=0xFFFFFF, x=15, y=y+20))
        elif self.current_screen == 3:
            self.group.append(label.Label(terminalio.FONT, text=f"Pets: {len(self.owned_pets)}", color=0x00FF00, x=10, y=40))
            for i, pet in enumerate(self.owned_pets[self.pet_scroll*5 : self.pet_scroll*5 + 5]):
                y = 60 + i*30
                self.group.append(label.Label(terminalio.FONT, text=f"{pet['emoji']} {pet['name']} x{pet['mult']}", color=pet['color'], x=15, y=y+15))

        self.display.root_group = self.group

    def screen_names(self): return ["HOME", "SHOP", "GACHA", "PETS", "REBIRTH", "STATS"]
    def next_screen(self): self.current_screen = (self.current_screen + 1) % 6; self.render_screen()
    def prev_screen(self): self.current_screen = (self.current_screen - 1) % 6; self.render_screen()
