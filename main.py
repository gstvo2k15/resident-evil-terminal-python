import sys
from pathlib import Path

import pygame

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 800
SCREEN_H = 600
FPS = 60

IMG_BG = BASE_DIR / "skycard_0.png"
IMG_1 = BASE_DIR / "skycard_1.png"
IMG_2 = BASE_DIR / "skycard_2.png"

SND_ACCEPT = BASE_DIR / "accept.mp3"
SND_WAITING = BASE_DIR / "beep_waitting.mp3"
SND_MAIN = BASE_DIR / "beep_main.mp3"

WHITE = (235, 235, 235)
GREEN = (0, 200, 40)
DARK_GREEN = (20, 60, 20)
SHADOW = (60, 60, 60)
BLACK = (0, 0, 0)

# Rectángulo aproximado de la gran ventana "PROGRAM(011)"
# Ajustado a tus capturas 800x600
PROGRAM_RECT = pygame.Rect(34, 18, 633, 284)

# =========================================================
# HELPERS
# =========================================================
def load_image(path: Path) -> pygame.Surface:
    if not path.exists():
        raise FileNotFoundError(f"Falta imagen: {path}")
    return pygame.transform.smoothscale(
        pygame.image.load(str(path)).convert(),
        (SCREEN_W, SCREEN_H)
    )

def load_sound(path: Path):
    if not path.exists():
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None

def blit_text_shadow(surface, font, text, color, shadow_color, x, y):
    s = font.render(text, True, shadow_color)
    t = font.render(text, True, color)
    surface.blit(s, (x + 2, y + 2))
    surface.blit(t, (x, y))

def crop_program_window(full_img: pygame.Surface) -> pygame.Surface:
    cropped = pygame.Surface((PROGRAM_RECT.width, PROGRAM_RECT.height)).convert()
    cropped.blit(full_img, (0, 0), PROGRAM_RECT)
    return cropped

def draw_arrow(surface, x, y):
    pts = [(x, y), (x + 12, y + 8), (x, y + 16)]
    pygame.draw.polygon(surface, WHITE, pts)
    pygame.draw.polygon(surface, SHADOW, pts, 1)

