import displayio
import terminalio

class Label(displayio.Group):
    def __init__(self, font=terminalio.FONT, text="", color=0xFFFFFF, x=0, y=0, scale=1, **kwargs):
        super().__init__(scale=scale, x=x, y=y)
        self.font = font
        self._color = color
        self._text = ""
        try:
            self.palette = displayio.Palette(2)
            self.palette.make_transparent(0)
            self.palette[1] = color
        except Exception:
            self.palette = None
        self.text = text

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        if self.palette:
            self.palette[1] = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if value == self._text and len(self) > 0:
            return
        self._text = str(value) if value is not None else ""
        while len(self) > 0:
            self.pop()

        if not self._text:
            return

        lines = self._text.split("\n")
        y_offset = 0
        for line in lines:
            if line:
                glyph_width, glyph_height = 6, 8
                if hasattr(self.font, 'get_bounding_box'):
                    try:
                        bbox = self.font.get_bounding_box()
                        if isinstance(bbox, (tuple, list)):
                            glyph_width, glyph_height = int(bbox[0]), int(bbox[1])
                    except Exception:
                        pass

                bm_w = len(line) * glyph_width
                bm_h = glyph_height
                try:
                    bitmap = displayio.Bitmap(bm_w, bm_h, 2)
                except Exception:
                    bitmap = None

                if bitmap:
                    for char_idx, char in enumerate(line):
                        char_code = ord(char)
                        if hasattr(self.font, 'get_glyph'):
                            glyph = self.font.get_glyph(char_code)
                            if glyph:
                                for gy in range(getattr(glyph, 'height', 0)):
                                    for gx in range(getattr(glyph, 'width', 0)):
                                        try:
                                            if glyph.bitmap[gx, gy]:
                                                px = char_idx * glyph_width + gx + getattr(glyph, 'dx', 0)
                                                py = gy + getattr(glyph, 'dy', 0)
                                                if 0 <= px < bm_w and 0 <= py < bm_h:
                                                    bitmap[px, py] = 1
                                        except Exception:
                                            pass
                        else:
                            for row in range(min(8, bm_h)):
                                for col in range(min(6, bm_w - char_idx * 6)):
                                    try:
                                        bitmap[char_idx * 6 + col, row] = 1
                                    except Exception:
                                        pass

                    try:
                        tile_grid = displayio.TileGrid(bitmap, pixel_shader=self.palette, x=0, y=y_offset)
                        self.append(tile_grid)
                    except Exception:
                        pass
            y_offset += 10
