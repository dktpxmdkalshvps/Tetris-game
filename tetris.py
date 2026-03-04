import pygame
import random
import sys
import math

# ── 1. CONSTANTS  ──────────────────────────────────────────
COLS, ROWS  = 10, 20
CELL        = 30
PANEL_W     = 180
BOARD_X     = PANEL_W
BOARD_W     = COLS * CELL
BOARD_H     = ROWS * CELL
WIN_W       = PANEL_W + BOARD_W + PANEL_W
WIN_H       = BOARD_H + 60
BOARD_Y     = 40
FPS         = 60

# --- 컬러 팔레트 (HEX to RGB) ---
ABYSSAL_BASE  = (9, 17, 43)    # #09112b
OCEAN_DEPTH   = (28, 51, 111)  # #1c336f
WAVES_FOAM    = (219, 232, 243)# #dbe8f3
MUTED_CURRENT = (88, 115, 163) # #5873a3
SEA_FOG       = (176, 189, 214)# #b0bdd6
BLACK_PEARL   = (0, 1, 4)      # #000104

BG          = ABYSSAL_BASE
BG2         = BLACK_PEARL
BORDER      = OCEAN_DEPTH
GRID        = (20, 35, 75)     # 격자는 더 어둡게
TEXT_DIM    = MUTED_CURRENT
TEXT_BRIGHT = WAVES_FOAM
WHITE       = (255, 255, 255)

#  테마 블록 색상 (필드별로 미묘하게 다른 파란색/청록색 계열)
COLORS = {
    "I": ((0, 245, 255), WAVES_FOAM, (0, 120, 140)),    # 발광 시안
    "O": ((255, 230, 0), (255, 255, 150), (140, 120, 0)), # 노랑
    "T": ((120, 100, 255), (180, 150, 255), (60, 30, 160)), # 보라빛 조류
    "S": ((0, 255, 136), (150, 255, 200), (0, 140, 70)),  # 초록
    "Z": ((255, 58, 92), (255, 150, 170), (140, 10, 40)),  # 빨강
    "J": ((40, 80, 255), (120, 150, 255), (10, 30, 150)),  # 깊은 바다 파랑
    "L": ((255, 140, 0), (255, 200, 100), (150, 70, 0)),   # 주황
}

SHAPES = {
    "I": [[1,1,1,1]],
    "O": [[1,1],[1,1]],
    "T": [[0,1,0],[1,1,1]],
    "S": [[0,1,1],[1,1,0]],
    "Z": [[1,1,0],[0,1,1]],
    "J": [[1,0,0],[1,1,1]],
    "L": [[0,0,1],[1,1,1]],
}

LINE_SCORES = [0, 100, 300, 500, 800]
LINE_NAMES  = ["", "SINGLE", "DOUBLE", "TRIPLE", "TETRIS!"]
CLEAR_MS    = 300

# ── 2. HELPERS ────────────────────────────────────────────────────────────────
def rotate_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]

def new_piece(key=None):
    k = key or random.choice(list(SHAPES.keys()))
    shape = [row[:] for row in SHAPES[k]]
    x = COLS // 2 - len(shape[0]) // 2
    return {"key": k, "shape": shape, "x": x, "y": 0}

def is_valid(board, shape, x, y):
    for r, row in enumerate(shape):
        for c, cell in enumerate(row):
            if not cell: continue
            nr, nc = r + y, c + x
            if nr < 0 or nr >= ROWS or nc < 0 or nc >= COLS: return False
            if board[nr][nc]: return False
    return True

def lock_piece(board, piece):
    b = [row[:] for row in board]
    for r, row in enumerate(piece["shape"]):
        for c, cell in enumerate(row):
            if cell:
                if 0 <= piece["y"]+r < ROWS and 0 <= piece["x"]+c < COLS:
                    b[piece["y"]+r][piece["x"]+c] = piece["key"]
    return b

def find_full_rows(board):
    return [i for i, row in enumerate(board) if all(row)]

def remove_lines(board, rows):
    kept = [row for i, row in enumerate(board) if i not in rows]
    empty = [[None]*COLS for _ in rows]
    return empty + kept

