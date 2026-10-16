import board
import busio
import digitalio
import displayio
import terminalio
import time
import gc
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from lib.save_manager import load_game, save_game, get_combined_state

try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

def show_loading_screen(display):
    group = displayio.Group()
    bg = displayio.Bitmap(240, 240, 1); palette = displayio.Palette(1); palette[0] = 0x0a0a1e
    group.append(displayio.TileGrid(bg, pixel_shader=palette))

    loading_text = label.Label(terminalio.FONT, text="GAME HUB", color=0xFFFFFF, x=70, y=100, scale=3)
    group.append(loading_text)

    bar_bg = displayio.Bitmap(160, 10, 1); bar_palette = displayio.Palette(2); bar_palette[0] = 0x333333; bar_palette[1] = 0x00FF00
    group.append(displayio.TileGrid(bar_bg, pixel_shader=bar_palette, x=40, y=140))

    display.root_group = group
    for i in range(5):
        w = int(160 * (i + 1) / 5)
        bar = displayio.Bitmap(w, 6, 1); p = displayio.Palette(1); p[0] = 0x00FF00
        group.append(displayio.TileGrid(bar, pixel_shader=p, x=42, y=142))
        time.sleep(0.2)
    time.sleep(0.3)

def main():
    displayio.release_displays()
    spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)
    display_bus = FourWire(spi, command=board.GP8, chip_select=board.GP9, reset=board.GP12, baudrate=40000000)
    display = ST7789(display_bus, width=240, height=240, rowstart=80, rotation=270)

    backlight = digitalio.DigitalInOut(board.GP13); backlight.switch_to_output(); backlight.value = True

    show_loading_screen(display)

    # Buttons
    btns = []
    for pin in [board.GP15, board.GP17, board.GP2, board.GP18, board.GP16, board.GP20, board.GP3, board.GP19, board.GP21]:
        b = digitalio.DigitalInOut(pin); b.switch_to_input(pull=digitalio.Pull.UP)
        btns.append(b)
    # btns order: A=0, B=1, UP=2, DOWN=3, LEFT=4, RIGHT=5, CTRL=6, X=7, Y=8

    data = load_game()
    save_data = data if data else {}

    from lib.clicker_game import ClickerGame
    from lib.zombie_game import ZombieShooterGame

    # Initialize both games
    clicker = ClickerGame(display, state=save_data.get('clicker'))
    zombie = ZombieShooterGame(display, owned_pets=clicker.owned_pets, state=save_data.get('zombie'))

    current_game = "menu"
    menu_selection = 0

    def show_main_menu():
        group = displayio.Group()
        bg = displayio.Bitmap(240, 240, 1); p = displayio.Palette(1); p[0] = 0x1a1a2e
        group.append(displayio.TileGrid(bg, pixel_shader=p))

        group.append(label.Label(terminalio.FONT, text="ULTIMATE PICO GAMES", color=0xFFD700, x=30, y=30, scale=1))

        options = ["CLICKER TYCOON", "ZOMBIE SHOOTER", "SAVE & EXIT"]
        for i, opt in enumerate(options):
            color = 0xFFFFFF if i == menu_selection else 0x666666
            group.append(label.Label(terminalio.FONT, text=f"{'> ' if i == menu_selection else '  '}{opt}", color=color, x=40, y=80 + i*40, scale=2))

        display.root_group = group
        gc.collect()

    show_main_menu()

    last_states = [True] * 9
    last_save_time = time.monotonic()

    while True:
        curr_time = time.monotonic()

        if curr_time - last_save_time > 60:
            save_game(get_combined_state(clicker, zombie))
            last_save_time = curr_time

        for i, btn in enumerate(btns):
            curr_state = btn.value
            if not curr_state and last_states[i]:
                if current_game == "menu":
                    if i == 2: # UP
                        menu_selection = (menu_selection - 1) % 3; show_main_menu()
                    elif i == 3: # DOWN
                        menu_selection = (menu_selection + 1) % 3; show_main_menu()
                    elif i == 0: # A
                        if menu_selection == 0:
                            current_game = "clicker"; clicker.render_screen()
                        elif menu_selection == 1:
                            current_game = "zombie"; zombie.owned_pets = clicker.owned_pets; zombie.pet_bonuses = zombie._calculate_pet_bonuses(); zombie.display.root_group = zombie.root_group
                        elif menu_selection == 2:
                            save_game(get_combined_state(clicker, zombie))

                elif current_game == "clicker":
                    if i == 6: # CTRL
                        current_game = "menu"; gc.collect(); show_main_menu()
                    elif i == 0: clicker.click() if clicker.current_screen == 0 else (clicker.buy_upgrade(0) if clicker.current_screen == 1 else None)
                    elif i == 1: clicker.buy_upgrade(1) if clicker.current_screen == 1 else (clicker.pull_gacha("premium") if clicker.current_screen == 2 else None)
                    elif i == 4: clicker.prev_screen()
                    elif i == 5: clicker.next_screen()
                    elif i == 7: # X
                        if clicker.current_screen == 1: clicker.buy_upgrade(2)
                        elif clicker.current_screen == 2: clicker.pull_gacha("ultra")
                    elif i == 8: # Y
                        if clicker.current_screen == 2: clicker.pull_gacha("basic")

                elif current_game == "zombie":
                    if i == 6: # CTRL
                        current_game = "menu"; gc.collect(); show_main_menu()
                    elif i == 0:
                        if zombie.game_over: zombie.restart()
                        elif zombie.show_menu: zombie.buy_upgrade("damage")
                        else: zombie.shoot()
                    elif i == 1:
                        if zombie.show_menu: zombie.buy_upgrade("fire_rate")
                        else: zombie.toggle_menu()
                    elif i == 2:
                        if zombie.show_menu: zombie.craft("medkit")
                    elif i == 3:
                        if zombie.show_menu: zombie.craft("ammo")
                    elif i == 7: # X
                        if zombie.show_menu: zombie.craft("barricade")

            last_states[i] = curr_state

        if current_game == "clicker": clicker.update()
        elif current_game == "zombie":
            if not zombie.show_menu and not zombie.game_over:
                if not btns[2].value: zombie.move_up()
                if not btns[3].value: zombie.move_down()
                if not btns[4].value: zombie.move_left()
                if not btns[5].value: zombie.move_right()
            zombie.update()
            zombie.render()

        time.sleep(0.01)

if __name__ == "__main__":
    main()
