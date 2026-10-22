import board
import time
import math
import array

try:
    import audiobusio
    import audiocore
    I2S_AVAILABLE = True
except ImportError:
    I2S_AVAILABLE = False

try:
    import pwmio
    PWM_AVAILABLE = True
except ImportError:
    PWM_AVAILABLE = False

class Speaker:
    def __init__(self, bit_clock=board.GP28, word_select=board.GP27, data=board.GP22, main_clock=board.GP26):
        self.i2s = None
        self.pwm = None

        if I2S_AVAILABLE:
            try:
                # Try initializing I2S with MCLK
                try:
                    self.i2s = audiobusio.I2SOut(bit_clock=bit_clock, word_select=word_select, data=data, main_clock=main_clock)
                except (TypeError, ValueError, AttributeError, Exception):
                    # Fall back to standard I2S without MCLK parameter if unsupported
                    self.i2s = audiobusio.I2SOut(bit_clock=bit_clock, word_select=word_select, data=data)
            except Exception as e:
                print(f"I2S init warning: {e}")

        if not self.i2s and PWM_AVAILABLE:
            try:
                self.pwm = pwmio.PWMOut(board.GP14, duty_cycle=0, frequency=440, variable_frequency=True)
            except Exception as e:
                print(f"PWM fallback warning: {e}")

    def _generate_sine_sample(self, frequency, duration, sample_rate=16000):
        n_samples = int(sample_rate * duration)
        buf = array.array("h", [0] * n_samples)
        for i in range(n_samples):
            t = float(i) / sample_rate
            buf[i] = int(16000 * math.sin(2 * math.pi * frequency * t))
        return buf, sample_rate

    def play_tone(self, frequency, duration=0.1, duty_cycle=16384):
        if self.i2s and I2S_AVAILABLE:
            try:
                buf, sample_rate = self._generate_sine_sample(frequency, duration)
                sample = audiocore.RawSample(buf, sample_rate=sample_rate)
                self.i2s.play(sample)
                time.sleep(duration)
                self.i2s.stop()
                return
            except Exception as e:
                pass

        if self.pwm:
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
