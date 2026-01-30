import pygame
import random
import sys
import os
from PIL import Image, ImageSequence

pygame.init()

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sonic Arrow Lapse!")
CLOCK = pygame.time.Clock()
FPS = 60

# ---------------- COLORS ----------------
TAN = (255, 218, 185)
WHITE = (255, 255, 255)
RED = (200, 0, 0)
YELLOW = (255, 251, 0)
GREEN = (0, 220, 0)
SONIC_BLUE = (0, 112, 221)
BRONZE = (205, 127, 50)
SILVER = (192, 192, 192)
GOLD = (255, 215, 0)
BLACK = (0, 0, 0)

# ---------------- BACKGROUND ----------------
try:
    background_image = pygame.image.load("Background.png").convert()
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
except pygame.error:
    background_image = pygame.Surface((WIDTH, HEIGHT))
    background_image.fill(TAN)

# ---------------- INTRO IMAGE ----------------
INTRO_IMAGE = pygame.image.load("Sonic.jpg").convert_alpha()
intro_rect = INTRO_IMAGE.get_rect(center=(WIDTH // 2, HEIGHT // 4))

BAR_Y = HEIGHT // 2
BOX_SIZE = 40

FONT = pygame.font.SysFont(None, 36)
BIG_FONT = pygame.font.SysFont(None, 64)

READY_TIME = 800
GO_TIME = 600
POP_DURATION = 300

# ---------------- LOAD GIF ----------------
def load_gif(path, max_w=None, max_h=None):
    try:
        gif = Image.open(path)
    except Exception:
        surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        return [surf], [100]

    frames = []
    durations = []

    for frame in ImageSequence.Iterator(gif):
        frame = frame.convert("RGBA")
        if max_w and max_h:
            w, h = frame.size
            scale = min(max_w / w, max_h / h, 1)
            frame = frame.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert_alpha()
        frames.append(surface)
        durations.append(frame.info.get("duration", 100))
    return frames, durations

# ---------------- DANCING GIF ----------------
DANCING_FRAMES, DANCING_DURATIONS = load_gif(os.path.join("gifs", "Dancing.gif"), WIDTH * 0.6, HEIGHT * 0.4)

# ---------------- RANK GIFS ----------------
RANK_GIFS = {
    rank: load_gif(os.path.join("gifs", f"Rank {rank}.gif"), WIDTH * 0.6, HEIGHT * 0.4)
    for rank in ["D", "C", "B", "A", "S"]
}

RANK_COLORS = {"D": RED, "C": WHITE, "B": BRONZE, "A": SILVER, "S": GOLD}

# ---------------- GIF DRAWING ----------------
def draw_animated_gif(frames, durations, center, gif_state):
    now = pygame.time.get_ticks()
    if now - gif_state["last_update"] >= durations[gif_state["index"]]:
        gif_state["index"] = (gif_state["index"] + 1) % len(frames)
        gif_state["last_update"] = now
    rect = frames[gif_state["index"]].get_rect(center=center)
    SCREEN.blit(frames[gif_state["index"]], rect)

# ---------------- OUTLINED TEXT ----------------
def draw_outlined_text(text, font, fill, outline, pos, thickness=2):
    base = font.render(text, True, fill)
    outline_surf = font.render(text, True, outline)
    rect = base.get_rect(topleft=pos)

    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx != 0 or dy != 0:
                SCREEN.blit(outline_surf, rect.move(dx, dy))
    SCREEN.blit(base, rect)

# ---------------- BUTTON ----------------
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, color):
        pygame.draw.rect(SCREEN, color, self.rect, border_radius=8)
        txt = FONT.render(self.text, True, WHITE)
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
        pygame.draw.rect(SCREEN, SONIC_BLUE, self.rect, border_radius=6)
        cx, cy = self.rect.center
        s = 10
        shapes = {
            "up": [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)],
            "down": [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)],
            "left": [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)],
            "right": [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
        }
        pygame.draw.polygon(SCREEN, WHITE, shapes[self.arrow])

# ---------------- GAME STATE ----------------
def reset_game():
    return {
        "boxes": [], "queue": [], "spawn_timer": 0, "speed": 2.5,
        "start_time": 0, "game_over": False, "rank": None,
        "countdown": True, "countdown_phase": "ready",
        "countdown_timer": pygame.time.get_ticks(),
        "rank_gif": None, "rank_state": {"index": 0, "last_update": pygame.time.get_ticks()},
        "dancing_state": {"index": 0, "last_update": pygame.time.get_ticks()}
    }