# =========================================================
# SCENE
# =========================================================
class RetroDoorLock:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True

        # Recursos
        self.bg = load_image(IMG_BG)
        img1 = load_image(IMG_1)
        img2 = load_image(IMG_2)

        # Extraemos solo la gran ventana de las capturas 1 y 2
        self.program_empty = crop_program_window(img1)
        self.program_info = crop_program_window(img2)

        self.snd_accept = load_sound(SND_ACCEPT)
        self.snd_waiting = load_sound(SND_WAITING)
        self.snd_main = load_sound(SND_MAIN)

        self.wait_channel = pygame.mixer.Channel(1)

        # Fuentes
        self.font_terminal = pygame.font.SysFont("couriernew", 34, bold=True)
        self.font_prompt = pygame.font.SysFont("couriernew", 30, bold=True)
        self.font_choice = pygame.font.SysFont("couriernew", 38, bold=True)

        # Estados
        self.state = "boot"
        self.timer = 0.0

        # Typing
        self.text_lines = []
        self.current_line_index = 0
        self.current_char_index = 0
        self.typing_speed = 0.035
        self.typing_accum = 0.0
        self.visible_lines = []

        # Selección
        self.selected = 0
        self.options = ["Yes", "No"]

        self.prepare_info_text()

    def prepare_info_text(self):
        self.text_lines = [
            "DOOR LOCK SERVICE",
            "----------------------------",
            "Hall side doors:      LOCKED",
            "",
            "The doors can be unlocked",
            "by a CARD KEY.",
            "",
            "-"
        ]
        self.current_line_index = 0
        self.current_char_index = 0
        self.visible_lines = [""]  # línea actual
        self.typing_accum = 0.0

    def reset_typing(self):
        self.prepare_info_text()

    def play(self, snd, loops=0):
        if snd:
            snd.play(loops=loops)

    def set_state(self, state):
        self.state = state
        self.timer = 0.0

        if state == "window_empty":
            self.play(self.snd_main)

        elif state == "typing_info":
            self.play(self.snd_main)
            self.reset_typing()

        elif state == "question":
            self.play(self.snd_main)

        elif state == "checking":
            if self.snd_waiting:
                self.wait_channel.play(self.snd_waiting, loops=-1)

        elif state == "done":
            self.wait_channel.stop()
            self.play(self.snd_accept)

    def update_typing(self, dt):
        if self.current_line_index >= len(self.text_lines):
            return

        self.typing_accum += dt
        while self.typing_accum >= self.typing_speed:
            self.typing_accum -= self.typing_speed

            full_line = self.text_lines[self.current_line_index]

            if self.current_char_index < len(full_line):
                current = self.visible_lines[-1]
                current += full_line[self.current_char_index]
                self.visible_lines[-1] = current
                self.current_char_index += 1
            else:
                self.current_line_index += 1
                self.current_char_index = 0
                if self.current_line_index < len(self.text_lines):
                    self.visible_lines.append("")

    def update(self, dt):
        self.timer += dt

        if self.state == "boot":
            if self.timer >= 0.7:
                self.set_state("window_empty")

        elif self.state == "window_empty":
            if self.timer >= 0.9:
                self.set_state("typing_info")

        elif self.state == "typing_info":
            self.update_typing(dt)

        elif self.state == "checking":
            if self.timer >= 2.0:
                self.set_state("done")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return

            if self.state == "typing_info":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.current_line_index < len(self.text_lines):
                        self.visible_lines = self.text_lines[:]
                        self.current_line_index = len(self.text_lines)
                        self.current_char_index = 0
                    else:
                        self.set_state("question")

            elif self.state == "question":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected = max(0, self.selected - 1)
                    self.play(self.snd_main)

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected = min(1, self.selected + 1)
                    self.play(self.snd_main)

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.options[self.selected] == "Yes":
                        self.set_state("checking")
                    else:
                        self.play(self.snd_main)

            elif self.state == "done":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "typing_info":
                if self.current_line_index < len(self.text_lines):
                    self.visible_lines = self.text_lines[:]
                    self.current_line_index = len(self.text_lines)
                    self.current_char_index = 0
                else:
                    self.set_state("question")

            elif self.state == "question":
                self.set_state("checking")

            elif self.state == "done":
                self.running = False

    def draw_program_empty(self):
        self.screen.blit(self.program_empty, PROGRAM_RECT.topleft)

    def draw_program_info_window(self):
        # Base del escritorio
        self.screen.blit(self.bg, (0, 0))

        # Ventana vacía como base
        self.draw_program_empty()

        # Fondo interno oscuro semitransparente dentro de la ventana
        inner = pygame.Surface((PROGRAM_RECT.width - 12, PROGRAM_RECT.height - 28), pygame.SRCALPHA)
        inner.fill((0, 20, 20, 135))
        self.screen.blit(inner, (PROGRAM_RECT.x + 6, PROGRAM_RECT.y + 22))

        # Título superior ya forma parte del recorte, pero dibujamos el contenido textual
        x = PROGRAM_RECT.x + 10
        y = PROGRAM_RECT.y + 26

        for i, line in enumerate(self.visible_lines):
            if i == 2 and "LOCKED" in line:
                # Partimos la línea para colorear LOCKED en verde
                left = "Hall side doors:      "
                right = "LOCKED"
                blit_text_shadow(self.screen, self.font_terminal, left, WHITE, SHADOW, x, y)
                blit_text_shadow(self.screen, self.font_terminal, right, GREEN, DARK_GREEN, x + 420, y)
            elif i == 5 and "CARD KEY" in line:
                left = "by a "
                right = "CARD KEY."
                blit_text_shadow(self.screen, self.font_terminal, left, WHITE, SHADOW, x, y)
                blit_text_shadow(self.screen, self.font_terminal, right, GREEN, DARK_GREEN, x + 106, y)
            else:
                blit_text_shadow(self.screen, self.font_terminal, line, WHITE, SHADOW, x, y)

            y += 40

    def draw_question_overlay(self):
        blit_text_shadow(self.screen, self.font_prompt, "Will you use the", WHITE, SHADOW, 90, 500)
        blit_text_shadow(self.screen, self.font_prompt, "Blue Card Key?", GREEN, DARK_GREEN, 90, 540)

        blit_text_shadow(self.screen, self.font_choice, "Yes", WHITE, SHADOW, 520, 525)
        blit_text_shadow(self.screen, self.font_choice, "No", WHITE, SHADOW, 650, 525)

        if self.selected == 0:
            draw_arrow(self.screen, 490, 536)
        else:
            draw_arrow(self.screen, 620, 536)

    def draw_checking_line(self):
        blit_text_shadow(
            self.screen,
            self.font_terminal,
            "Checking up ID-CARD....",
            WHITE,
            SHADOW,
            PROGRAM_RECT.x + 10,
            PROGRAM_RECT.y + 190
        )

    def draw_done_line(self):
        blit_text_shadow(
            self.screen,
            self.font_terminal,
            "Door unlocked.",
            GREEN,
            DARK_GREEN,
            PROGRAM_RECT.x + 10,
            PROGRAM_RECT.y + 190
        )

    def render(self):
        if self.state == "boot":
            self.screen.blit(self.bg, (0, 0))

        elif self.state == "window_empty":
            self.screen.blit(self.bg, (0, 0))
            self.draw_program_empty()

        elif self.state == "typing_info":
            self.draw_program_info_window()

        elif self.state == "question":
            self.draw_program_info_window()
            self.draw_question_overlay()

        elif self.state == "checking":
            self.draw_program_info_window()
            self.draw_checking_line()

        elif self.state == "done":
            self.draw_program_info_window()
            self.draw_done_line()

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.render()

        self.wait_channel.stop()

# =========================================================
# MAIN
# =========================================================
def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Door Lock Service")

    app = RetroDoorLock(screen)
    app.run()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()