def get_ghost(board, piece):
    g = dict(piece, shape=[r[:] for r in piece["shape"]])
    while is_valid(board, g["shape"], g["x"], g["y"]+1):
        g["y"] += 1
    return g

def create_board():
    return [[None]*COLS for _ in range(ROWS)]

# ── 3. DRAWING PRIMITIVES ─────────────────────────────────────────────────────
def draw_cell(surf, x, y, key, ghost=False):
    px, py = BOARD_X + x * CELL, BOARD_Y + y * CELL
    s = CELL
    fill, hi, sh = COLORS[key]

    if ghost:
        r = pygame.Rect(px+2, py+2, s-4, s-4)
        surf_ghost = pygame.Surface((s-4, s-4), pygame.SRCALPHA)
        pygame.draw.rect(surf_ghost, (*fill, 40), surf_ghost.get_rect(), border_radius=2)
        pygame.draw.rect(surf_ghost, (*fill, 80), surf_ghost.get_rect(), width=1, border_radius=2)
        surf.blit(surf_ghost, r.topleft)
        return

    pygame.draw.rect(surf, fill, (px+1, py+1, s-2, s-2), border_radius=2)
    pygame.draw.rect(surf, hi, (px+2, py+2, s-4, max(1, int(s*0.25))), border_radius=1)
    pygame.draw.rect(surf, sh, (px+2, py+s-int(s*0.18)-1, s-4, int(s*0.18)), border_radius=1)

def draw_mini_cell(surf, px, py, key, size=20):
    fill, hi, _ = COLORS[key]
    pygame.draw.rect(surf, fill, (px, py, size, size), border_radius=2)
    pygame.draw.rect(surf, hi, (px+1, py+1, size-2, 4), border_radius=1)

def draw_panel_box(surf, rx, ry, rw, rh, label, accent=None):
    col = accent if accent else BORDER
    pygame.draw.rect(surf, BG2, (rx, ry, rw, rh), border_radius=6)
    pygame.draw.rect(surf, col, (rx, ry, rw, rh), width=1, border_radius=6)
    if label:
        font_xs = pygame.font.SysFont("Courier New", 10, bold=True)
        lbl = font_xs.render(label, True, TEXT_DIM)
        surf.blit(lbl, (rx+12, ry+8))

def draw_text(surf, text, x, y, font, color, align="left"):
    t = font.render(str(text), True, color)
    if align == "center": x -= t.get_width() // 2
    elif align == "right": x -= t.get_width()
    surf.blit(t, (x, y))

def glow_text(surf, text, x, y, font, color, strength=5, align="left"):
    """텍스트 주변에 은은한 그림자/발광 효과를 줍니다."""
    t = font.render(str(text), True, color)
    if align == "center": x -= t.get_width() // 2
    elif align == "right": x -= t.get_width()
    
    # 그림자/발광 효과 (상하좌우로 살짝만 겹침)
    # RGBA를 지원하도록 설정하여 부드럽게 번지게 합니다.
    shadow_color = (*color[:3], 100) # 불투명도 조절
    for dx, dy in [(-1, -1), (1, 1), (-1, 1), (1, -1)]:
        gs = font.render(str(text), True, shadow_color)
        surf.blit(gs, (x + dx, y + dy))
        
    surf.blit(t, (x, y))

