import sys
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

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Door Lock Service")
clock = pygame.time.Clock()

# =========================================================
# COLORES
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
OVERLAY_DARK = (0, 0, 0, 60)

# =========================================================
# RECURSOS
# =========================================================
def load_image(path: Path) -> pygame.Surface:
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
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

wait_channel = pygame.mixer.Channel(1)

# Fuente monoespaciada. Si no existe Courier New en el sistema,
# pygame usará la más cercana.
font_title = pygame.font.SysFont("couriernew", 28, bold=True)
font_term = pygame.font.SysFont("couriernew", 30, bold=True)
font_prompt = pygame.font.SysFont("couriernew", 26, bold=True)
font_choice = pygame.font.SysFont("couriernew", 34, bold=True)
font_small = pygame.font.SysFont("couriernew", 16, bold=True)

# =========================================================
# HELPERS DIBUJO
# =========================================================
def play_sound(sound, loops=0):
    if sound:
        sound.play(loops=loops)

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

def draw_arrow(surface, x, y):
    pts = [(x, y), (x + 14, y + 8), (x, y + 16)]
    pygame.draw.polygon(surface, WHITE_DIRTY, pts)
    pygame.draw.polygon(surface, SHADOW, pts, 1)

def draw_scanlines(surface, alpha=22, step=2):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    w, h = surface.get_size()
    for y in range(0, h, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (w, y))
    surface.blit(overlay, (0, 0))

def draw_vignette(surface, strength=80):
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    center_x = w / 2
    center_y = h / 2
    max_dist = (center_x ** 2 + center_y ** 2) ** 0.5

    for y in range(h):
        for x in range(w):
            dx = x - center_x
            dy = y - center_y
            d = (dx * dx + dy * dy) ** 0.5
            a = int((d / max_dist) * strength)
            if a > 0:
                overlay.set_at((x, y), (0, 0, 0, min(a, 120)))
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

