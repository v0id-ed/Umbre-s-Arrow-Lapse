import pygame
import random
import sys
import os
from PIL import Image, ImageSequence

pygame.init()

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arrow Timing Game")
CLOCK = pygame.time.Clock()
FPS = 60
GAME_DURATION = 120  # seconds (2 minutes)

# ---------------- COLORS ----------------
GRAY = (150, 150, 150)
BLACK = (0, 0, 0)
YELLOW = (255, 230, 0)

# ---------------- BACKGROUND ----------------
background = pygame.Surface((WIDTH, HEIGHT))
background.fill(GRAY)

BAR_Y = HEIGHT // 2
BOX_SIZE = 40
FONT = pygame.font.SysFont(None, 36)
BIG_FONT = pygame.font.SysFont(None, 64)

READY_TIME = 800
GO_TIME = 600
POP_DURATION = 300

# ---------------- LOAD GIF ----------------
def load_gif(path, max_w=None, max_h=None):
    gif = Image.open(path)
    frames = []
    durations = []

    for frame in ImageSequence.Iterator(gif):
        frame = frame.convert("RGBA")
        if max_w and max_h:
            w, h = frame.size
            scale = min(max_w / w, max_h / h, 1)
            frame = frame.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        surf = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert_alpha()
        frames.append(surf)
        durations.append(frame.info.get("duration", 100))

    return frames, durations

# ---------------- GAMEPLAY GIF ----------------
PLAY_FRAMES, PLAY_DURATIONS = load_gif(
    os.path.join("gifs", "Umbreon dancing.gif"),
    WIDTH * 0.6,
    HEIGHT * 0.35
)

gif_state = {"index": 0, "last_update": pygame.time.get_ticks()}

def draw_animated_gif(frames, durations, center, state):
    now = pygame.time.get_ticks()
    if now - state["last_update"] >= durations[state["index"]]:
        state["index"] = (state["index"] + 1) % len(frames)
        state["last_update"] = now
    rect = frames[state["index"]].get_rect(center=center)
    SCREEN.blit(frames[state["index"]], rect)

# ---------------- BUTTON ----------------
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self):
        pygame.draw.rect(SCREEN, BLACK, self.rect, border_radius=8)
        txt = FONT.render(self.text, True, YELLOW)
        SCREEN.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

# ---------------- ARROW BOX ----------------
class ArrowBox:
    def __init__(self, arrow):
        self.arrow = arrow
        self.y = BAR_Y
        self.x = {
            "left": WIDTH * 0.25 - BOX_SIZE // 2,
            "right": WIDTH * 0.75 - BOX_SIZE // 2,
            "up": WIDTH // 2 - BOX_SIZE // 2,
            "down": WIDTH // 2 - BOX_SIZE // 2
        }[arrow]
        self.rect = pygame.Rect(self.x, self.y, BOX_SIZE, BOX_SIZE)

    def update(self, speed):
        self.y += speed
        self.rect.y = self.y

    def draw(self):
        pygame.draw.rect(SCREEN, BLACK, self.rect, border_radius=6)
        cx, cy = self.rect.center
        s = 10
        shapes = {
            "up": [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)],
            "down": [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)],
            "left": [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)],
            "right": [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
        }
        pygame.draw.polygon(SCREEN, YELLOW, shapes[self.arrow])

# ---------------- GAME STATE ----------------
def reset_game():
    return {
        "boxes": [],
        "queue": [],
        "spawn_timer": 0,
        "speed": 2.5,
        "start_time": 0,
        "countdown": True,
        "countdown_phase": "ready",
        "countdown_timer": pygame.time.get_ticks(),
        "game_over": False
    }

game_started = False
game = reset_game()

start_button = Button((WIDTH//2 - 75, BAR_Y + 200, 150, 50), "Start")
play_again_button = Button((WIDTH//2 - 100, HEIGHT - 100, 200, 50), "Play Again")

# ---------------- MAIN LOOP ----------------
while True:
    CLOCK.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if not game_started:
            if start_button.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                game_started = True
                game = reset_game()
                gif_state["index"] = 0

        elif game["game_over"]:
            if play_again_button.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                game_started = False
                game = reset_game()

        elif not game["countdown"] and event.type == pygame.KEYDOWN and game["queue"]:
            key_map = {
                pygame.K_LEFT: "left",
                pygame.K_RIGHT: "right",
                pygame.K_UP: "up",
                pygame.K_DOWN: "down"
            }
            if event.key in key_map:
                if key_map[event.key] == game["queue"][0]:
                    game["queue"].pop(0)
                    game["boxes"].pop(0)
                else:
                    game["game_over"] = True

    SCREEN.blit(background, (0, 0))
    pygame.draw.rect(SCREEN, YELLOW, (0, BAR_Y - 4, WIDTH, 8))

    # -------- START SCREEN --------
    if not game_started:
        title = BIG_FONT.render("Arrow Timing Game", True, YELLOW)
        SCREEN.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//3)))
        start_button.draw()

    # -------- GAME RUNNING --------
    elif not game["game_over"]:
        draw_animated_gif(PLAY_FRAMES, PLAY_DURATIONS, (WIDTH//2, HEIGHT//4), gif_state)

        if game["countdown"]:
            now = pygame.time.get_ticks()
            elapsed = now - game["countdown_timer"]
            text = "Ready?" if game["countdown_phase"] == "ready" else "Go!"
            total = READY_TIME if game["countdown_phase"] == "ready" else GO_TIME

            scale = min(elapsed / POP_DURATION, 1) * 0.5 + 0.5
            surf = BIG_FONT.render(text, True, YELLOW)
            surf = pygame.transform.rotozoom(surf, 0, scale)
            SCREEN.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT * 0.7)))

            if elapsed >= total:
                if game["countdown_phase"] == "ready":
                    game["countdown_phase"] = "go"
                    game["countdown_timer"] = now
                else:
                    game["countdown"] = False
                    game["start_time"] = pygame.time.get_ticks()
        else:
            elapsed = (pygame.time.get_ticks() - game["start_time"]) / 1000

            if elapsed >= GAME_DURATION:
                game["game_over"] = True

            game["spawn_timer"] += 1
            if game["spawn_timer"] >= 35:
                arrow = random.choice(["left", "right", "up", "down"])
                game["boxes"].append(ArrowBox(arrow))
                game["queue"].append(arrow)
                game["spawn_timer"] = 0
                game["speed"] += 0.05

            for box in game["boxes"]:
                box.update(game["speed"])
                box.draw()
                if box.y > HEIGHT:
                    game["game_over"] = True

            timer = FONT.render(f"{elapsed:05.2f}", True, YELLOW)
            SCREEN.blit(timer, (WIDTH - timer.get_width() - 10, 10))

    # -------- GAME OVER --------
    else:
        over = BIG_FONT.render("Time's Up!", True, YELLOW)
        SCREEN.blit(over, over.get_rect(center=(WIDTH//2, HEIGHT//2)))
        play_again_button.draw()

    pygame.display.flip()