# ── 4. GAME STATE ──────────────────────────────────────────
class Game:
    def __init__(self):
        self.hi_score = 0
        self.reset()

    def reset(self):
        self.board = create_board()
        self.current = new_piece()
        self.next = new_piece()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.combo = 0
        self.game_over = False
        self.paused = False
        self.gravity_acc = 0
        self.clearing_rows = []
        self.clear_timer = 0
        self.clear_flash = False
        self.popups = []
        self.das_dir = 0
        self.das_timer = 0
        self.das_delay = 170
        self.das_repeat = 50

    def gravity_delay(self):
        return max(80, 800 - (self.level - 1) * 75)

    def try_move(self, dx=0, dy=0):
        if is_valid(self.board, self.current["shape"], self.current["x"]+dx, self.current["y"]+dy):
            self.current["x"] += dx; self.current["y"] += dy
            return True
        return False

    def try_rotate(self):
        rot = rotate_cw(self.current["shape"])
        for dx in [0, -1, 1, -2, 2]:
            if is_valid(self.board, rot, self.current["x"]+dx, self.current["y"]):
                self.current["shape"] = rot; self.current["x"] += dx
                return

    def settle(self):
        self.board = lock_piece(self.board, self.current)
        full = find_full_rows(self.board)
        if full:
            self.clearing_rows = full
            self.clear_timer = CLEAR_MS
            self.clear_flash = True
        else:
            self._spawn_next()

    def finish_clear(self):
        count = len(self.clearing_rows)
        self.board = remove_lines(self.board, self.clearing_rows)
        self.clearing_rows = []
        self.lines += count
        self.level = self.lines // 10 + 1
        self.combo += 1
        self.score += LINE_SCORES[count] * self.combo
        self.hi_score = max(self.hi_score, self.score)
        
        # 팝업 생성
        self.popups.append({
            "text": f"{LINE_NAMES[count]} x{self.combo}",
            "x": BOARD_X + BOARD_W//2, "y": BOARD_Y + 300,
            "life": 1000, "color": WAVES_FOAM
        })
        self._spawn_next()

    def _spawn_next(self):
        self.current = self.next
        self.next = new_piece()
        self.combo = 0 if not self.clearing_rows else self.combo
        if not is_valid(self.board, self.current["shape"], self.current["x"], self.current["y"]):
            self.game_over = True

    def update(self, dt_ms):
        if self.game_over or self.paused: return
        if self.clearing_rows:
            self.clear_timer -= dt_ms
            if self.clear_timer <= CLEAR_MS // 2: self.clear_flash = False
            if self.clear_timer <= 0: self.finish_clear()
            return

        self.gravity_acc += dt_ms
        if self.gravity_acc >= self.gravity_delay():
            self.gravity_acc = 0
            if not self.try_move(dy=1): self.settle()

        if self.das_dir != 0:
            self.das_timer -= dt_ms
            if self.das_timer <= 0:
                self.das_timer = self.das_repeat
                self.try_move(dx=self.das_dir)

        for p in self.popups:
            p["life"] -= dt_ms
            p["y"] -= 0.5
        self.popups = [p for p in self.popups if p["life"] > 0]

    def handle_keydown(self, key):
        if self.paused:
            if key == pygame.K_ESCAPE:
                self.paused = False
            return

        if self.game_over:
            return

        if key == pygame.K_LEFT:
            self.try_move(dx=-1)
            self.das_dir = -1
            self.das_timer = self.das_delay
        elif key == pygame.K_RIGHT:
            self.try_move(dx=1)
            self.das_dir = 1
            self.das_timer = self.das_delay
        elif key in (pygame.K_UP, pygame.K_z):
            self.try_rotate()
        elif key == pygame.K_DOWN:
            self.try_move(dy=1)
            self.gravity_acc = 0
        elif key == pygame.K_SPACE:
            while self.try_move(dy=1): pass
            self.settle()
        elif key == pygame.K_ESCAPE:
            self.paused = True

    def handle_keyup(self, key):
        if key == pygame.K_LEFT and self.das_dir == -1:
            self.das_dir = 0
            self.das_timer = 0
        elif key == pygame.K_RIGHT and self.das_dir == 1:
            self.das_dir = 0
            self.das_timer = 0


