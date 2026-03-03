import pygame
import random

# 1. 데이터 및 상수 정의 (Constants)
# --- 화면 설정 ---
CELL_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
SIDE_PANEL_WIDTH = 200
SCREEN_WIDTH = BOARD_WIDTH * CELL_SIZE + SIDE_PANEL_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT * CELL_SIZE
FPS = 60

# --- 블록 모양 (Tetrominoes) ---
TETROMINOES = {
    'I': [[1, 1, 1, 1]],
    'J': [[1, 0, 0], [1, 1, 1]],
    'L': [[0, 0, 1], [1, 1, 1]],
    'O': [[1, 1], [1, 1]],
    'S': [[0, 1, 1], [1, 1, 0]],
    'T': [[0, 1, 0], [1, 1, 1]],
    'Z': [[1, 1, 0], [0, 1, 1]]
}

# --- 색상 ---
COLORS = {
    'I': (0, 255, 255),   # Cyan
    'J': (0, 0, 255),     # Blue
    'L': (255, 165, 0),   # Orange
    'O': (255, 255, 0),   # Yellow
    'S': (0, 255, 0),     # Green
    'T': (128, 0, 128),   # Purple
    'Z': (255, 0, 0),     # Red
    'GRID': (50, 50, 50), # Grid lines
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255)
}

# 2. 핵심 클래스 설계 (OOP)

class Tetromino:
    """블록 하나하나의 설계도"""
    def __init__(self, x, y, shape_name):
        self.x = x
        self.y = y
        self.shape_name = shape_name
        self.shape = TETROMINOES[shape_name]
        self.color = COLORS[shape_name]
        self.rotation = 0

    def rotate(self):
        """블록을 90도 회전시킴."""
        # 행렬을 시계 방향으로 90도 회전
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

    def move(self, dx, dy):
        """블록을 좌우/아래로 이동."""
        self.x += dx
        self.y += dy

