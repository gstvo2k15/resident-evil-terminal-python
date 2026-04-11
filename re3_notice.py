import sys
import random
from pathlib import Path

import pygame

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

BG_IMAGE = BASE_DIR / "Skycard_hd_0.png"

SND_ACCEPT = BASE_DIR / "accept.mp3"
SND_WAITING = BASE_DIR / "beep_waitting.mp3"
SND_MAIN = BASE_DIR / "beep_main.mp3"

PASSWORD_OPTIONS = ["0131", "0513", "4011", "4312"]

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Resident Evil 3 - STARS Notice")
clock = pygame.time.Clock()

# =========================================================
# COLORS
# =========================================================
WHITE_DIRTY = (230, 232, 228)
WHITE_SOFT = (200, 202, 198)
SHADOW = (70, 74, 90)
GREEN_TEXT = (0, 210, 45)
GREEN_DARK = (10, 70, 18)
FRAME_LIGHT = (208, 208, 208)
FRAME_MID = (152, 152, 152)
FRAME_DARK = (54, 54, 54)
INTERIOR_TOP = (18, 31, 36)
INTERIOR_BOTTOM = (10, 18, 22)
BLACK = (0, 0, 0)

# =========================================================
# RESOURCES
# =========================================================
def load_image(path: Path) -> pygame.Surface:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    img = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))


def load_sound(path: Path):
    if not path.exists():
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


bg = load_image(BG_IMAGE)

snd_accept = load_sound(SND_ACCEPT)
snd_waiting = load_sound(SND_WAITING)
snd_main = load_sound(SND_MAIN)

type_channel = pygame.mixer.Channel(2)

font_title = pygame.font.SysFont("couriernew", 28, bold=True)
font_term = pygame.font.SysFont("couriernew", 30, bold=True)
font_small = pygame.font.SysFont("couriernew", 24, bold=True)

# =========================================================
# HELPERS
# =========================================================
def play_sound(sound, loops=0):
    if sound:
        sound.play(loops=loops)


def play_type_sound():
    if snd_main and not type_channel.get_busy():
        type_channel.play(snd_main)


def draw_shadow_text(surface, font, text, color, shadow_color, pos):
    x, y = pos
    shadow = font.render(text, True, shadow_color)
    main = font.render(text, True, color)
    surface.blit(shadow, (x + 2, y + 2))
    surface.blit(main, (x, y))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - pow(1 - t, 3)


def draw_scanlines(surface, alpha=18, step=2):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    w, h = surface.get_size()
    for y in range(0, h, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (w, y))
    surface.blit(overlay, (0, 0))


