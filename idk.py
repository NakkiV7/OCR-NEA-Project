import pygame
import os
import sys

#config
SCREEN_SIZE = (800, 600)
FRAME_W = 120
FRAME_H = 80
SCALE = 2
MOVE_SPEED = 200
GRAVITY = 1700.0
JUMP_VELOCITY = -650.0
MAX_FALL = 1400.0
TILE_SIZE = 64

#paths
BASE_DIR = os.path.dirname(__file__)
KNIGHT_DIR = os.path.join(BASE_DIR, "assets", "FreeKnight_v1", "Colour1",
                          "NoOutline", "120x80_PNGSheets")
IDLE_SHEET = os.path.join(KNIGHT_DIR, "_Idle.png")
RUN_SHEET = os.path.join(KNIGHT_DIR, "_Run.png")


def load_frames(path):
    sheet = pygame.image.load(path).convert_alpha()
    w, _ = sheet.get_size()
    cols = w // FRAME_W
    frames = []
    for i in range(cols):
        rect = pygame.Rect(i * FRAME_W, 0, FRAME_W, FRAME_H)
        frame = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        frame = pygame.transform.scale(
            frame,
            (frame.get_width() * SCALE, frame.get_height() * SCALE),
        )
        frames.append(frame)
    return frames


class TileMap:
    def __init__(self, layout, tile_size=TILE_SIZE):
        self.layout = layout
        self.tile_size = tile_size
        self.physics_rects = []
        for y, row in enumerate(layout):
            for x, ch in enumerate(row):
                if ch == "1":
                    r = pygame.Rect(
                        x * tile_size, y * tile_size, tile_size, tile_size
                    )
                    self.physics_rects.append(r)

    def physics_rects_around(self, _pos):
        return self.physics_rects

    def draw(self, surf):
        surf.fill((60, 120, 190))
        for rect in self.physics_rects:
            pygame.draw.rect(surf, (80, 70, 60), rect)
            pygame.draw.rect(surf, (130, 120, 100), rect, 2)


class PhysicsBody:
    def __init__(self, pos, size):
        self.pos = list(pos)
        self.size = list(size)
        self.velocity = [0.0, 0.0]
        self.collisions = {"up": False, "down": False, "left": False, "right": False}

    def rect(self):
        return pygame.Rect(
            int(self.pos[0]), int(self.pos[1]),
            int(self.size[0]), int(self.size[1])
        )

    def update(self, tilemap, movement, dt):
        self.collisions = {"up": False, "down": False, "left": False, "right": False}

        move_x = movement[0] * dt
        move_y = movement[1] * dt
        frame_move = (move_x + self.velocity[0] * dt,
                      move_y + self.velocity[1] * dt)

        #horizontal
        self.pos[0] += frame_move[0]
        r = self.rect()
        for tile in tilemap.physics_rects_around(self.pos):
            if r.colliderect(tile):
                if frame_move[0] > 0:
                    r.right = tile.left
                    self.collisions["right"] = True
                elif frame_move[0] < 0:
                    r.left = tile.right
                    self.collisions["left"] = True
                self.pos[0] = r.x

        #vertical
        self.pos[1] += frame_move[1]
        r = self.rect()
        for tile in tilemap.physics_rects_around(self.pos):
            if r.colliderect(tile):
                if frame_move[1] > 0:
                    r.bottom = tile.top
                    self.collisions["down"] = True
                elif frame_move[1] < 0:
                    r.top = tile.bottom
                    self.collisions["up"] = True
                self.pos[1] = r.y

        #gravity
        self.velocity[1] = min(MAX_FALL, self.velocity[1] + GRAVITY * dt)
        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0.0


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, tilemap):
        super().__init__()
        self.animations = {
            "idle": load_frames(IDLE_SHEET),
            "run": load_frames(RUN_SHEET),
        }
        self.state = "idle"
        self.frames = self.animations[self.state]
        self.frame_index = 0
        self.time_since_last = 0.0
        self.anim_dt = 0.1

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

        body_w = 40 * SCALE
        body_h = 70 * SCALE
        self.body = PhysicsBody(
            pos=(pos[0] - body_w // 2, pos[1] - body_h),
            size=(body_w, body_h),
        )

        self.tilemap = tilemap
        self.speed = MOVE_SPEED
        self.flip = False

    def update(self, dt):
        keys = pygame.key.get_pressed()
        move_dir = keys[pygame.K_d] - keys[pygame.K_a]
        horiz_speed = move_dir * self.speed

        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_w]
        if jump_pressed and self.body.collisions["down"]:
            self.body.velocity[1] = JUMP_VELOCITY

        self.body.update(self.tilemap, (horiz_speed, 0), dt)

        if horiz_speed != 0:
            self.flip = horiz_speed < 0

        if not self.body.collisions["down"]:
            self.state = "idle"
        elif abs(move_dir) > 0:
            self.state = "run"
        else:
            self.state = "idle"

        if self.frames is not self.animations[self.state]:
            self.frames = self.animations[self.state]
            self.frame_index = 0
            self.time_since_last = 0.0

        self.time_since_last += dt
        if self.time_since_last >= self.anim_dt:
            self.time_since_last -= self.anim_dt
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        frame = self.frames[self.frame_index]
        self.image = pygame.transform.flip(frame, self.flip, False)

        self.rect.centerx = int(self.body.pos[0] + self.body.size[0] / 2)
        self.rect.bottom = int(self.body.pos[1] + self.body.size[1])


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()
    pygame.display.set_caption("knight platformer prototype")

    layout = [
        "0000000000",
        "0000000000",
        "0000000000",
        "0000000000",
        "0000000000",
        "0000111000",
        "1111111111",
        "1111111111",
        "1111111111",
    ]
    tilemap = TileMap(layout)
    player = Player(pos=(SCREEN_SIZE[0] // 3, SCREEN_SIZE[1] // 2), tilemap=tilemap)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(dt)

        tilemap.draw(screen)
        screen.blit(player.image, player.rect)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
