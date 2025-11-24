import os
import pygame
from pathlib import Path
from boot import FRAME_W, FRAME_H, SCALE, TILE_SIZE

#paths
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / 'assets'
KNIGHT_DIR = ASSETS_DIR / 'FreeKnight_v1' / 'Colour1' / 'NoOutline' / '120x80_PNGSheets'
ENEMY_DIR = ASSETS_DIR / 'FreeKnight_v1' / 'Colour2' / 'NoOutline' / '120x80_PNGSheets'
TILE_SHEET = ASSETS_DIR / 'Tile assets' / 'Terrain' / 'Terrain (16x16).png'
TILE_SOURCE_SIZE = 16
_MENU_TILE = None

#tile code map: layout chars to (col,row) in sheet
TILE_CODE_MAP = {
    '1': (1, 0),
    '2': (0, 0),
    '3': (2, 0),
    '4': (3, 0),
    '5': (1, 1),
    'F': (4, 1),
    'f': (4, 1),
}


def load_frames_from_sheet(path, frame_w=FRAME_W, frame_h=FRAME_H):
    #load a spritesheet and slice all frames across the first row
    sheet = pygame.image.load(str(path)).convert_alpha()
    w, _ = sheet.get_size()
    cols = w // frame_w
    frames = []
    for i in range(cols):
        rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        frames.append(frame)
    return frames


def load_knight_animations():
    #load idle, run, optional jump and attack animations
    idle_path = os.path.join(KNIGHT_DIR, '_Idle.png')
    run_path = os.path.join(KNIGHT_DIR, '_Run.png')
    jump_path = os.path.join(KNIGHT_DIR, '_Jump.png')
    attack_path = os.path.join(KNIGHT_DIR, '_Attack.png')
    if not os.path.exists(idle_path) or not os.path.exists(run_path):
        raise FileNotFoundError(f'missing knight sheets in {KNIGHT_DIR}')
    animations = {
        'idle': [pygame.transform.scale(frame, (frame.get_width() * SCALE, frame.get_height() * SCALE)) for frame in load_frames_from_sheet(idle_path)],
        'run': [pygame.transform.scale(frame, (frame.get_width() * SCALE, frame.get_height() * SCALE)) for frame in load_frames_from_sheet(run_path)],
    }
    if os.path.exists(jump_path):
        animations['jump'] = [pygame.transform.scale(frame, (frame.get_width() * SCALE, frame.get_height() * SCALE)) for frame in load_frames_from_sheet(jump_path)]
    if os.path.exists(attack_path):
        animations['attack'] = [pygame.transform.scale(frame, (frame.get_width() * SCALE, frame.get_height() * SCALE)) for frame in load_frames_from_sheet(attack_path)]
    return animations


def load_enemy_run():
    #load enemy run frames from alternate colour set
    run_path = os.path.join(ENEMY_DIR, '_Run.png')
    idle_path = os.path.join(ENEMY_DIR, '_Idle.png')
    base_path = run_path if os.path.exists(run_path) else idle_path
    if not base_path or not os.path.exists(base_path):
        raise FileNotFoundError(f'missing enemy sheets in {ENEMY_DIR}')
    return [pygame.transform.scale(frame, (frame.get_width() * SCALE, frame.get_height() * SCALE)) for frame in load_frames_from_sheet(base_path)]


def slice_tileset(path=TILE_SHEET, source_size=TILE_SOURCE_SIZE, target_size=TILE_SIZE):
    #slice terrain sheet into scaled tiles
    sheet = pygame.image.load(str(path)).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()
    cols = sheet_w // source_size
    rows = sheet_h // source_size
    tiles = []
    for y in range(rows):
        for x in range(cols):
            rect = pygame.Rect(x * source_size, y * source_size, source_size, source_size)
            tile = pygame.Surface((source_size, source_size), pygame.SRCALPHA)
            tile.blit(sheet, (0, 0), rect)
            if target_size != source_size:
                tile = pygame.transform.scale(tile, (target_size, target_size))
            tiles.append(tile)
    return tiles, cols


def make_orb_surface(radius=10):
    #create simple yellow orb surface
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 230, 90), (radius, radius), radius)
    pygame.draw.circle(surf, (255, 255, 210), (radius, radius), max(1, radius // 2))
    return surf, radius


def load_menu_tile():
    #load a single tile for menu background
    global _MENU_TILE
    if _MENU_TILE is not None:
        return _MENU_TILE
    tiles, _ = slice_tileset()
    _MENU_TILE = tiles[0] if tiles else None
    return _MENU_TILE