def make_interior_surface(size):
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(lerp(INTERIOR_TOP[0], INTERIOR_BOTTOM[0], t))
        g = int(lerp(INTERIOR_TOP[1], INTERIOR_BOTTOM[1], t))
        b = int(lerp(INTERIOR_TOP[2], INTERIOR_BOTTOM[2], t))
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

    noise = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 3):
        shade = 8 if (y // 3) % 2 == 0 else 0
        pygame.draw.line(noise, (shade, shade, shade, 10), (0, y), (w, y))
    surf.blit(noise, (0, 0))
    return surf


def draw_window(surface, rect, title="PROGRAM(1:1)"):
    x, y, w, h = rect

    pygame.draw.rect(surface, FRAME_MID, rect)
    pygame.draw.rect(surface, FRAME_DARK, rect, 2)
    pygame.draw.line(surface, WHITE_DIRTY, (x + 1, y + 1), (x + w - 2, y + 1))
    pygame.draw.line(surface, WHITE_DIRTY, (x + 1, y + 1), (x + 1, y + h - 2))
    pygame.draw.line(surface, FRAME_DARK, (x, y + h - 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, FRAME_DARK, (x + w - 1, y), (x + w - 1, y + h - 1))

    bar_h = max(24, int(h * 0.05))
    title_rect = pygame.Rect(x + 4, y + 4, w - 8, bar_h)
    pygame.draw.rect(surface, FRAME_LIGHT, title_rect)
    pygame.draw.rect(surface, FRAME_DARK, title_rect, 1)

    btn_w = 18
    left_btn = pygame.Rect(x + 8, y + 7, btn_w, bar_h - 6)
    right_btn = pygame.Rect(x + w - 8 - btn_w, y + 7, btn_w, bar_h - 6)
    pygame.draw.rect(surface, FRAME_MID, left_btn)
    pygame.draw.rect(surface, FRAME_MID, right_btn)
    pygame.draw.rect(surface, FRAME_DARK, left_btn, 1)
    pygame.draw.rect(surface, FRAME_DARK, right_btn, 1)
    pygame.draw.line(surface, BLACK, (left_btn.x + 4, left_btn.centery), (left_btn.right - 4, left_btn.centery), 2)
    pygame.draw.line(surface, BLACK, (right_btn.x + 4, right_btn.centery), (right_btn.right - 4, right_btn.centery), 2)

    title_surf = font_title.render(title, True, (80, 80, 80))
    title_pos = title_surf.get_rect(center=(x + w // 2, y + 4 + bar_h // 2))
    surface.blit(title_surf, title_pos)

    pad = 6
    inner = pygame.Rect(x + pad, y + bar_h + pad, w - pad * 2, h - bar_h - pad * 2 - 10)
    inner_surf = make_interior_surface((inner.w, inner.h))
    surface.blit(inner_surf, inner.topleft)
    pygame.draw.rect(surface, BLACK, inner, 2)

    bottom_h = 12
    bottom_rect = pygame.Rect(x + 4, y + h - bottom_h - 4, w - 8, bottom_h)
    pygame.draw.rect(surface, FRAME_LIGHT, bottom_rect)
    pygame.draw.rect(surface, FRAME_DARK, bottom_rect, 1)

    handle = pygame.Rect(bottom_rect.x + 80, bottom_rect.y + 1, 18, bottom_rect.h - 2)
    pygame.draw.rect(surface, FRAME_MID, handle)
    pygame.draw.rect(surface, FRAME_DARK, handle, 1)

    return inner

# =========================================================
# CONTENT
# =========================================================
def build_notice_lines(password: str):
    return [
        ("NOTICE TO STARS PERSONNEL", WHITE_DIRTY),
        ("...", WHITE_DIRTY),
        ("Due to the emergency, the", WHITE_DIRTY),
        ("key to the STARS office has", WHITE_DIRTY),
        ("been moved to the evidence", WHITE_DIRTY),
        ("room.", WHITE_DIRTY),
        ("", WHITE_DIRTY),
        ("Today's password for the", WHITE_DIRTY),
        ("safe is ", WHITE_DIRTY, f"{password}.", GREEN_TEXT),
    ]

# =========================================================
# APP
# =========================================================
class App:
    def __init__(self):
        self.running = True
        self.state = "idle_bg"
        self.state_timer = 0.0

        self.password = random.choice(PASSWORD_OPTIONS)
        self.lines = build_notice_lines(self.password)

        self.target_rect = pygame.Rect(42, 40, 1020, 470)
        self.grow_origin = (120, 120)
        self.grow_start_size = (140, 72)
        self.grow_duration = 0.48
        self.idle_bg_duration = 0.65

        self.visible_lines = []
        self.line_index = 0
        self.char_index = 0
        self.typing_speed = 0.024
        self.typing_accum = 0.0

        self.flash_done = False
        self.flash_timer = 0.0

    def current_window_rect(self):
        if self.state != "grow":
            return self.target_rect.copy()

        t = ease_out_cubic(min(1.0, self.state_timer / self.grow_duration))
        sw, sh = self.grow_start_size
        tw, th = self.target_rect.size

        w = int(lerp(sw, tw, t))
        h = int(lerp(sh, th, t))
        x = int(lerp(self.grow_origin[0], self.target_rect.x, t))
        y = int(lerp(self.grow_origin[1], self.target_rect.y, t))
        return pygame.Rect(x, y, w, h)

    def reset_typing(self):
        self.visible_lines = [""]
        self.line_index = 0
        self.char_index = 0
        self.typing_accum = 0.0

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "typing":
            self.reset_typing()

        elif new_state == "done":
            self.flash_done = True
            self.flash_timer = 0.18
            play_sound(snd_accept)

    def update_typing(self, dt):
        if self.line_index >= len(self.lines):
            return

        self.typing_accum += dt
        while self.typing_accum >= self.typing_speed:
            self.typing_accum -= self.typing_speed

            line = self.lines[self.line_index]
            base_text = line[0]

            if self.char_index < len(base_text):
                ch = base_text[self.char_index]
                self.visible_lines[-1] += ch
                self.char_index += 1

                if ch != " ":
                    play_type_sound()

            else:
                if len(line) == 4:
                    self.visible_lines[-1] = line
                    play_type_sound()
                else:
                    self.visible_lines[-1] = (self.visible_lines[-1], line[1])

                self.line_index += 1
                self.char_index = 0
                if self.line_index < len(self.lines):
                    self.visible_lines.append("")

    def update(self, dt):
        self.state_timer += dt

        if self.flash_done:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_done = False

        if self.state == "idle_bg":
            if self.state_timer >= self.idle_bg_duration:
                self.set_state("grow")

        elif self.state == "grow":
            if self.state_timer >= self.grow_duration:
                self.set_state("typing")

        elif self.state == "typing":
            self.update_typing(dt)
            if self.line_index >= len(self.lines) and self.state_timer >= 2.2:
                self.set_state("done")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return

            if self.state == "typing":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.visible_lines = []
                    for line in self.lines:
                        if len(line) == 4:
                            self.visible_lines.append(line)
                        else:
                            self.visible_lines.append((line[0], line[1]))
                    self.line_index = len(self.lines)
                    self.char_index = 0
                    self.state_timer = 999

            elif self.state == "done":
                if event.key in (pygame.K_r,):
                    self.password = random.choice(PASSWORD_OPTIONS)
                    self.lines = build_notice_lines(self.password)
                    self.set_state("typing")

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False

    def draw_background(self):
        screen.blit(bg, (0, 0))

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 22))
        screen.blit(overlay, (0, 0))

    def draw_lines(self, inner_rect):
        x = inner_rect.x + 18
        y = inner_rect.y + 8
        line_h = 46

        for item in self.visible_lines:
            if isinstance(item, str):
                draw_shadow_text(screen, font_term, item, WHITE_DIRTY, SHADOW, (x, y))
            else:
                if len(item) == 2:
                    txt, color = item
                    draw_shadow_text(screen, font_term, txt, color, SHADOW, (x, y))
                elif len(item) == 4:
                    left_txt, left_col, right_txt, right_col = item
                    draw_shadow_text(screen, font_term, left_txt, left_col, SHADOW, (x, y))
                    left_width = font_term.size(left_txt)[0]
                    draw_shadow_text(screen, font_term, right_txt, right_col, GREEN_DARK, (x + left_width, y))

            y += line_h

    def render(self):
        self.draw_background()

        if self.state != "idle_bg":
            rect = self.current_window_rect()
            inner_rect = draw_window(screen, rect, "PROGRAM(1:1)")

            if rect.w > 320 and rect.h > 160 and self.state != "grow":
                self.draw_lines(inner_rect)

        if self.flash_done:
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 18))
            screen.blit(flash, (0, 0))

        draw_scanlines(screen, alpha=18, step=2)

        flicker = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flicker.fill((0, 0, 0, 6))
        screen.blit(flicker, (0, 0))

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.render()


if __name__ == "__main__":
    app = App()
    app.run()
    pygame.quit()
    sys.exit()