game_started = False
game = reset_game()
start_button = Button((WIDTH//2 - 75, BAR_Y + 200, 150, 50), "Start")
play_again_button = Button((WIDTH//2 - 100, HEIGHT - 100, 200, 50), "Play Again")

# ---------------- GAME OVER ----------------
def trigger_game_over():
    game["game_over"] = True
    elapsed = (pygame.time.get_ticks() - game["start_time"]) / 1000
    if elapsed < 3: game["rank"] = "D"
    elif elapsed < 4: game["rank"] = "C"
    elif elapsed < 6: game["rank"] = "B"
    elif elapsed < 9: game["rank"] = "A"
    else: game["rank"] = "S"
    game["rank_gif"] = RANK_GIFS[game["rank"]]

# ---------------- MAIN LOOP ----------------
while True:
    CLOCK.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if not game_started:
            if start_button.clicked(event) or (event.type==pygame.KEYDOWN and event.key==pygame.K_RETURN):
                game_started=True
                game=reset_game()
        elif game["game_over"]:
            if play_again_button.clicked(event) or (event.type==pygame.KEYDOWN and event.key==pygame.K_RETURN):
                game_started=False
                game=reset_game()
        elif not game["countdown"] and event.type==pygame.KEYDOWN and game["queue"]:
            key_map={pygame.K_LEFT:"left", pygame.K_RIGHT:"right", pygame.K_UP:"up", pygame.K_DOWN:"down"}
            if event.key in key_map:
                if key_map[event.key]==game["queue"][0]:
                    game["queue"].pop(0)
                    game["boxes"].pop(0)
                else: trigger_game_over()

    SCREEN.blit(background_image,(0,0))
    pygame.draw.rect(SCREEN,SONIC_BLUE,(0,BAR_Y-4,WIDTH,8))

    # -------- START SCREEN --------
    if not game_started:
        SCREEN.blit(INTRO_IMAGE, intro_rect)
        draw_outlined_text(
            "Sonic Arrow Lapse!",
            BIG_FONT,
            GOLD,
            SONIC_BLUE,
            (WIDTH//2 - 210, BAR_Y//2 + 240),
            thickness=5
        )
        start_button.draw(SONIC_BLUE)

    # -------- GAME RUNNING --------
    elif not game["game_over"]:
        draw_animated_gif(DANCING_FRAMES,DANCING_DURATIONS,(WIDTH//2,HEIGHT//4),game["dancing_state"])

        if game["countdown"]:
            now = pygame.time.get_ticks()
            elapsed = now - game["countdown_timer"]
            text = "Ready?" if game["countdown_phase"]=="ready" else "Gotta go fast!"
            total = READY_TIME if game["countdown_phase"]=="ready" else GO_TIME

            # -------- POP-UP WITH OUTLINE --------
            scale = min(elapsed/POP_DURATION,1)*0.5+0.5
            text_surf = BIG_FONT.render(text,True,GREEN)
            outline_surf = BIG_FONT.render(text,True,WHITE)
            temp_surf = pygame.Surface((text_surf.get_width()+8,text_surf.get_height()+8),pygame.SRCALPHA)
            for dx in range(-3,4):   # thicker outline
                for dy in range(-3,4):
                    if dx!=0 or dy!=0:
                        temp_surf.blit(outline_surf,(dx+4,dy+4))
            temp_surf.blit(text_surf,(4,4))
            scaled_surf = pygame.transform.rotozoom(temp_surf,0,scale)
            SCREEN.blit(scaled_surf,scaled_surf.get_rect(center=(WIDTH//2,int(HEIGHT*0.7))))

            if elapsed>=total:
                if game["countdown_phase"]=="ready":
                    game["countdown_phase"]="go"
                    game["countdown_timer"]=now
                else:
                    game["countdown"]=False
                    game["start_time"]=pygame.time.get_ticks()

        else:
            elapsed=(pygame.time.get_ticks()-game["start_time"])/1000
            minutes=int(elapsed//60)
            seconds=int(elapsed%60)
            millis=int((elapsed%1)*1000)
            timer_txt=FONT.render(f"{minutes}:{seconds:02d}.{millis:03d}",True,WHITE)
            SCREEN.blit(timer_txt,(WIDTH-timer_txt.get_width()-10,10))

            game["spawn_timer"]+=1
            if game["spawn_timer"]>=35:
                arrow=random.choice(["left","right","up","down"])
                game["boxes"].append(ArrowBox(arrow))
                game["queue"].append(arrow)
                game["spawn_timer"]=0
                game["speed"]+=0.05

            for box in game["boxes"]:
                box.update(game["speed"])
                box.draw()
                if box.y>HEIGHT: trigger_game_over()

    # -------- GAME OVER --------
    else:
        draw_animated_gif(*game["rank_gif"],(WIDTH//2,HEIGHT//4),game["rank_state"])
        if game["rank"] is not None:
            rank_color = RANK_COLORS[game["rank"]]
            outline_color = BLACK if game["rank"]=="C" else WHITE
            draw_outlined_text(f"You got rank {game['rank']}",BIG_FONT,rank_color,outline_color,(WIDTH//2-160,HEIGHT//2+90))
            play_again_button.draw(SONIC_BLUE)

    pygame.display.flip()
