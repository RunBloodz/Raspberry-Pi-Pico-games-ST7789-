import board
import pwmio
import time

class Speaker:
    def __init__(self, pin=board.GP14):
        self.pin = pin
        self.pwm = None
        try:
            self.pwm = pwmio.PWMOut(pin, duty_cycle=0, frequency=440, variable_frequency=True)
        except Exception as e:
            print(f"Audio init warning: {e}")

    def play_tone(self, frequency, duration=0.1, duty_cycle=16384):
        if not self.pwm:
            return
        try:
            self.pwm.frequency = int(frequency)
            self.pwm.duty_cycle = duty_cycle
            time.sleep(duration)
            self.pwm.duty_cycle = 0
        except Exception:
            if self.pwm:
                self.pwm.duty_cycle = 0

    def play_click(self):
        self.play_tone(1000, 0.03, 8192)

    def play_shoot(self):
        self.play_tone(800, 0.03, 16384)
        self.play_tone(400, 0.03, 16384)

    def play_buy(self):
        self.play_tone(523, 0.05, 16384) # C5
        self.play_tone(659, 0.05, 16384) # E5
        self.play_tone(784, 0.08, 16384) # G5

    def play_hit(self):
        self.play_tone(150, 0.05, 16384)

    def play_game_over(self):
        self.play_tone(400, 0.1, 16384)
        self.play_tone(300, 0.1, 16384)
        self.play_tone(200, 0.2, 16384)
