import sys
import random
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

BG_IMAGE = BASE_DIR / "RE3_newest_saffspringHd_Fixed_BASE.png"

SND_OPEN = BASE_DIR / "re3_openning_terminal_letters_pc.mp3"
SND_LETTERS = BASE_DIR / "re3_letters_pc.mp3"
SND_CHOOSE = BASE_DIR / "re3_chosing_single_letters_pc.mp3"
SND_ENTER = BASE_DIR / "re3_enter_passwd_pc.mp3"
SND_FINISH = BASE_DIR / "re3_finish_passwd_pc.mp3"

PASSWORD_OPTIONS = ["SAFSPRIN", "ADRAVIL", "AQUACURE"]

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Resident Evil 3 - Security Terminal")
clock = pygame.time.Clock()

WHITE_DIRTY = (230, 232, 228)
SHADOW = (70, 74, 90)
RED_TEXT = (170, 18, 34)
RED_DARK = (60, 10, 16)
FRAME_LIGHT = (208, 208, 208)
FRAME_MID = (152, 152, 152)
FRAME_DARK = (54, 54, 54)
KEY_FILL = (160, 160, 160)
KEY_FILL_HI = (205, 205, 205)
KEY_TEXT = (72, 72, 72)
BLACK = (0, 0, 0)

font_title = pygame.font.SysFont("couriernew", 28, bold=True)
font_term = pygame.font.SysFont("couriernew", 30, bold=True)
font_key = pygame.font.SysFont("arial", 26, bold=True)
font_key_small = pygame.font.SysFont("arial", 18, bold=True)

typing_channel = pygame.mixer.Channel(0)
ui_channel = pygame.mixer.Channel(1)


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

snd_open = load_sound(SND_OPEN)
snd_letters = load_sound(SND_LETTERS)
snd_choose = load_sound(SND_CHOOSE)
snd_enter = load_sound(SND_ENTER)
snd_finish = load_sound(SND_FINISH)


def play_typing_open():
    if snd_open:
        typing_channel.stop()
        typing_channel.play(snd_open)


def play_typing_normal():
    if snd_letters:
        typing_channel.stop()
        typing_channel.play(snd_letters)


def play_choose():
    if snd_choose:
        ui_channel.stop()
        ui_channel.play(snd_choose)


def play_enter():
    if snd_enter:
        ui_channel.stop()
        ui_channel.play(snd_enter)


def play_finish():
    if snd_finish:
        ui_channel.stop()
        ui_channel.play(snd_finish)


def draw_shadow_text(surface, font, text, color, shadow_color, pos):
    x_pos, y_pos = pos
    shadow = font.render(text, True, shadow_color)
    main = font.render(text, True, color)
    surface.blit(shadow, (x_pos + 2, y_pos + 2))
    surface.blit(main, (x_pos, y_pos))


def lerp(a_val, b_val, factor):
    return a_val + (b_val - a_val) * factor


def ease_out_cubic(factor):
    factor = max(0.0, min(1.0, factor))
    return 1 - pow(1 - factor, 3)


def draw_scanlines(surface, alpha=18, step=2):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    width, height = surface.get_size()
    for y_pos in range(0, height, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y_pos), (width, y_pos))
    surface.blit(overlay, (0, 0))


def build_scene_base():
    base = bg.copy()
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 16))
    base.blit(overlay, (0, 0))
    return base


def make_terminal_background(scene_base, inner_rect):
    slice_surface = scene_base.subsurface(inner_rect).copy().convert_alpha()
    darken = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    darken.fill((0, 0, 0, 118))
    slice_surface.blit(darken, (0, 0))

    internal_scan = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    for y_pos in range(0, inner_rect.h, 3):
        pygame.draw.line(internal_scan, (255, 255, 255, 3), (0, y_pos), (inner_rect.w, y_pos))
    slice_surface.blit(internal_scan, (0, 0))
    return slice_surface