# ── 5. RENDERER  ──────────────────────────────────────────────
class Renderer:
    def __init__(self):
        pygame.font.init()
        self.f_big = pygame.font.SysFont("monospace", 28, bold=True)
        self.f_med = pygame.font.SysFont("monospace", 18, bold=True)
        self.f_sm  = pygame.font.SysFont("monospace", 13, bold=True)
        self.t = 0

    def draw(self, surf, game, dt):
        self.t += dt
        surf.fill(BG)
        
        # 보드 배경 
        pygame.draw.rect(surf, (15, 25, 55), (BOARD_X, BOARD_Y, BOARD_W, BOARD_H))

        # 그리드
        for r in range(ROWS + 1):
            pygame.draw.line(surf, GRID, (BOARD_X, BOARD_Y + r*CELL), (BOARD_X+BOARD_W, BOARD_Y + r*CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surf, GRID, (BOARD_X + c*CELL, BOARD_Y), (BOARD_X + c*CELL, BOARD_Y+BOARD_H))

        # 고정 블록
        for r, row in enumerate(game.board):
            for c, key in enumerate(row):
                if key:
                    if r in game.clearing_rows and game.clear_flash:
                        pygame.draw.rect(surf, WHITE, (BOARD_X+c*CELL+1, BOARD_Y+r*CELL+1, CELL-2, CELL-2))
                    else:
                        draw_cell(surf, c, r, key)

        # 고스트 & 현재 블록
        if not game.game_over and not game.clearing_rows:
            ghost = get_ghost(game.board, game.current)
            for r, row in enumerate(ghost["shape"]):
                for c, val in enumerate(row):
                    if val: draw_cell(surf, ghost["x"]+c, ghost["y"]+r, game.current["key"], ghost=True)
            for r, row in enumerate(game.current["shape"]):
                for c, val in enumerate(row):
                    if val: draw_cell(surf, game.current["x"]+c, game.current["y"]+r, game.current["key"])

        self._draw_panels(surf, game)
        if game.game_over: self._draw_overlay(surf, "GAME OVER", game.score)
        elif game.paused: self._draw_overlay(surf, "PAUSED")

    def _draw_panels(self, surf, game):
        # 왼쪽 패널
        lx = 15
        draw_panel_box(surf, lx, BOARD_Y, PANEL_W-30, 60, "HI-SCORE")
        draw_text(surf, f"{game.hi_score:07d}", lx+15, BOARD_Y+25, self.f_med, WAVES_FOAM)

        draw_panel_box(surf, lx, BOARD_Y+75, PANEL_W-30, 60, "SCORE")
        glow_text(surf, f"{game.score:07d}", lx+15, BOARD_Y+100, self.f_med, (0, 245, 255))

        draw_panel_box(surf, lx, BOARD_Y+150, PANEL_W-30, 180, "CONTROLS")
        ctrls = [("←→", "MOVE"), ("↑/Z", "ROT"), ("↓", "DROP"), ("SPC", "HARD"), ("ESC", "PAUSE")]
        for i, (k, v) in enumerate(ctrls):
            draw_text(surf, k, lx+15, BOARD_Y+180+i*25, self.f_sm, MUTED_CURRENT)
            draw_text(surf, v, lx+PANEL_W-45, BOARD_Y+180+i*25, self.f_sm, MUTED_CURRENT, align="right")

        # 오른쪽 패널
        rx = BOARD_X + BOARD_W + 15
        draw_panel_box(surf, rx, BOARD_Y, PANEL_W-30, 100, "NEXT")
        if game.next:
            shape = game.next["shape"]
            for r, row in enumerate(shape):
                for c, val in enumerate(row):
                    if val: draw_mini_cell(surf, rx+40+c*20, BOARD_Y+40+r*20, game.next["key"])

        draw_panel_box(surf, rx, BOARD_Y+115, PANEL_W-30, 60, "LEVEL")
        draw_text(surf, f"Lv. {game.level:02d}", rx+15, BOARD_Y+140, self.f_med, (0, 255, 136))

        draw_panel_box(surf, rx, BOARD_Y+190, PANEL_W-30, 60, "LINES")
        draw_text(surf, f"{game.lines:04d}", rx+15, BOARD_Y+215, self.f_med, SEA_FOG)

    def _draw_overlay(self, surf, msg, score=None):
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((0, 1, 4, 200)) # Black Pearl shadow
        surf.blit(overlay, (BOARD_X, BOARD_Y))
        glow_text(surf, msg, BOARD_X+BOARD_W//2, BOARD_Y+250, self.f_big, WAVES_FOAM, align="center")
        if score is not None:
            draw_text(surf, f"SCORE: {score}", BOARD_X+BOARD_W//2, BOARD_Y+300, self.f_med, SEA_FOG, align="center")

# ── 6. MAIN LOOP ──────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Abyssal Tetris - Marine Edition")
    clock = pygame.time.Clock()
    game = Game()
    renderer = Renderer()

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over: game.reset()
                else: game.handle_keydown(event.key)
            if event.type == pygame.KEYUP: game.handle_keyup(event.key)

        game.update(dt)
        renderer.draw(screen, game, dt)
        pygame.display.flip()

if __name__ == "__main__":
    main()