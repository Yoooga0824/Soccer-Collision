import pygame
import sys
import math
import random

pygame.init()

PANEL_WIDTH, PANEL_HEIGHT = 1200, 900
FIELD_MARGIN_X, FIELD_MARGIN_Y = 200, 150
WIDTH, HEIGHT = 800, 600

screen = pygame.display.set_mode((PANEL_WIDTH, PANEL_HEIGHT))
pygame.display.set_caption("Soccer Collision")

BACKGROUND = (20, 120, 40)
TRACK_COLOR = (255, 200, 220)
FIELD_LINES = (255, 255, 255)
PLAYER1_COLOR = (50, 120, 255)
PLAYER2_COLOR = (255, 80, 80)
BALL_COLOR = (255, 255, 0)
GOAL_COLOR = (200, 200, 200)
UI_BACKGROUND = (30, 30, 30, 180)
UI_TEXT = (255, 255, 255)
SCOREBOARD_BG = (70, 70, 80)
SCOREBOARD_BORDER = (200, 200, 200)

PLAYER_RADIUS = 25
BALL_RADIUS = 12
PLAYER_SPEED = 4
MAX_SHOT_POWER = 15
FRICTION = 0.96
GOAL_WIDTH = 150
GOAL_DEPTH = 20

font_large = pygame.font.Font(None, 110)
font_menu_title = pygame.font.SysFont("impact", 120, bold=True, italic=True)
font_glow = pygame.font.SysFont("impact", 120, bold=True, italic=True)
font_medium = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 30)

MENU_TEXT = (255, 255, 240)
MENU_ACCENT = (100, 255, 255)
MENU_ACCENT2 = (255, 0, 100)

history_file = "soccer_history.txt"

def field_x(x): return x + FIELD_MARGIN_X
def field_y(y): return y + FIELD_MARGIN_Y

