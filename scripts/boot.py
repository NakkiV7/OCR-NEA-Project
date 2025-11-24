import pygame

#config
TILE_SIZE = 64
VIEW_COLS = 15
VIEW_ROWS = 11
SCREEN_SIZE = (VIEW_COLS * TILE_SIZE, VIEW_ROWS * TILE_SIZE)
FRAME_W = 120
FRAME_H = 80
SCALE = 2
SPEED = 180
ANIM_FPS = 10
GRAVITY = 1900.0
JUMP_VELOCITY = -850.0
MAX_FALL = 1400.0
JUMP_HOLD_TIME = 0.25
JUMP_HOLD_FORCE = -1400.0
JUMP_CUT = 0.4
COYOTE_TIME = 0.12
JUMP_BUFFER = 0.12


def init_pygame():
    #setup pygame window and clock
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()
    pygame.display.set_caption('free knight prototype level')
    return screen, clock