def draw_window(surface, rect, title="PROGRAM(011)"):
    x, y, w, h = rect

    # Marco exterior
    pygame.draw.rect(surface, FRAME_MID, rect)
    pygame.draw.rect(surface, FRAME_DARK, rect, 2)
    pygame.draw.line(surface, WHITE_DIRTY, (x + 1, y + 1), (x + w - 2, y + 1))
    pygame.draw.line(surface, WHITE_DIRTY, (x + 1, y + 1), (x + 1, y + h - 2))
    pygame.draw.line(surface, FRAME_DARK, (x, y + h - 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, FRAME_DARK, (x + w - 1, y), (x + w - 1, y + h - 1))

    # Barra de título
    bar_h = max(24, int(h * 0.05))
    title_rect = pygame.Rect(x + 4, y + 4, w - 8, bar_h)
    pygame.draw.rect(surface, FRAME_LIGHT, title_rect)
    pygame.draw.rect(surface, FRAME_DARK, title_rect, 1)

    # Botones falsos
    btn_w = 18
    left_btn = pygame.Rect(x + 8, y + 7, btn_w, bar_h - 6)
    right_btn = pygame.Rect(x + w - 8 - btn_w, y + 7, btn_w, bar_h - 6)
    pygame.draw.rect(surface, FRAME_MID, left_btn)
    pygame.draw.rect(surface, FRAME_MID, right_btn)
    pygame.draw.rect(surface, FRAME_DARK, left_btn, 1)
    pygame.draw.rect(surface, FRAME_DARK, right_btn, 1)
    pygame.draw.line(surface, BLACK, (left_btn.x + 4, left_btn.centery), (left_btn.right - 4, left_btn.centery), 2)
    pygame.draw.line(surface, BLACK, (right_btn.x + 4, right_btn.centery), (right_btn.right - 4, right_btn.centery), 2)

    # Título
    title_surf = font_title.render(title, True, (80, 80, 80))
    title_rect2 = title_surf.get_rect(center=(x + w // 2, y + 4 + bar_h // 2))
    surface.blit(title_surf, title_rect2)

    # Interior
    pad = 6
    inner = pygame.Rect(x + pad, y + bar_h + pad, w - pad * 2, h - bar_h - pad * 2 - 10)
    inner_surf = make_interior_surface((inner.w, inner.h))
    surface.blit(inner_surf, inner.topleft)
    pygame.draw.rect(surface, BLACK, inner, 2)

    # Barra inferior decorativa
    bottom_h = 12
    bottom_rect = pygame.Rect(x + 4, y + h - bottom_h - 4, w - 8, bottom_h)
    pygame.draw.rect(surface, FRAME_LIGHT, bottom_rect)
    pygame.draw.rect(surface, FRAME_DARK, bottom_rect, 1)

    handle = pygame.Rect(bottom_rect.x + 80, bottom_rect.y + 1, 18, bottom_rect.h - 2)
    pygame.draw.rect(surface, FRAME_MID, handle)
    pygame.draw.rect(surface, FRAME_DARK, handle, 1)

    return inner

# =========================================================
# CONTENIDO
# =========================================================
TEXT_LINES = [
    ("DOOR LOCK SERVICE", WHITE_DIRTY),
    ("--------------------------------", WHITE_DIRTY),
    ("Hall side doors: ", WHITE_DIRTY, "LOCKED", GREEN_TEXT),
    ("", WHITE_DIRTY),
    ("The doors can be unlocked", WHITE_DIRTY),
    ("by a ", WHITE_DIRTY, "CARD KEY.", GREEN_TEXT),
    ("-", WHITE_DIRTY),
]

QUESTION_1 = "¿Vas a utilizar:"
QUESTION_2 = "Tarj. llave azul?"
OPTIONS = ["Sí", "No"]

# =========================================================
# ESCENA
# =========================================================
class App:
    def __init__(self):
        self.running = True
        self.state = "grow"
        self.state_timer = 0.0

        self.target_rect = pygame.Rect(26, 30, 820, 390)
        self.grow_origin = (96, 110)
        self.grow_start_size = (120, 64)
        self.grow_duration = 0.55

        self.typing_started = False
        self.typing_speed = 0.030
        self.typing_accum = 0.0
        self.line_index = 0
        self.char_index = 0
        self.visible_lines = []

        self.question_char_index_1 = 0
        self.question_char_index_2 = 0
        self.question_speed = 0.022
        self.question_accum = 0.0

        self.selected = 0
        self.checking_dots = 0
        self.dot_timer = 0.0

        self.boot_subtitle = "Control de cerraduras."
        self.boot_subtitle_visible = ""
        self.boot_subtitle_index = 0
        self.boot_subtitle_accum = 0.0

        self.done_hold = 0.0

    def reset_typing(self):
        self.visible_lines = [""]
        self.line_index = 0
        self.char_index = 0
        self.typing_accum = 0.0

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

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "typing":
            self.reset_typing()
            play_sound(snd_main)

        elif new_state == "question":
            play_sound(snd_main)

        elif new_state == "checking":
            self.checking_dots = 0
            self.dot_timer = 0.0
            if snd_waiting:
                wait_channel.play(snd_waiting, loops=-1)

        elif new_state == "done":
            wait_channel.stop()
            play_sound(snd_accept)

    def update_boot_subtitle(self, dt):
        if self.boot_subtitle_index >= len(self.boot_subtitle):
            return
        self.boot_subtitle_accum += dt
        speed = 0.028
        while self.boot_subtitle_accum >= speed and self.boot_subtitle_index < len(self.boot_subtitle):
            self.boot_subtitle_accum -= speed
            self.boot_subtitle_visible += self.boot_subtitle[self.boot_subtitle_index]
            self.boot_subtitle_index += 1

    def update_typing(self, dt):
        if self.line_index >= len(TEXT_LINES):
            return

        self.typing_accum += dt
        while self.typing_accum >= self.typing_speed:
            self.typing_accum -= self.typing_speed

            line = TEXT_LINES[self.line_index]
            base_text = line[0]

            if self.char_index < len(base_text):
                self.visible_lines[-1] += base_text[self.char_index]
                self.char_index += 1
            else:
                # Líneas con segunda parte coloreada
                if len(line) == 4:
                    self.visible_lines[-1] = line
                else:
                    self.visible_lines[-1] = (self.visible_lines[-1], line[1])

                self.line_index += 1
                self.char_index = 0
                if self.line_index < len(TEXT_LINES):
                    self.visible_lines.append("")

    def update_question_typing(self, dt):
        self.question_accum += dt
        while self.question_accum >= self.question_speed:
            self.question_accum -= self.question_speed
            if self.question_char_index_1 < len(QUESTION_1):
                self.question_char_index_1 += 1
            elif self.question_char_index_2 < len(QUESTION_2):
                self.question_char_index_2 += 1

    def update(self, dt):
        self.state_timer += dt
        self.update_boot_subtitle(dt)

        if self.state == "grow":
            if self.state_timer >= self.grow_duration:
                self.set_state("typing")

        elif self.state == "typing":
            self.update_typing(dt)
            if self.line_index >= len(TEXT_LINES):
                if self.state_timer >= 2.5:
                    self.set_state("question")

        elif self.state == "question":
            self.update_question_typing(dt)

        elif self.state == "checking":
            self.dot_timer += dt
            if self.dot_timer >= 0.28:
                self.dot_timer = 0.0
                self.checking_dots = (self.checking_dots + 1) % 5

            if self.state_timer >= 2.2:
                self.set_state("done")

        elif self.state == "done":
            self.done_hold += dt

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
                    for line in TEXT_LINES:
                        if len(line) == 4:
                            self.visible_lines.append(line)
                        else:
                            self.visible_lines.append((line[0], line[1]))
                    self.line_index = len(TEXT_LINES)
                    self.char_index = 0
                    self.state_timer = 999

            elif self.state == "question":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected = max(0, self.selected - 1)
                    play_sound(snd_main)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected = min(1, self.selected + 1)
                    play_sound(snd_main)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.selected == 0:
                        self.set_state("checking")
                    else:
                        play_sound(snd_main)

            elif self.state == "done":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False

    def draw_background(self):
        screen.blit(bg, (0, 0))

        dark_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 24))
        screen.blit(dark_overlay, (0, 0))

    def draw_subtitle(self):
        draw_shadow_text(
            screen,
            font_prompt,
            self.boot_subtitle_visible,
            WHITE_SOFT,
            SHADOW,
            (90, SCREEN_H - 80)
        )

    def draw_terminal_lines(self, inner_rect):
        x = inner_rect.x + 18
        y = inner_rect.y + 10
        line_h = 44

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

    def draw_question(self):
        q1 = QUESTION_1[:self.question_char_index_1]
        q2 = QUESTION_2[:self.question_char_index_2]

        draw_shadow_text(screen, font_prompt, q1, WHITE_SOFT, SHADOW, (90, SCREEN_H - 82))
        draw_shadow_text(screen, font_prompt, q2, GREEN_TEXT, GREEN_DARK, (470, SCREEN_H - 82))

        draw_shadow_text(screen, font_choice, "Sí", WHITE_DIRTY, SHADOW, (760, SCREEN_H - 56))
        draw_shadow_text(screen, font_choice, "No", WHITE_DIRTY, SHADOW, (880, SCREEN_H - 56))

        if self.selected == 0:
            draw_arrow(screen, 735, SCREEN_H - 44)
        else:
            draw_arrow(screen, 855, SCREEN_H - 44)

    def draw_checking(self, inner_rect):
        dots = "." * self.checking_dots
        line = f"Checking up ID-CARD{dots}"
        draw_shadow_text(
            screen,
            font_term,
            line,
            WHITE_DIRTY,
            SHADOW,
            (inner_rect.x + 18, inner_rect.y + 238)
        )

        draw_shadow_text(
            screen,
            font_prompt,
            "Comprobando tarjeta...",
            WHITE_SOFT,
            SHADOW,
            (90, SCREEN_H - 80)
        )

    def draw_done(self, inner_rect):
        draw_shadow_text(
            screen,
            font_term,
            "Checking up ID-CARD....",
            WHITE_DIRTY,
            SHADOW,
            (inner_rect.x + 18, inner_rect.y + 238)
        )
        draw_shadow_text(
            screen,
            font_term,
            "OK!",
            WHITE_DIRTY,
            SHADOW,
            (inner_rect.x + 18, inner_rect.y + 282)
        )
        draw_shadow_text(
            screen,
            font_term,
            "Hall side doors lock released.",
            WHITE_DIRTY,
            SHADOW,
            (inner_rect.x + 18, inner_rect.y + 326)
        )
        draw_shadow_text(
            screen,
            font_term,
            "-",
            WHITE_DIRTY,
            SHADOW,
            (inner_rect.x + 18, inner_rect.y + 370)
        )

        draw_shadow_text(
            screen,
            font_prompt,
            "Puertas del vestíbulo: ",
            WHITE_SOFT,
            SHADOW,
            (90, SCREEN_H - 80)
        )
        draw_shadow_text(
            screen,
            font_prompt,
            "ABIERTAS",
            GREEN_TEXT,
            GREEN_DARK,
            (470, SCREEN_H - 80)
        )

    def render(self):
        self.draw_background()

        rect = self.current_window_rect()
        inner_rect = draw_window(screen, rect, "PROGRAM(011)")

        # Durante crecimiento no dibujamos texto hasta que la ventana tenga tamaño creíble
        if rect.w > 300 and rect.h > 140:
            if self.state in ("typing", "question", "checking", "done"):
                self.draw_terminal_lines(inner_rect)

        if self.state == "question":
            self.draw_question()
        elif self.state == "checking":
            self.draw_checking(inner_rect)
        elif self.state == "done":
            self.draw_done(inner_rect)

        self.draw_subtitle()

        draw_scanlines(screen, alpha=18, step=2)

        # Flicker leve
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

        wait_channel.stop()

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    app = App()
    app.run()
    pygame.quit()
    sys.exit()