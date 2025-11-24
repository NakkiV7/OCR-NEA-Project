import pygame
from assets import slice_tileset, TILE_CODE_MAP, TILE_SHEET, TILE_SOURCE_SIZE, load_knight_animations, load_enemy_run, make_orb_surface
from boot import TILE_SIZE, VIEW_COLS, VIEW_ROWS
from entities import Player, Enemy, Projectile


class TileMap:
    def __init__(self, layout, tile_size=TILE_SIZE, bg_top=(70, 120, 190), bg_bottom=(130, 170, 210)):
        #store layout
        self.layout = layout
        self.tile_size = tile_size
        self.bg_top = bg_top
        self.bg_bottom = bg_bottom
        #tiles
        self.tile_images = []
        self.tileset_cols = 0
        self.finish_rect = None
        self.dynamic_provider = lambda: []
        if TILE_SHEET and tile_size:
            try:
                self.tile_images, self.tileset_cols = slice_tileset(TILE_SHEET, TILE_SOURCE_SIZE, tile_size)
            except Exception:
                self.tile_images = []
                self.tileset_cols = 0
        #collision rects
        self.physics_rects = []
        self.tile_index_map = {}
        self.solid_codes = set(TILE_CODE_MAP.keys())
        for y, row in enumerate(layout):
            for x, ch in enumerate(row):
                if ch != '0':
                    rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                    if ch in self.solid_codes:
                        self.physics_rects.append(rect)
                    if ch.lower() == 'f':
                        self.finish_rect = rect
                    idx = self._code_to_index(ch)
                    self.tile_index_map[(x, y)] = idx
        #precompute solid grid
        self.solid_grid = [[ch in self.solid_codes for ch in row] for row in layout]
        #fallback finish on last ground tile if none was placed
        if self.finish_rect is None and layout:
            fx = (len(layout[0]) - 1) * tile_size
            fy = (len(layout) - 1) * tile_size
            self.finish_rect = pygame.Rect(fx, fy, tile_size, tile_size)

    def physics_rects_around(self, _pos):
        #return all rects (map is small) plus dynamic rects
        return self.physics_rects + list(self.dynamic_provider())

    def is_solid_at(self, world_x, world_y):
        #check if a world coordinate hits a solid tile
        tx = int(world_x // self.tile_size)
        ty = int(world_y // self.tile_size)
        if ty < 0 or ty >= len(self.layout) or tx < 0 or tx >= len(self.layout[0]):
            return False
        return self.solid_grid[ty][tx]

    def render(self, surf, cam_x=0):
        #background gradient
        w, h = surf.get_size()
        for i in range(h):
            t = i / h
            rcol = int(self.bg_top[0] * (1 - t) + self.bg_bottom[0] * t)
            gcol = int(self.bg_top[1] * (1 - t) + self.bg_bottom[1] * t)
            bcol = int(self.bg_top[2] * (1 - t) + self.bg_bottom[2] * t)
            surf.fill((rcol, gcol, bcol), rect=pygame.Rect(0, i, w, 1))
        #visible rect
        view_rect = pygame.Rect(cam_x, 0, w, h)
        for y, row in enumerate(self.layout):
            for x, ch in enumerate(row):
                if ch == '0':
                    continue
                world_rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                if not view_rect.colliderect(world_rect):
                    continue
                pos = (world_rect.x - cam_x, world_rect.y)
                img = None
                idx = self.tile_index_map.get((x, y))
                if idx is not None and 0 <= idx < len(self.tile_images):
                    img = self.tile_images[idx]
                if img:
                    surf.blit(img, pos)
                else:
                    color = (230, 220, 110) if ch.lower() == 'f' else (100, 80, 40)
                    pygame.draw.rect(surf, color, pygame.Rect(pos[0], pos[1], self.tile_size, self.tile_size))
                #draw finish overlay for clarity
                if self.finish_rect and world_rect.colliderect(self.finish_rect):
                    overlay = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                    overlay.fill((240, 220, 50, 160))
                    pygame.draw.rect(overlay, (255, 245, 120), overlay.get_rect(), 2)
                    surf.blit(overlay, pos)

    def _code_to_index(self, ch):
        #map layout char to sheet index
        if ch in TILE_CODE_MAP and self.tileset_cols:
            col, row = TILE_CODE_MAP[ch]
            idx = row * self.tileset_cols + col
            if 0 <= idx < len(self.tile_images):
                return idx
        if ch.isdigit():
            v = int(ch)
            if v > 0 and v <= len(self.tile_images):
                return v - 1
        return None


class Level:
    def __init__(self, layout, bg_top=(70, 120, 190), bg_bottom=(130, 170, 210), platforms=None, player_start=None):
        #build tilemap and player
        self.tilemap = TileMap(layout, TILE_SIZE, bg_top=bg_top, bg_bottom=bg_bottom)
        self.projectiles = []
        self.tilemap.projectiles = self.projectiles
        self.orb_surf, self.orb_radius = make_orb_surface()
        start_pos = player_start if player_start else (TILE_SIZE * 2, TILE_SIZE * 6)
        self.player = Player(pos=start_pos, animations=load_knight_animations(), tilemap=self.tilemap, spawn_projectile=self.spawn_projectile)
        self.platforms = platforms if platforms else []
        self.tilemap.dynamic_provider = lambda: [p.rect for p in self.platforms]
        self.enemies = []
        self.spawn_triggers = [
            (TILE_SIZE * 8, 4),
            (TILE_SIZE * 22, 6),
            (TILE_SIZE * 40, 8),
        ]
        self.triggered = set()
        self.camera_x = 0
        self.finished = False
        self.failed = False
        self.width = len(layout[0]) * TILE_SIZE
        self.height = len(layout) * TILE_SIZE

    def update(self, dt):
        #freeze when finished or failed
        if self.finished or self.failed:
            return
        #update moving platforms first
        for plat in self.platforms:
            plat.update(dt)
        #carry player with platform if standing on top
        for plat in self.platforms:
            if self._player_on_platform(plat):
                dx, dy = plat.delta
                self.player.body.pos[0] += dx
                self.player.body.pos[1] += dy
        #update player and camera
        self.player.update(dt)
        target_x = self.player.body.pos[0] + self.player.body.size[0] / 2 - (VIEW_COLS * TILE_SIZE) / 2
        max_cam = max(0, self.width - VIEW_COLS * TILE_SIZE)
        self.camera_x = max(0, min(max_cam, target_x))
        if self._touching_finish():
            self.finished = True
        self._maybe_spawn_enemies()
        #update projectiles
        for proj in list(self.projectiles):
            proj.update(dt)
            if proj.pos[0] < 0 or proj.pos[0] > self.width:
                self.projectiles.remove(proj)
        #update enemies and collisions
        player_rect = self.player.body.rect()
        for enemy in list(self.enemies):
            enemy.update(dt, target_pos=(self.player.body.pos[0], self.player.body.pos[1]))
            #enemy hit player
            if enemy.body.rect().colliderect(player_rect):
                self.failed = True
            #projectile hits enemy
            for proj in list(self.projectiles):
                if self._projectile_hits_enemy(proj, enemy):
                    self.enemies.remove(enemy)
                    self.projectiles.remove(proj)
                    break

    def draw(self, surf):
        #render level and player
        self.tilemap.render(surf, cam_x=self.camera_x)
        for plat in self.platforms:
            plat.draw(surf, cam_x=self.camera_x)
        surf.blit(self.player.image, self.player.rect.move(-self.camera_x, 0))
        for enemy in self.enemies:
            enemy.draw(surf, cam_x=self.camera_x)
        for proj in self.projectiles:
            proj.draw(surf, cam_x=self.camera_x)

    def _spawn_enemies(self):
        #place a few enemies along the course (unused now)
        enemy_frames = load_enemy_run()
        spots = [
            (TILE_SIZE * 10, TILE_SIZE * 6),
            (TILE_SIZE * 25, TILE_SIZE * 6),
            (TILE_SIZE * 45, TILE_SIZE * 6),
        ]
        return [Enemy(pos=pos, frames=enemy_frames, tilemap=self.tilemap) for pos in spots]

    def spawn_projectile(self, pos, vx):
        #spawn yellow orb projectile
        self.projectiles.append(Projectile(pos, vx, self.orb_surf, self.orb_radius))

    def _maybe_spawn_enemies(self):
        #spawn batches when player reaches thresholds
        px = self.player.body.pos[0]
        enemy_frames = load_enemy_run()
        for idx, (threshold, count) in enumerate(self.spawn_triggers):
            if idx in self.triggered:
                continue
            if px >= threshold:
                self.triggered.add(idx)
                spacing = TILE_SIZE * 1.5
                #spawn just off the right edge of the current view
                offscreen_start = min(self.width - TILE_SIZE, self.camera_x + VIEW_COLS * TILE_SIZE + TILE_SIZE * 2)
                start_x = max(offscreen_start, threshold + TILE_SIZE)
                y = TILE_SIZE * 6
                for i in range(count):
                    pos = (start_x + spacing * i, y)
                    self.enemies.append(Enemy(pos=pos, frames=enemy_frames, tilemap=self.tilemap))

    def _touching_finish(self):
        #detect finish contact even when standing on top
        if not self.tilemap.finish_rect:
            return False
        player_rect = self.player.body.rect()
        finish_rect = self.tilemap.finish_rect
        if player_rect.colliderect(finish_rect):
            return True
        #edge-touch check: standing on top
        horizontal_overlap = (player_rect.right > finish_rect.left) and (player_rect.left < finish_rect.right)
        on_top = player_rect.bottom == finish_rect.top
        return horizontal_overlap and on_top

    def _player_on_platform(self, plat):
        #check if player stands on platform top
        player_rect = self.player.body.rect()
        rect = plat.rect
        horizontal_overlap = (player_rect.right > rect.left) and (player_rect.left < rect.right)
        on_top = player_rect.bottom == rect.top
        return horizontal_overlap and on_top

    def _projectile_hits_enemy(self, proj, enemy):
        #circle-rect collision using orb radius
        cx, cy = proj.rect.center
        rect = enemy.body.rect()
        nearest_x = max(rect.left, min(cx, rect.right))
        nearest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - nearest_x
        dy = cy - nearest_y
        return dx * dx + dy * dy <= proj.radius * proj.radius


class MovingPlatform:
    def __init__(self, pos, size, delta, speed):
        #movement endpoints
        self.start = list(pos)
        self.end = [pos[0] + delta[0], pos[1] + delta[1]]
        self.pos = list(pos)
        self.prev_pos = list(pos)
        self.size = size
        self.speed = speed
        self.direction = 1

    def update(self, dt):
        #move toward target
        self.prev_pos = list(self.pos)
        target = self.end if self.direction > 0 else self.start
        vx = target[0] - self.pos[0]
        vy = target[1] - self.pos[1]
        dist = (vx * vx + vy * vy) ** 0.5
        step = self.speed * dt
        if dist <= step or dist == 0:
            self.pos = list(target)
            self.direction *= -1
        else:
            self.pos[0] += vx / dist * step
            self.pos[1] += vy / dist * step

    @property
    def rect(self):
        #current rect
        return pygame.Rect(int(self.pos[0]), int(self.pos[1]), int(self.size[0]), int(self.size[1]))

    @property
    def delta(self):
        #frame movement delta
        return (self.pos[0] - self.prev_pos[0], self.pos[1] - self.prev_pos[1])

    def draw(self, surf, cam_x=0):
        #draw platform
        pygame.draw.rect(surf, (90, 120, 200), self.rect.move(-cam_x, 0))
