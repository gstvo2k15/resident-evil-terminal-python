import os
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

# Imágenes exactas que has subido
IMG_BG = BASE_DIR / "skycard_0.png"
IMG_1 = BASE_DIR / "skycard_1.png"
IMG_2 = BASE_DIR / "skycard_2.png"
IMG_3 = BASE_DIR / "skycard_3.png"
IMG_4 = BASE_DIR / "skycard_4.png"

# Sonidos exactos que has subido
SND_ACCEPT = BASE_DIR / "accept.mp3"
SND_WAITING = BASE_DIR / "beep_waitting.mp3"
SND_MAIN = BASE_DIR / "beep_main.mp3"

# Texto interactivo
PROMPT_TEXT_1 = "Will you use the"
PROMPT_TEXT_2 = "Blue Card Key?"
OPTIONS = ["Yes", "No"]

# Posiciones aproximadas basadas en tu captura
OPT_ARROW_POS = {
    "Yes": (500, 538),
    "No": (640, 538),
}

# =========================================================
# HELPERS
# =========================================================
def safe_load_image(path: Path) -> pygame.Surface:
    if not path.exists():
        raise FileNotFoundError(f"No existe la imagen: {path}")
    img = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))

def safe_load_sound(path: Path):
    if not path.exists():
        print(f"[WARN] No existe el sonido: {path}")
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error as e:
        print(f"[WARN] No se pudo cargar sonido {path.name}: {e}")
        return None

def play_sound(sound, loops=0):
    if sound is not None:
        sound.play(loops=loops)

def stop_sound(sound):
    if sound is not None:
        sound.stop()

def draw_shadow_text(surface, font, text, color, shadow_color, pos):
    x, y = pos
    shadow = font.render(text, True, shadow_color)
    main = font.render(text, True, color)
    surface.blit(shadow, (x + 2, y + 2))
    surface.blit(main, (x, y))

def draw_choice_arrow(surface, pos):
    x, y = pos
    # Flecha blanca simple estilo PS1
    pts = [(x, y), (x + 14, y + 8), (x, y + 16)]
    pygame.draw.polygon(surface, (230, 230, 230), pts)
    pygame.draw.polygon(surface, (80, 80, 80), pts, 1)

# =========================================================
# APP
# =========================================================
class DoorLockScene:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True

        # Estados
        self.state = "boot_bg"
        self.state_timer = 0.0

        # Selección
        self.selected_index = 0

        # Recursos
        self.bg = safe_load_image(IMG_BG)
        self.frame_1 = safe_load_image(IMG_1)
        self.frame_2 = safe_load_image(IMG_2)
        self.frame_3 = safe_load_image(IMG_3)
        self.frame_4 = safe_load_image(IMG_4)

        self.snd_accept = safe_load_sound(SND_ACCEPT)
        self.snd_waiting = safe_load_sound(SND_WAITING)
        self.snd_main = safe_load_sound(SND_MAIN)

        # Canal dedicado para el sonido de espera
        self.wait_channel = pygame.mixer.Channel(1)

        # Fuente aproximada para el overlay de opciones
        self.font_big = pygame.font.SysFont("couriernew", 40, bold=True)
        self.font_med = pygame.font.SysFont("couriernew", 34, bold=True)

    def set_state(self, new_state: str):
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "menu_empty":
            play_sound(self.snd_main)

        elif new_state == "menu_info":
            play_sound(self.snd_main)

        elif new_state == "question":
            play_sound(self.snd_main)

        elif new_state == "checking":
            if self.snd_waiting is not None:
                self.wait_channel.play(self.snd_waiting, loops=-1)

        elif new_state == "done":
            self.wait_channel.stop()
            play_sound(self.snd_accept)

    def update(self, dt: float):
        self.state_timer += dt

        if self.state == "boot_bg":
            if self.state_timer >= 0.9:
                self.set_state("menu_empty")

        elif self.state == "menu_empty":
            if self.state_timer >= 1.1:
                self.set_state("menu_info")

        elif self.state == "checking":
            if self.state_timer >= 2.2:
                self.set_state("done")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return

            if self.state == "question":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected_index = max(0, self.selected_index - 1)
                    play_sound(self.snd_main)

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected_index = min(len(OPTIONS) - 1, self.selected_index + 1)
                    play_sound(self.snd_main)

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected = OPTIONS[self.selected_index]
                    if selected == "Yes":
                        self.set_state("checking")
                    else:
                        # Si elige No, vuelve a la pregunta sin hacer nada más
                        play_sound(self.snd_main)

            elif self.state == "menu_info":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.set_state("question")

            elif self.state == "done":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "menu_info":
                self.set_state("question")
            elif self.state == "done":
                self.running = False

    def render(self):
        if self.state == "boot_bg":
            self.screen.blit(self.bg, (0, 0))

        elif self.state == "menu_empty":
            self.screen.blit(self.frame_1, (0, 0))

        elif self.state == "menu_info":
            self.screen.blit(self.frame_2, (0, 0))

        elif self.state == "question":
            self.screen.blit(self.frame_3, (0, 0))
            self.draw_question_overlay()

        elif self.state == "checking":
            self.screen.blit(self.frame_4, (0, 0))

        elif self.state == "done":
            self.screen.blit(self.frame_4, (0, 0))
            self.draw_done_overlay()

        pygame.display.flip()

    def draw_question_overlay(self):
        # Overlay inferior para emular el texto de decisión
        # Posiciones calibradas para 800x600
        draw_shadow_text(
            self.screen,
            self.font_med,
            PROMPT_TEXT_1,
            (235, 235, 235),
            (60, 60, 60),
            (92, 502),
        )
        draw_shadow_text(
            self.screen,
            self.font_med,
            PROMPT_TEXT_2,
            (0, 150, 40),
            (20, 40, 20),
            (92, 545),
        )

        draw_shadow_text(
            self.screen,
            self.font_big,
            "Yes",
            (235, 235, 235),
            (60, 60, 60),
            (530, 528),
        )
        draw_shadow_text(
            self.screen,
            self.font_big,
            "No",
            (235, 235, 235),
            (60, 60, 60),
            (658, 528),
        )

        current = OPTIONS[self.selected_index]
        draw_choice_arrow(self.screen, OPT_ARROW_POS[current])

    def draw_done_overlay(self):
        # Mensaje final sencillo
        draw_shadow_text(
            self.screen,
            self.font_med,
            "Door unlocked.",
            (0, 220, 70),
            (20, 40, 20),
            (92, 545),
        )

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
    pygame.display.set_caption("Resident Evil 2 - Door Lock Service")

    app = DoorLockScene(screen)
    app.run()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()