def draw_window(surface, rect, scene_base, title="PROGRAM(1:1)"):
    x_pos, y_pos, width, height = rect

    pygame.draw.rect(surface, FRAME_MID, rect)
    pygame.draw.rect(surface, FRAME_DARK, rect, 2)
    pygame.draw.line(surface, WHITE_DIRTY, (x_pos + 1, y_pos + 1), (x_pos + width - 2, y_pos + 1))
    pygame.draw.line(surface, WHITE_DIRTY, (x_pos + 1, y_pos + 1), (x_pos + 1, y_pos + height - 2))
    pygame.draw.line(surface, FRAME_DARK, (x_pos, y_pos + height - 1), (x_pos + width - 1, y_pos + height - 1))
    pygame.draw.line(surface, FRAME_DARK, (x_pos + width - 1, y_pos), (x_pos + width - 1, y_pos + height - 1))

    bar_height = max(24, int(height * 0.05))
    title_rect = pygame.Rect(x_pos + 4, y_pos + 4, width - 8, bar_height)
    pygame.draw.rect(surface, FRAME_LIGHT, title_rect)
    pygame.draw.rect(surface, FRAME_DARK, title_rect, 1)

    button_width = 18
    left_button = pygame.Rect(x_pos + 8, y_pos + 7, button_width, bar_height - 6)
    right_button = pygame.Rect(x_pos + width - 8 - button_width, y_pos + 7, button_width, bar_height - 6)
    pygame.draw.rect(surface, FRAME_MID, left_button)
    pygame.draw.rect(surface, FRAME_MID, right_button)
    pygame.draw.rect(surface, FRAME_DARK, left_button, 1)
    pygame.draw.rect(surface, FRAME_DARK, right_button, 1)
    pygame.draw.line(surface, BLACK, (left_button.x + 4, left_button.centery), (left_button.right - 4, left_button.centery), 2)
    pygame.draw.line(surface, BLACK, (right_button.x + 4, right_button.centery), (right_button.right - 4, right_button.centery), 2)

    title_surface = font_title.render(title, True, (80, 80, 80))
    title_pos = title_surface.get_rect(center=(x_pos + width // 2, y_pos + 4 + bar_height // 2))
    surface.blit(title_surface, title_pos)

    pad = 6
    inner = pygame.Rect(x_pos + pad, y_pos + bar_height + pad, width - pad * 2, height - bar_height - pad * 2 - 10)

    inner_surface = make_terminal_background(scene_base, inner)
    surface.blit(inner_surface, inner.topleft)
    pygame.draw.rect(surface, BLACK, inner, 2)

    bottom_height = 12
    bottom_rect = pygame.Rect(x_pos + 4, y_pos + height - bottom_height - 4, width - 8, bottom_height)
    pygame.draw.rect(surface, FRAME_LIGHT, bottom_rect)
    pygame.draw.rect(surface, FRAME_DARK, bottom_rect, 1)

    handle = pygame.Rect(bottom_rect.x + 80, bottom_rect.y + 1, 18, bottom_rect.h - 2)
    pygame.draw.rect(surface, FRAME_MID, handle)
    pygame.draw.rect(surface, FRAME_DARK, handle, 1)

    return inner


class KeyboardWindow:
    def __init__(self):
        self.rect = pygame.Rect(225, 555, 1088, 282)
        self.grid = [
            ["ESC", "A", "B", "C", "D", "E", "F", "G", "H", "BACK"],
            ["I", "J", "K", "L", "M", "N", "O", "P", "Q", "ENTER"],
            ["R", "S", "T", "U", "V", "W", "X", "Y", "Z", "ENTER"],
        ]
        self.row = 0
        self.col = 1

    def move(self, dx, dy):
        old_row = self.row
        old_col = self.col

        if dy != 0:
            new_row = max(0, min(2, self.row + dy))
            if self.col == 9:
                self.row = new_row
            else:
                self.row = new_row
                if self.row == 2 and self.col > 8:
                    self.col = 8

        if dx != 0:
            if self.row == 0:
                self.col = max(0, min(9, self.col + dx))
            elif self.row in (1, 2):
                self.col = max(0, min(9, self.col + dx))

        if old_row != self.row or old_col != self.col:
            play_choose()

    def get_label(self):
        return self.grid[self.row][self.col]

    def draw(self, surface):
        inner = draw_window(surface, self.rect, surface.copy(), "KEYBOARD(1:1)")

        start_x = inner.x + 6
        start_y = inner.y + 8
        cell_w = 102
        cell_h = 78
        gap = 6

        for row_idx in range(3):
            for col_idx in range(10):
                label = self.grid[row_idx][col_idx]

                if row_idx == 2 and col_idx == 9:
                    continue

                x_pos = start_x + col_idx * (cell_w + gap)
                y_pos = start_y + row_idx * (cell_h + gap)

                width = cell_w
                height = cell_h

                if label == "ENTER":
                    width = cell_w
                    height = cell_h * 2 + gap

                rect = pygame.Rect(x_pos, y_pos, width, height)
                selected = row_idx == self.row and col_idx == self.col

                fill = KEY_FILL_HI if selected else KEY_FILL
                pygame.draw.rect(surface, fill, rect)
                pygame.draw.rect(surface, FRAME_DARK, rect, 2)
                pygame.draw.line(surface, WHITE_DIRTY, (rect.x + 1, rect.y + 1), (rect.right - 2, rect.y + 1))
                pygame.draw.line(surface, WHITE_DIRTY, (rect.x + 1, rect.y + 1), (rect.x + 1, rect.bottom - 2))

                if label == "BACK":
                    lines = ["BACK", "SPACE"]
                    for idx, txt in enumerate(lines):
                        txt_surface = font_key_small.render(txt, True, KEY_TEXT)
                        txt_rect = txt_surface.get_rect(center=(rect.centerx, rect.y + 24 + idx * 22))
                        surface.blit(txt_surface, txt_rect)
                elif label == "ESC":
                    txt_surface = font_key.render(label, True, KEY_TEXT)
                    txt_rect = txt_surface.get_rect(center=rect.center)
                    surface.blit(txt_surface, txt_rect)
                elif label == "ENTER":
                    pygame.draw.line(surface, KEY_TEXT, (rect.centerx + 18, rect.bottom - 24), (rect.centerx - 6, rect.bottom - 24), 5)
                    pygame.draw.line(surface, KEY_TEXT, (rect.centerx - 6, rect.bottom - 24), (rect.centerx + 18, rect.bottom - 50), 5)
                else:
                    txt_surface = font_key.render(label, True, KEY_TEXT)
                    txt_rect = txt_surface.get_rect(center=rect.center)
                    surface.blit(txt_surface, txt_rect)


class App:
    def __init__(self):
        self.running = True
        self.state = "idle_bg"
        self.state_timer = 0.0

        self.target_rect = pygame.Rect(64, 48, 1134, 530)
        self.grow_origin = (150, 120)
        self.grow_start_size = (160, 70)
        self.grow_duration = 0.46
        self.idle_bg_duration = 0.45

        self.opening_lines = [
            ("Umbrella Security System", WHITE_DIRTY),
            ("First Class", WHITE_DIRTY),
            ("Medical Storage Room:", WHITE_DIRTY),
        ]

        self.main_lines = [
            ("Security Authorization", WHITE_DIRTY),
            ("Current Status: ", WHITE_DIRTY, "Locked", RED_TEXT),
            ("Please enter password and", WHITE_DIRTY),
            ("then press the RETURN key.", WHITE_DIRTY),
        ]

        self.success_lines = [
            ("Password: Confirmed", WHITE_DIRTY),
            ("Room Access: Confirmed", WHITE_DIRTY),
            ("Deactivating lock.", WHITE_DIRTY),
            ("Please wait...", WHITE_DIRTY),
            ("Current Status: ", WHITE_DIRTY, "Unlocked", WHITE_DIRTY),
            ("-", WHITE_DIRTY),
        ]

        self.valid_passwords = PASSWORD_OPTIONS[:]
        self.visible_lines = []
        self.current_block = []
        self.block_index = 0
        self.block_char = 0
        self.block_done = False
        self.typing_accum = 0.0

        self.opening_speed = 0.050
        self.normal_speed = 0.040
        self.success_speed = 0.042

        self.pause_after_opening = 0.50
        self.pause_after_main = 0.55
        self.pause_after_finish = 0.65

        self.input_text = ""
        self.cursor_timer = 0.0
        self.cursor_on = True

        self.keyboard = KeyboardWindow()

        self.flash_timer = 0.0
        self.flash_alpha = 0

    def current_window_rect(self):
        if self.state != "grow":
            return self.target_rect.copy()

        factor = ease_out_cubic(min(1.0, self.state_timer / self.grow_duration))
        start_width, start_height = self.grow_start_size
        target_width, target_height = self.target_rect.size

        width = int(lerp(start_width, target_width, factor))
        height = int(lerp(start_height, target_height, factor))
        x_pos = int(lerp(self.grow_origin[0], self.target_rect.x, factor))
        y_pos = int(lerp(self.grow_origin[1], self.target_rect.y, factor))
        return pygame.Rect(x_pos, y_pos, width, height)

    def current_speed(self):
        if self.state == "typing_opening":
            return self.opening_speed
        if self.state in ("typing_main", "typing_success"):
            return self.success_speed if self.state == "typing_success" else self.normal_speed
        return self.normal_speed

    def begin_block(self, block_lines):
        self.current_block = block_lines
        self.block_index = 0
        self.block_char = 0
        self.block_done = False
        self.typing_accum = 0.0
        if not self.visible_lines:
            self.visible_lines = [""]

    def finalize_current_line(self, line):
        if len(line) in (4, 6):
            self.visible_lines[-1] = line
        else:
            if isinstance(self.visible_lines[-1], str):
                self.visible_lines[-1] = (self.visible_lines[-1], line[1])
            else:
                self.visible_lines[-1] = line

    def play_char_sound(self):
        if self.state == "typing_opening":
            play_typing_open()
        else:
            play_typing_normal()

    def update_typing_block(self, dt):
        if self.block_done:
            return

        self.typing_accum += dt
        speed = self.current_speed()

        while self.typing_accum >= speed and not self.block_done:
            self.typing_accum -= speed

            if self.block_index >= len(self.current_block):
                self.block_done = True
                break

            line = self.current_block[self.block_index]
            text = line[0]

            if self.block_char < len(text):
                char = text[self.block_char]
                if not isinstance(self.visible_lines[-1], str):
                    self.visible_lines.append("")
                self.visible_lines[-1] += char
                self.block_char += 1
                if char != " ":
                    self.play_char_sound()
            else:
                self.finalize_current_line(line)
                self.block_index += 1
                self.block_char = 0
                if self.block_index < len(self.current_block):
                    self.visible_lines.append("")
                else:
                    self.block_done = True

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "typing_opening":
            self.visible_lines = [""]
            self.begin_block(self.opening_lines)

        elif new_state == "typing_main":
            if self.visible_lines and self.visible_lines[-1] != "":
                self.visible_lines.append("")
            self.begin_block(self.main_lines)

        elif new_state == "password_entry":
            self.cursor_timer = 0.0
            self.cursor_on = True
            self.input_text = ""
            self.keyboard = KeyboardWindow()

        elif new_state == "submitting":
            play_finish()

        elif new_state == "typing_success":
            self.visible_lines = [""]
            self.begin_block(self.success_lines)

        elif new_state == "invalid":
            self.flash_timer = 0.35
            self.flash_alpha = 100

        elif new_state == "done":
            self.cursor_on = False

    def submit_password(self):
        play_finish()
        if self.input_text in self.valid_passwords:
            self.set_state("submitting")
        else:
            self.set_state("invalid")

    def activate_key(self):
        label = self.keyboard.get_label()

        if label == "ESC":
            self.running = False
            return

        if label == "BACK":
            if self.input_text:
                self.input_text = self.input_text[:-1]
                play_enter()
            return

        if label == "ENTER":
            if self.input_text:
                self.submit_password()
            return

        if len(label) == 1 and label.isalpha():
            if len(self.input_text) < 8:
                self.input_text += label
                play_enter()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.state not in ("password_entry",):
                self.running = False
                return

            if self.state == "password_entry":
                if event.key == pygame.K_LEFT:
                    self.keyboard.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.keyboard.move(1, 0)
                elif event.key == pygame.K_UP:
                    self.keyboard.move(0, -1)
                elif event.key == pygame.K_DOWN:
                    self.keyboard.move(0, 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.activate_key()

            elif self.state == "done":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.running = False

    def update_cursor(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.45:
            self.cursor_timer = 0.0
            self.cursor_on = not self.cursor_on

    def update(self, dt):
        self.state_timer += dt

        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_timer = 0
                self.flash_alpha = 0

        if self.state == "idle_bg":
            if self.state_timer >= self.idle_bg_duration:
                self.set_state("grow")

        elif self.state == "grow":
            if self.state_timer >= self.grow_duration:
                self.set_state("typing_opening")

        elif self.state == "typing_opening":
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("pause_opening")

        elif self.state == "pause_opening":
            if self.state_timer >= self.pause_after_opening:
                self.set_state("typing_main")

        elif self.state == "typing_main":
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("pause_main")

        elif self.state == "pause_main":
            if self.state_timer >= self.pause_after_main:
                self.set_state("password_entry")

        elif self.state == "password_entry":
            self.update_cursor(dt)

        elif self.state == "submitting":
            if self.state_timer >= self.pause_after_finish:
                self.set_state("typing_success")

        elif self.state == "typing_success":
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("done")

        elif self.state == "invalid":
            if self.state_timer >= 0.40:
                self.input_text = ""
                self.set_state("password_entry")

    def draw_program_lines(self, inner_rect):
        x_pos = inner_rect.x + 14
        y_pos = inner_rect.y + 6
        line_height = 44

        for item in self.visible_lines:
            if isinstance(item, str):
                draw_shadow_text(screen, font_term, item, WHITE_DIRTY, SHADOW, (x_pos, y_pos))
            else:
                if len(item) == 2:
                    txt, color = item
                    draw_shadow_text(screen, font_term, txt, color, SHADOW, (x_pos, y_pos))
                elif len(item) == 4:
                    left_txt, left_col, right_txt, right_col = item
                    draw_shadow_text(screen, font_term, left_txt, left_col, SHADOW, (x_pos, y_pos))
                    offset = font_term.size(left_txt)[0]
                    draw_shadow_text(screen, font_term, right_txt, right_col, RED_DARK if right_col == RED_TEXT else SHADOW, (x_pos + offset, y_pos))
                elif len(item) == 6:
                    left_txt, left_col, mid_txt, mid_col, right_txt, right_col = item
                    draw_shadow_text(screen, font_term, left_txt, left_col, SHADOW, (x_pos, y_pos))
                    offset = font_term.size(left_txt)[0]
                    draw_shadow_text(screen, font_term, mid_txt, mid_col, SHADOW, (x_pos + offset, y_pos))
                    offset += font_term.size(mid_txt)[0]
                    draw_shadow_text(screen, font_term, right_txt, right_col, SHADOW, (x_pos + offset, y_pos))
            y_pos += line_height

        if self.state == "password_entry":
            prompt_y = inner_rect.y + 6 + len(self.visible_lines) * line_height
            prompt_x = inner_rect.x + 14
            prefix = "Enter Password:"
            draw_shadow_text(screen, font_term, prefix, WHITE_DIRTY, SHADOW, (prompt_x, prompt_y))
            prefix_w = font_term.size(prefix)[0]
            draw_shadow_text(screen, font_term, self.input_text, WHITE_DIRTY, SHADOW, (prompt_x + prefix_w, prompt_y))
            if self.cursor_on:
                input_w = font_term.size(self.input_text)[0]
                draw_shadow_text(screen, font_term, "_", WHITE_DIRTY, SHADOW, (prompt_x + prefix_w + input_w, prompt_y))

    def render(self):
        scene_base = build_scene_base()
        screen.blit(scene_base, (0, 0))

        rect = self.current_window_rect() if self.state != "idle_bg" else None

        if rect:
            inner_rect = draw_window(screen, rect, scene_base, "PROGRAM(1:1)")
            if rect.w > 280 and rect.h > 150 and self.state != "grow":
                self.draw_program_lines(inner_rect)

        if self.state == "password_entry":
            self.keyboard.draw(screen)

        if self.flash_alpha > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, self.flash_alpha))
            screen.blit(overlay, (0, 0))

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

        typing_channel.stop()
        ui_channel.stop()


if __name__ == "__main__":
    App().run()
    pygame.quit()
    sys.exit()