class Board:
    """게임판 관리"""
    def __init__(self):
        # 10x20 크기의 2차원 리스트(격자 데이터)
        self.grid = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

    def is_valid_move(self, piece):
        """블록이 벽에 부딪히거나 다른 블록과 겹치는지 확인(충돌 감지)."""
        for r_idx, row in enumerate(piece.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    # 보드 경계 확인
                    if not (0 <= piece.x + c_idx < BOARD_WIDTH):
                        return False
                    if not (0 <= piece.y + r_idx < BOARD_HEIGHT):
                        return False
                    # 다른 블록과 충돌 확인
                    if self.grid[piece.y + r_idx][piece.x + c_idx] != 0:
                        return False
        return True

    def lock_piece(self, piece):
        """바닥에 닿은 블록을 보드 데이터에 고정."""
        for r_idx, row in enumerate(piece.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + r_idx][piece.x + c_idx] = piece.shape_name
        
        return self.clear_lines()

    def clear_lines(self):
        """꽉 찬 가로줄을 찾아 지우고, 위쪽 블록들을 아래로 내림."""
        lines_to_clear = []
        for r_idx, row in enumerate(self.grid):
            if 0 not in row:
                lines_to_clear.append(r_idx)
        
        # 꽉 찬 줄 삭제 및 새로운 빈 줄 추가
        for r_idx in lines_to_clear:
            del self.grid[r_idx]
            self.grid.insert(0, [0 for _ in range(BOARD_WIDTH)])
            
        return len(lines_to_clear)

    def draw(self, surface):
        """고정된 블록들을 그림"""
        surface.fill(COLORS['BLACK']) # Draw background for the board area
        for r_idx, row in enumerate(self.grid):
            for c_idx, cell in enumerate(row):
                if cell != 0:
                    pygame.draw.rect(surface, COLORS[cell],
                                     (c_idx * CELL_SIZE, r_idx * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        # 그리드 라인 그리기
        for x in range(0, BOARD_WIDTH * CELL_SIZE, CELL_SIZE):
            pygame.draw.line(surface, COLORS['GRID'], (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(surface, COLORS['GRID'], (0, y), (BOARD_WIDTH * CELL_SIZE, y))


class Game:
    """전체 흐름 제어"""
    def __init__(self, surface, font):
        self.surface = surface
        self.font = font
        self.board = Board()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece() # 다음 블록
        self.gravity_timer = 0
        self.gravity_speed = 40 # 숫자가 작을수록 빠름 (프레임 기반)
        
        # 점수표 (1, 2, 3, 4줄 클리어)
        self.score_table = {1: 40, 2: 100, 3: 300, 4: 1200}

    def new_piece(self):
        """새로운 랜덤 블록 생성"""
        shape_name = random.choice(list(TETROMINOES.keys()))
        # 중앙 상단에서 시작
        start_x = BOARD_WIDTH // 2 - len(TETROMINOES[shape_name][0]) // 2
        return Tetromino(start_x, 0, shape_name)

    def process_cleared_lines(self, cleared_lines):
        if cleared_lines > 0:
            self.score += self.score_table[cleared_lines] * self.level
            self.lines_cleared += cleared_lines
            # 레벨업: 10줄마다
            if self.lines_cleared >= self.level * 10:
                self.level += 1
                self.gravity_speed = max(5, self.gravity_speed - 5) # 레벨업 시 속도 증가

    def lock_piece_and_get_next(self):
        """현재 블록을 고정하고, 점수를 처리한 뒤, 다음 블록을 가져옴"""
        cleared_lines = self.board.lock_piece(self.current_piece)
        self.process_cleared_lines(cleared_lines)
        
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        if not self.board.is_valid_move(self.current_piece):
            self.game_over = True

    def handle_input(self, event):
        """키보드 입력 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.current_piece.move(-1, 0)
                if not self.board.is_valid_move(self.current_piece):
                    self.current_piece.move(1, 0) # 원위치
            elif event.key == pygame.K_RIGHT:
                self.current_piece.move(1, 0)
                if not self.board.is_valid_move(self.current_piece):
                    self.current_piece.move(-1, 0)
            elif event.key == pygame.K_DOWN:
                 self.current_piece.move(0, 1)
                 if not self.board.is_valid_move(self.current_piece):
                    self.current_piece.move(0, -1)
            elif event.key == pygame.K_UP: # 회전
                self.current_piece.rotate()
                if not self.board.is_valid_move(self.current_piece):
                    # 회전이 불가능하면 3번 더 회전해서 원상태로
                    self.current_piece.rotate()
                    self.current_piece.rotate()
                    self.current_piece.rotate()
            elif event.key == pygame.K_SPACE: # 하드 드롭
                while self.board.is_valid_move(self.current_piece):
                    self.current_piece.move(0, 1)
                self.current_piece.move(0, -1) # 마지막 유효 위치로
                self.lock_piece_and_get_next()


    def update(self):
        """중력에 의해 블록을 아래로 한 칸씩 내림."""
        self.gravity_timer += 1
        if self.gravity_timer > self.gravity_speed:
            self.current_piece.move(0, 1)
            self.gravity_timer = 0
            if not self.board.is_valid_move(self.current_piece):
                self.current_piece.move(0, -1) # 마지막 유효 위치로
                self.lock_piece_and_get_next()

    def draw(self):
        """보드, 블록, 사이드 패널을 화면에 그림."""
        self.surface.fill(COLORS['BLACK'])
        
        # 게임 보드 그리기
        game_board_surface = self.surface.subsurface((0, 0, BOARD_WIDTH * CELL_SIZE, SCREEN_HEIGHT))
        self.board.draw(game_board_surface)

        # 현재 블록 그리기
        piece = self.current_piece
        for r_idx, row in enumerate(piece.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.surface, piece.color,
                                     ((piece.x + c_idx) * CELL_SIZE, 
                                      (piece.y + r_idx) * CELL_SIZE, 
                                      CELL_SIZE, CELL_SIZE))
        
        # 사이드 패널 그리기
        panel_x = BOARD_WIDTH * CELL_SIZE
        pygame.draw.rect(self.surface, COLORS['GRID'], (panel_x, 0, SIDE_PANEL_WIDTH, SCREEN_HEIGHT))

        # 다음 블록(Next Piece) 표시
        next_text = self.font.render("Next", True, COLORS['WHITE'])
        self.surface.blit(next_text, (panel_x + 40, 30))
        
        next_p = self.next_piece
        for r_idx, row in enumerate(next_p.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.surface, next_p.color, 
                                     (panel_x + 40 + c_idx * CELL_SIZE, 70 + r_idx * CELL_SIZE,
                                      CELL_SIZE, CELL_SIZE))

        # 점수(Score) 표시
        score_text = self.font.render(f"Score: {self.score}", True, COLORS['WHITE'])
        self.surface.blit(score_text, (panel_x + 40, 200))
        
        # 레벨(Level) 표시
        level_text = self.font.render(f"Level: {self.level}", True, COLORS['WHITE'])
        self.surface.blit(level_text, (panel_x + 40, 240))

        pygame.display.update()


def main():
    """메인 게임 함수"""
    pygame.init()
    pygame.font.init() # 폰트 모듈 초기화
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    
    # 폰트 설정
    font = pygame.font.SysFont('Consolas', 30)

    game = Game(screen, font)
    
    # 3. 주요 로직 프로세스 (Algorithm)
    running = True
    while running and not game.game_over:
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_input(event)

        # 게임 상태 업데이트
        game.update()
        
        # 화면 그리기
        game.draw()
        
        clock.tick(FPS)

    print("Game Over!")
    pygame.quit()

if __name__ == '__main__':
    main()