def init_game():
    p1_x = 50 + GOAL_DEPTH + PLAYER_RADIUS + 10
    p2_x = WIDTH - 50 - GOAL_DEPTH - PLAYER_RADIUS - 10
    y_c = HEIGHT // 2
    off_y = 60
    return {
        'players1': [
            {"x": p1_x, "y": y_c, "active": False, "num": 1},
            {"x": p1_x + 100, "y": y_c - off_y, "active": False, "num": 2},
            {"x": p1_x + 100, "y": y_c + off_y, "active": False, "num": 3},
        ],
        'players2': [
            {"x": p2_x, "y": y_c, "active": False, "num": 1},
            {"x": p2_x - 100, "y": y_c - off_y, "active": False, "num": 2},
            {"x": p2_x - 100, "y": y_c + off_y, "active": False, "num": 3},
        ],
        'selected_player': 0,
        'ball': {"x": WIDTH // 2, "y": HEIGHT // 2, "vx": 0, "vy": 0},
        'current_player': 1,
        'game_state': "aiming",
        'shot_power': 0,
        'charging_power': False,
        'score': {"player1": 0, "player2": 0},
        'winner': None
    }

def reset_positions(game_state):
    p1_x = 50 + GOAL_DEPTH + PLAYER_RADIUS + 10
    p2_x = WIDTH - 50 - GOAL_DEPTH - PLAYER_RADIUS - 10
    y_c = HEIGHT // 2
    off_y = 60
    game_state['players1'][0].update({"x": p1_x, "y": y_c, "active": False})
    game_state['players1'][1].update({"x": p1_x + 100, "y": y_c - off_y, "active": False})
    game_state['players1'][2].update({"x": p1_x + 100, "y": y_c + off_y, "active": False})
    game_state['players2'][0].update({"x": p2_x, "y": y_c, "active": False})
    game_state['players2'][1].update({"x": p2_x - 100, "y": y_c - off_y, "active": False})
    game_state['players2'][2].update({"x": p2_x - 100, "y": y_c + off_y, "active": False})
    game_state['ball'].update({"x": WIDTH // 2, "y": HEIGHT // 2, "vx": 0, "vy": 0})
    game_state['shot_power'] = 0
    game_state['charging_power'] = False
    game_state['selected_player'] = 0

def save_history(score1, score2, mode="PvP"):
    try:
        with open(history_file, "a", encoding='utf-8') as f:
            f.write(f"{mode} | {score1}:{score2}\n")
    except Exception as e:
        print("Error saving history:", e)

def load_history():
    try:
        with open(history_file, "r", encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            return lines[::-1]
    except Exception:
        return []

def draw_track(screen):
    track_margin = 36
    track_rect = pygame.Rect(field_x(0) - track_margin, field_y(0) - track_margin, WIDTH + track_margin * 2, HEIGHT + track_margin * 2)
    pygame.draw.rect(screen, TRACK_COLOR, track_rect, border_radius=60)
    for i in range(1, 4):
        offset = i * 14
        pygame.draw.rect(
            screen, (255, 245, 255),
            pygame.Rect(field_x(0) - track_margin + offset, field_y(0) - track_margin + offset,
                        WIDTH + (track_margin - offset) * 2, HEIGHT + (track_margin - offset) * 2),
            2, border_radius=60 - i * 10
        )

def draw_goal_3d(screen, left=True):
    x_goal = field_x(30) if left else field_x(WIDTH - 30)
    sign = 1 if left else -1
    post_color = (210, 210, 210)
    net_color = (180, 180, 180, 80)
    pygame.draw.rect(screen, post_color,
        (x_goal - sign * 6, field_y(HEIGHT // 2 - GOAL_WIDTH // 2) - 6, sign * (GOAL_DEPTH + 12), GOAL_WIDTH + 12), border_radius=10)
    pygame.draw.rect(screen, GOAL_COLOR,
        (x_goal, field_y(HEIGHT // 2 - GOAL_WIDTH // 2), sign * GOAL_DEPTH, GOAL_WIDTH), border_radius=6)
    points_front = [
        (x_goal, field_y(HEIGHT // 2 - GOAL_WIDTH // 2)),
        (x_goal, field_y(HEIGHT // 2 + GOAL_WIDTH // 2)),
        (x_goal + sign * GOAL_DEPTH, field_y(HEIGHT // 2 + GOAL_WIDTH // 2) - 28),
        (x_goal + sign * GOAL_DEPTH, field_y(HEIGHT // 2 - GOAL_WIDTH // 2) + 28)
    ]
    pygame.draw.polygon(screen, (230, 230, 230, 40), points_front)
    net_surface = pygame.Surface((GOAL_DEPTH + 20, GOAL_WIDTH + 20), pygame.SRCALPHA)
    for i in range(0, GOAL_WIDTH + 20, 16):
        pygame.draw.line(net_surface, net_color, (0, i), (GOAL_DEPTH + 20, i // 2), 2)
    for i in range(0, GOAL_DEPTH + 20, 14):
        pygame.draw.line(net_surface, net_color, (i, 0), (i, GOAL_WIDTH + 20), 2)
    if left:
        screen.blit(net_surface, (x_goal, field_y(HEIGHT // 2 - GOAL_WIDTH // 2) - 10))
    else:
        screen.blit(pygame.transform.flip(net_surface, True, False), (x_goal - GOAL_DEPTH - 20, field_y(HEIGHT // 2 - GOAL_WIDTH // 2) - 10))

def draw_field(screen):
    pygame.draw.rect(screen, FIELD_LINES, (field_x(50), field_y(50), WIDTH - 100, HEIGHT - 100), 3)
    pygame.draw.circle(screen, FIELD_LINES, (field_x(WIDTH // 2), field_y(HEIGHT // 2)), 70, 2)
    pygame.draw.circle(screen, FIELD_LINES, (field_x(WIDTH // 2), field_y(HEIGHT // 2)), 5)
    pygame.draw.rect(screen, FIELD_LINES, (field_x(50), field_y(HEIGHT // 2 - 100), 100, 200), 2)
    pygame.draw.rect(screen, FIELD_LINES, (field_x(WIDTH - 150), field_y(HEIGHT // 2 - 100), 100, 200), 2)
    pygame.draw.rect(screen, FIELD_LINES, (field_x(50), field_y(HEIGHT // 2 - 60), 40, 120), 2)
    pygame.draw.rect(screen, FIELD_LINES, (field_x(WIDTH - 90), field_y(HEIGHT // 2 - 60), 40, 120), 2)
    pygame.draw.circle(screen, FIELD_LINES, (field_x(50 + 80), field_y(HEIGHT // 2)), 3)
    pygame.draw.circle(screen, FIELD_LINES, (field_x(WIDTH - 80), field_y(HEIGHT // 2)), 3)
    pygame.draw.line(screen, FIELD_LINES, (field_x(WIDTH // 2), field_y(50)), (field_x(WIDTH // 2), field_y(HEIGHT - 50)), 2)
    draw_goal_3d(screen, left=True)
    draw_goal_3d(screen, left=False)

def draw_soccer_ball(screen, pos, radius):
    x, y = pos
    sx, sy = field_x(x), field_y(y)
    pygame.draw.circle(screen, (235, 235, 235), (int(sx), int(sy)), radius)
    pentagon_points = [
        [(0, -1), (0.95, -0.31), (0.59, 0.81), (-0.59, 0.81), (-0.95, -0.31)],
        [(0, 1), (0.59, -0.81), (0.95, 0.31), (0, -1), (-0.59, -0.81)],
    ]
    for i in range(5):
        angle = i * (2 * math.pi / 5)
        pts = []
        for px, py in pentagon_points[0]:
            a = angle + math.atan2(py, px)
            r = radius * 0.45 if i % 2 == 0 else radius * 0.28
            pts.append((int(sx + math.cos(a) * r), int(sy + math.sin(a) * r)))
        pygame.draw.polygon(screen, (40, 40, 40), pts)
    shadow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(shadow, (50, 50, 50, 90), (radius, radius + 3), int(radius * 0.97))
    screen.blit(shadow, (int(sx - radius), int(sy - radius)), special_flags=pygame.BLEND_RGBA_ADD)

def draw_players(screen, game_state):
    for i, p in enumerate(game_state['players1']):
        color = PLAYER1_COLOR
        border = (255, 255, 255)
        if game_state['current_player'] == 1 and i == game_state['selected_player']:
            border = (255, 255, 0)
            pygame.draw.circle(screen, (255, 255, 0), (field_x(int(p["x"])), field_y(int(p["y"]))), PLAYER_RADIUS + 7, 3)
        pygame.draw.circle(screen, color, (field_x(int(p["x"])), field_y(int(p["y"]))), PLAYER_RADIUS)
        pygame.draw.circle(screen, border, (field_x(int(p["x"])), field_y(int(p["y"]))), PLAYER_RADIUS, 2)
        num_text = font_small.render(str(p['num']), True, (255, 255, 255))
        screen.blit(num_text, (field_x(int(p["x"])) - num_text.get_width() // 2, field_y(int(p["y"])) - num_text.get_height() // 2))
    for i, p in enumerate(game_state['players2']):
        color = PLAYER2_COLOR
        border = (255, 255, 255)
        if game_state['current_player'] == 2 and i == game_state['selected_player']:
            border = (255, 255, 0)
            pygame.draw.circle(screen, (255, 255, 0), (field_x(int(p["x"])), field_y(int(p["y"]))), PLAYER_RADIUS + 7, 3)
        pygame.draw.circle(screen, color, (field_x(int(p["x"])), field_y(int(p["y"]))), PLAYER_RADIUS)
        pygame.draw.circle(screen, border, (field_x(int(p["x"])), field_y(int(p["y"]))), PLAYER_RADIUS, 2)
        num_text = font_small.render(str(p['num']), True, (255, 255, 255))
        screen.blit(num_text, (field_x(int(p["x"])) - num_text.get_width() // 2, field_y(int(p["y"])) - num_text.get_height() // 2))
    ball = game_state['ball']
    draw_soccer_ball(screen, (ball["x"], ball["y"]), BALL_RADIUS)

def draw_scoreboard(screen, game_state):
    sw, sh = 220, 80
    scoreboard_rect = pygame.Rect((PANEL_WIDTH - sw) // 2, 25, sw, sh)
    pygame.draw.rect(screen, SCOREBOARD_BG, scoreboard_rect, border_radius=18)
    pygame.draw.rect(screen, SCOREBOARD_BORDER, scoreboard_rect, 4, border_radius=18)
    for i, score in enumerate([game_state['score']['player1'], game_state['score']['player2']]):
        color = PLAYER1_COLOR if i == 0 else PLAYER2_COLOR
        pygame.draw.circle(screen, color, (scoreboard_rect.left + 60 + i * 100, scoreboard_rect.centery), 31)
        pygame.draw.circle(screen, (255, 255, 255), (scoreboard_rect.left + 60 + i * 100, scoreboard_rect.centery), 28, 4)
        num_text = font_large.render(str(score), True, (255, 255, 255))
        screen.blit(num_text, (scoreboard_rect.left + 60 + i * 100 - num_text.get_width() // 2, scoreboard_rect.centery - num_text.get_height() // 2))

def draw_ui(screen, game_state):
    ui_surface = pygame.Surface((PANEL_WIDTH, 70), pygame.SRCALPHA)
    ui_surface.fill(UI_BACKGROUND)
    screen.blit(ui_surface, (0, 0))
    draw_scoreboard(screen, game_state)
    player_color = PLAYER1_COLOR if game_state['current_player'] == 1 else PLAYER2_COLOR
    player_text = font_small.render(f"Current Player: {'Blue' if game_state['current_player'] == 1 else 'Red'}", True, player_color)
    screen.blit(player_text, (30, 25))
    if game_state['game_state'] == "aiming":
        status_text = font_small.render(
            "Click to select your player | Arrow keys to move | Space to charge/shoot", True, (200, 200, 100))
        screen.blit(status_text, (PANEL_WIDTH - status_text.get_width() - 30, 25))
        bar_w, bar_h = 320, 32
        bar_x = PANEL_WIDTH // 2 - bar_w // 2
        bar_y = PANEL_HEIGHT - 70
        pygame.draw.rect(screen, (70, 70, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
        power_ratio = min(1.0, game_state['shot_power'] / MAX_SHOT_POWER)
        grad_colors = [(70, 255, 70), (255, 215, 0), (255, 80, 80)]
        def grad_col(ratio):
            if ratio < 0.5:
                c1, c2 = grad_colors[0], grad_colors[1]
                f = ratio / 0.5
            else:
                c1, c2 = grad_colors[1], grad_colors[2]
                f = (ratio - 0.5) / 0.5
            return tuple(int(c1[i] + (c2[i] - c1[i]) * f) for i in range(3))
        fill_len = int((bar_w - 10) * power_ratio)
        if fill_len > 0:
            for i in range(fill_len):
                color = grad_col(i / (bar_w - 10))
                pygame.draw.rect(screen, color, (bar_x + 5 + i, bar_y + 5, 1, bar_h - 10), border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), 3, border_radius=10)
        power_text = font_small.render(f"Power: {int(game_state['shot_power'])}", True, (200, 200, 100))
        screen.blit(power_text, (PANEL_WIDTH // 2 - power_text.get_width() // 2, bar_y - 28))

def check_goal(game_state):
    ball = game_state['ball']
    if ball["x"] - BALL_RADIUS < 30 and HEIGHT // 2 - GOAL_WIDTH // 2 < ball["y"] < HEIGHT // 2 + GOAL_WIDTH // 2:
        game_state['game_state'] = "scored"
        game_state['winner'] = 2
        game_state['score']["player2"] += 1
        return True
    if ball["x"] + BALL_RADIUS > WIDTH - 30 and HEIGHT // 2 - GOAL_WIDTH // 2 < ball["y"] < HEIGHT // 2 + GOAL_WIDTH // 2:
        game_state['game_state'] = "scored"
        game_state['winner'] = 1
        game_state['score']["player1"] += 1
        return True
    return False

def move_ball(game_state):
    ball = game_state['ball']
    ball["x"] += ball["vx"]
    ball["y"] += ball["vy"]
    ball["vx"] *= FRICTION
    ball["vy"] *= FRICTION
    if abs(ball["vx"]) < 0.1 and abs(ball["vy"]) < 0.1:
        ball["vx"] = ball["vy"] = 0
        return True
    return False

def handle_collisions(game_state):
    ball = game_state['ball']
    for player in game_state['players1'] + game_state['players2']:
        dx = ball["x"] - player["x"]
        dy = ball["y"] - player["y"]
        dist = math.hypot(dx, dy)
        if dist < PLAYER_RADIUS + BALL_RADIUS:
            angle = math.atan2(dy, dx)
            overlap = PLAYER_RADIUS + BALL_RADIUS - dist + 1
            ball["x"] += math.cos(angle) * overlap
            ball["y"] += math.sin(angle) * overlap
            speed = math.hypot(ball["vx"], ball["vy"]) * 0.9 + 2.0
            ball["vx"] = speed * math.cos(angle)
            ball["vy"] = speed * math.sin(angle)

def handle_boundary(game_state):
    ball = game_state['ball']
    in_left_goal = (
        ball["x"] < 50 + BALL_RADIUS and
        (HEIGHT // 2 - GOAL_WIDTH // 2 - BALL_RADIUS) < ball["y"] < (HEIGHT // 2 + GOAL_WIDTH // 2 + BALL_RADIUS)
    )
    in_right_goal = (
        ball["x"] > WIDTH - 50 - BALL_RADIUS and
        (HEIGHT // 2 - GOAL_WIDTH // 2 - BALL_RADIUS) < ball["y"] < (HEIGHT // 2 + GOAL_WIDTH // 2 + BALL_RADIUS)
    )
    if not (in_left_goal or in_right_goal):
        if ball["x"] < 50 + BALL_RADIUS:
            ball["x"] = 50 + BALL_RADIUS
            ball["vx"] = -ball["vx"] * 0.7
        elif ball["x"] > WIDTH - 50 - BALL_RADIUS:
            ball["x"] = WIDTH - 50 - BALL_RADIUS
            ball["vx"] = -ball["vx"] * 0.7
    if ball["y"] < 50 + BALL_RADIUS:
        ball["y"] = 50 + BALL_RADIUS
        ball["vy"] = -ball["vy"] * 0.7
    elif ball["y"] > HEIGHT - 50 - BALL_RADIUS:
        ball["y"] = HEIGHT - 50 - BALL_RADIUS
        ball["vy"] = -ball["vy"] * 0.7

def get_current_team(game_state):
    return game_state['players1'] if game_state['current_player'] == 1 else game_state['players2']

def draw_cool_sharp_button(surf, rect, label, selected=False, hover=False):
    x, y, w, h = rect
    points = [
        (x + 16, y),
        (x + w - 16, y),
        (x + w, y + h // 2),
        (x + w - 16, y + h),
        (x + 16, y + h),
        (x, y + h // 2)
    ]
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        col = (
            int(60 + 120 * i / h),
            int(120 + 100 * i / h),
            255 if hover or selected else 180 + int(40 * i / h),
            210 if hover else 190
        )
        pygame.draw.line(grad, col, (0, i), (w, i))
    pygame.draw.polygon(surf, (0, 0, 0, 0), points)
    surf.blit(grad, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
    border_col = MENU_ACCENT if selected else MENU_ACCENT2 if hover else (160, 160, 255)
    pygame.draw.polygon(surf, border_col, points, 4 if (selected or hover) else 2)
    for glow in range(10, 0, -3):
        glow_alpha = 24 if (hover or selected) else 10
        pygame.draw.polygon(surf, border_col + (glow_alpha,), [(px, py) for px, py in points], glow)
    txt = font_medium.render(label, True, MENU_TEXT)
    surf.blit(txt, (x + w // 2 - txt.get_width() // 2, y + h // 2 - txt.get_height() // 2))

def menu_screen():
    try:
        menu_bg = pygame.image.load("background.jpg").convert()
        menu_bg = pygame.transform.scale(menu_bg, (PANEL_WIDTH, PANEL_HEIGHT))
    except Exception as e:
        menu_bg = None
        print("Menu background image not found or failed to load:", e)
    menu_items = [
        {"label": "Player vs Player", "action": "pvp"},
        {"label": "Player vs AI", "action": "vs_ai"},
        {"label": "History", "action": "history"},
        {"label": "Quit", "action": "quit"},
    ]
    selected = 0
    viewing_history = False
    history_lines = []
    while True:
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
            overlay = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((30, 40, 60, 80))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((25, 25, 40))
        title_str = "Soccer Collision"
        for i in range(14, 0, -2):
            col = (MENU_ACCENT2[0], MENU_ACCENT2[1], 255, 20 + i * 3)
            glow = font_glow.render(title_str, True, col)
            screen.blit(glow, (PANEL_WIDTH // 2 - glow.get_width() // 2, 120 + i))
        title_text = font_menu_title.render(title_str, True, (255, 255, 255))
        screen.blit(title_text, (PANEL_WIDTH // 2 - title_text.get_width() // 2, 120))
        if not viewing_history:
            btn_w, btn_h = 340, 80
            btn_margin = 50
            start_y = PANEL_HEIGHT // 2 - (len(menu_items) * (btn_h + btn_margin)) // 2 + 60
            mouse_x, mouse_y = pygame.mouse.get_pos()
            hover_idx = -1
            for i, item in enumerate(menu_items):
                bx = PANEL_WIDTH // 2 - btn_w // 2
                by = start_y + i * (btn_h + btn_margin)
                rect = pygame.Rect(bx, by, btn_w, btn_h)
                is_hover = rect.collidepoint(mouse_x, mouse_y)
                if is_hover: hover_idx = i
                draw_cool_sharp_button(screen, rect, item["label"], selected=(i == selected), hover=is_hover)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(menu_items)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(menu_items)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        action = menu_items[selected]["action"]
                        if action == "history":
                            viewing_history = True
                            history_lines = load_history()
                        else:
                            return action
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, item in enumerate(menu_items):
                        bx = PANEL_WIDTH // 2 - btn_w // 2
                        by = start_y + i * (btn_h + btn_margin)
                        rect = pygame.Rect(bx, by, btn_w, btn_h)
                        if rect.collidepoint(mouse_x, mouse_y):
                            if item["action"] == "history":
                                viewing_history = True
                                history_lines = load_history()
                            else:
                                return item["action"]
            if hover_idx != -1:
                selected = hover_idx
        else:
            box_w, box_h = 550, 420
            box_x = PANEL_WIDTH // 2 - box_w // 2
            box_y = PANEL_HEIGHT // 2 - box_h // 2 + 10
            pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_w, box_h), border_radius=18)
            pygame.draw.rect(screen, (170, 170, 200), (box_x, box_y, box_w, box_h), 4, border_radius=18)
            title = font_medium.render("History", True, MENU_TEXT)
            screen.blit(title, (PANEL_WIDTH // 2 - title.get_width() // 2, box_y + 20))
            if history_lines:
                for idx, line in enumerate(history_lines[:15]):
                    txt = font_small.render(f"{line}", True, MENU_TEXT)
                    screen.blit(txt, (box_x + 34, box_y + 70 + idx * 24))
            else:
                txt = font_small.render("No record yet.", True, MENU_TEXT)
                screen.blit(txt, (box_x + box_w // 2 - txt.get_width() // 2, box_y + box_h // 2))
            tip = font_small.render("Press ESC to return", True, (150, 150, 180))
            screen.blit(tip, (box_x + box_w // 2 - tip.get_width() // 2, box_y + box_h - 40))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        viewing_history = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    viewing_history = False
        pygame.display.flip()

def ai_choose_player_and_move(game_state, team_idx):
    team = game_state['players1'] if team_idx == 1 else game_state['players2']
    ball = game_state['ball']
    dists = [math.hypot(ball['x'] - p['x'], ball['y'] - p['y']) for p in team]
    min_i = dists.index(min(dists))
    game_state['selected_player'] = min_i
    cur_player = team[min_i]
    dx, dy = ball['x'] - cur_player['x'], ball['y'] - cur_player['y']
    dist = math.hypot(dx, dy)
    move_speed = PLAYER_SPEED
    if dist > 40:
        move_x = move_speed * dx / dist
        move_y = move_speed * dy / dist
        cur_player['x'] += move_x
        cur_player['y'] += move_y
        cur_player['x'] = max(60, min(WIDTH - 60, cur_player['x']))
        cur_player['y'] = max(60, min(HEIGHT - 60, cur_player['y']))
        return False
    else:
        return True

def ai_charge_and_shoot(game_state, team_idx):
    team = game_state['players1'] if team_idx == 1 else game_state['players2']
    cur_player = team[game_state['selected_player']]
    ball = game_state['ball']
    dx, dy = ball['x'] - cur_player['x'], ball['y'] - cur_player['y']
    dist = math.hypot(dx, dy)
    if dist < 150:
        angle = math.atan2(dy, dx)
        if team_idx == 1:
            tx, ty = WIDTH - 20, HEIGHT // 2 + random.randint(-40, 40)
        else:
            tx, ty = 20, HEIGHT // 2 + random.randint(-40, 40)
        tdx, tdy = tx - ball['x'], ty - ball['y']
        tdist = math.hypot(tdx, tdy)
        if tdist > 0:
            tdx, tdy = tdx / tdist, tdy / tdist
        else:
            tdx, tdy = math.cos(angle), math.sin(angle)
        shot_power = random.uniform(10, 15)
        game_state['ball']["vx"] = tdx * shot_power * 1.5
        game_state['ball']["vy"] = tdy * shot_power * 1.5
        game_state['game_state'] = "moving"
        for pl in game_state['players1']:
            pl["active"] = False
        for pl in game_state['players2']:
            pl["active"] = False
        game_state['shot_power'] = 0
        return True
    return False

def main():
    clock = pygame.time.Clock()
    power_speed = 0.25
    game_state = init_game()
    in_menu = True
    mode = "pvp"
    try:
        soccer_bg = pygame.image.load("Soccer.jpg").convert()
        soccer_bg = pygame.transform.scale(soccer_bg, (PANEL_WIDTH, PANEL_HEIGHT))
    except Exception as e:
        soccer_bg = None
        print("Game background image not found or failed to load:", e)

    while True:
        if in_menu:
            menu_action = menu_screen()
            if menu_action == "pvp":
                mode = "pvp"
                game_state = init_game()
                in_menu = False
            elif menu_action == "vs_ai":
                mode = "vs_ai"
                game_state = init_game()
                in_menu = False
            elif menu_action == "history":
                continue
            elif menu_action == "quit":
                pygame.quit()
                sys.exit()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game_state = init_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                in_menu = True
                break
            if game_state['game_state'] == "scored" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                save_history(game_state['score']["player1"], game_state['score']["player2"], mode="PvP" if mode == "pvp" else "PvE")
                reset_positions(game_state)
                game_state['current_player'] = 2 if game_state['winner'] == 1 else 1
                game_state['game_state'] = "aiming"
                game_state['winner'] = None

            if mode == "vs_ai":
                human_player = 1
                ai_player = 2
            else:
                human_player = 1
                ai_player = -1

            if game_state['game_state'] == "aiming":
                if mode == "vs_ai" and game_state['current_player'] == 2:
                    # 事件内不处理AI逻辑
                    pass
                else:
                    # 玩家操作
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        mx_field = mx - FIELD_MARGIN_X
                        my_field = my - FIELD_MARGIN_Y
                        team = get_current_team(game_state)
                        for i, p in enumerate(team):
                            if math.hypot(mx_field - p["x"], my_field - p["y"]) < PLAYER_RADIUS + 6:
                                game_state['selected_player'] = i
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not game_state['charging_power']:
                        game_state['charging_power'] = True
                        game_state['shot_power'] = 0
                    if event.type == pygame.KEYUP and event.key == pygame.K_SPACE and game_state['charging_power']:
                        game_state['charging_power'] = False
                        team = get_current_team(game_state)
                        cur_player = team[game_state['selected_player']]
                        dx = game_state['ball']["x"] - cur_player["x"]
                        dy = game_state['ball']["y"] - cur_player["y"]
                        dist = math.hypot(dx, dy)
                        if dist < 150 and game_state['shot_power'] > 0:
                            dx /= dist
                            dy /= dist
                            game_state['ball']["vx"] = dx * game_state['shot_power'] * 1.5
                            game_state['ball']["vy"] = dy * game_state['shot_power'] * 1.5
                            game_state['game_state'] = "moving"
                            for pl in game_state['players1']:
                                pl["active"] = False
                            for pl in game_state['players2']:
                                pl["active"] = False
                        game_state['shot_power'] = 0

        if in_menu:
            continue

        keys = pygame.key.get_pressed()
        # --- AI逻辑每帧执行，不卡顿 ---
        if game_state['game_state'] == "aiming":
            if mode == "vs_ai" and game_state['current_player'] == 2:
                ready = ai_choose_player_and_move(game_state, 2)
                if ready:
                    ai_charge_and_shoot(game_state, 2)
            else:
                cur_player = get_current_team(game_state)[game_state['selected_player']]
                cur_player["active"] = True
                speed = PLAYER_SPEED * (0.7 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1)
                if keys[pygame.K_LEFT] and cur_player["x"] > 60:
                    cur_player["x"] -= speed
                if keys[pygame.K_RIGHT] and cur_player["x"] < WIDTH - 60:
                    cur_player["x"] += speed
                if keys[pygame.K_UP] and cur_player["y"] > 60:
                    cur_player["y"] -= speed
                if keys[pygame.K_DOWN] and cur_player["y"] < HEIGHT - 60:
                    cur_player["y"] += speed
                if game_state['charging_power']:
                    game_state['shot_power'] += power_speed
                    if game_state['shot_power'] > MAX_SHOT_POWER:
                        game_state['shot_power'] = MAX_SHOT_POWER
        elif game_state['game_state'] == "moving":
            ball_stopped = move_ball(game_state)
            handle_collisions(game_state)
            handle_boundary(game_state)
            scored = check_goal(game_state)
            if ball_stopped and not scored:
                game_state['current_player'] = 2 if game_state['current_player'] == 1 else 1
                game_state['game_state'] = "aiming"
                game_state['shot_power'] = 0
                game_state['charging_power'] = False
                for pl in game_state['players1']:
                    pl["active"] = False
                for pl in game_state['players2']:
                    pl["active"] = False

        if soccer_bg:
            screen.blit(soccer_bg, (0, 0))
            overlay = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((40, 60, 40, 70))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((55, 85, 45))
        draw_track(screen)
        field_surface = pygame.Surface((WIDTH, HEIGHT))
        field_surface.fill(BACKGROUND)
        screen.blit(field_surface, (FIELD_MARGIN_X, FIELD_MARGIN_Y))
        draw_field(screen)
        draw_players(screen, game_state)
        draw_ui(screen, game_state)
        instructions = [
            "Instructions:",
            "Click on your player to select (when playing).",
            "Arrow keys - Move selected player",
            "Space - Charge/Shoot (release to shoot)",
            "Shift - Slow move",
            "R - Restart",
            "ESC - Back to Menu"
        ]
        for i, text in enumerate(instructions):
            instr = font_small.render(text, True, (200, 200, 200))
            screen.blit(instr, (30, PANEL_HEIGHT - 210 + i * 28))
        if game_state['game_state'] == "scored":
            overlay = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            goal_text = font_large.render(f"Player {game_state['winner']} Scores!", True,
                                          PLAYER1_COLOR if game_state['winner'] == 1 else PLAYER2_COLOR)
            screen.blit(goal_text, (PANEL_WIDTH // 2 - goal_text.get_width() // 2, PANEL_HEIGHT // 2 - 50))
            score_text = font_medium.render(
                f"Now: {game_state['score']['player1']} - {game_state['score']['player2']}",
                True, (255, 255, 200))
            screen.blit(score_text, (PANEL_WIDTH // 2 - score_text.get_width() // 2, PANEL_HEIGHT // 2 + 20))
            continue_text = font_medium.render("Press Space to continue", True, (200, 200, 100))
            screen.blit(continue_text, (PANEL_WIDTH // 2 - continue_text.get_width() // 2, PANEL_HEIGHT // 2 + 80))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()