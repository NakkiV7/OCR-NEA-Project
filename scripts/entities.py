import pygame
from boot import SPEED, GRAVITY, MAX_FALL, JUMP_VELOCITY, JUMP_HOLD_TIME, JUMP_HOLD_FORCE, JUMP_CUT, COYOTE_TIME, JUMP_BUFFER, SCALE


class PhysicsBody:
    def __init__(self, owner, e_type, pos, size):
        #owner reference and type string
        self.owner = owner
        self.type = e_type
        #position and size
        self.pos = list(pos)
        self.size = list(size)
        #velocity
        self.velocity = [0.0, 0.0]
        #collision flags
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

    def rect(self):
        #integer rect for collisions
        return pygame.Rect(int(self.pos[0]), int(self.pos[1]), int(self.size[0]), int(self.size[1]))

    def update(self, tilemap, movement=(0, 0), dt=0.0):
        #reset collisions each frame
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        move_x = movement[0] * dt
        move_y = movement[1] * dt
        frame_movement = (move_x + self.velocity[0] * dt, move_y + self.velocity[1] * dt)

        #horizontal move
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        #vertical move
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        #gravity
        self.velocity[1] = min(MAX_FALL, self.velocity[1] + GRAVITY * dt)
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0.0


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, animations, tilemap, spawn_projectile=None):
        super().__init__()
        #animations dict
        self.animations = animations
        #state
        self.state = 'idle'
        self.frames = self.animations[self.state]
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        #physics body
        body_w = int(40 * SCALE)
        body_h = int(70 * SCALE)
        self.body = PhysicsBody(self, 'player', [pos[0] - body_w // 2, pos[1] - body_h], [body_w, body_h])
        #movement
        self.speed = SPEED
        self.flip = False
        self.tilemap = tilemap
        self.spawn_projectile = spawn_projectile
        #jump state
        self.prev_jump = False
        self.jump_held = False
        self.jump_timer = 0.0
        self.coyote_timer = 0.0
        self.jump_buffer = 0.0
        #attack state
        self.attacking = False
        self.attack_timer = 0.0
        self.attack_cooldown = 1.0
        self.attack_anim_time = 0.25
        self.attack_speed = 520.0
        self.attack_anim_timer = 0.0
        #animation timing
        self.time_since_last = 0
        from boot import ANIM_FPS
        self.anim_dt = 1.0 / ANIM_FPS

    def update(self, dt):
        #input
        keys = pygame.key.get_pressed()
        move_x = (keys[pygame.K_d] - keys[pygame.K_a])
        attack_pressed = keys[pygame.K_j]

        #variable jump
        jump_down = keys[pygame.K_w] or keys[pygame.K_SPACE]
        jump_pressed = jump_down and not self.prev_jump
        jump_released = (not jump_down) and self.prev_jump
        if self.body.collisions['down']:
            self.coyote_timer = COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)
        if jump_pressed:
            self.jump_buffer = JUMP_BUFFER
        else:
            self.jump_buffer = max(0.0, self.jump_buffer - dt)

        if self.jump_buffer > 0 and self.coyote_timer > 0:
            self.body.velocity[1] = JUMP_VELOCITY
            self.jump_timer = 0.0
            self.jump_held = True
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
        elif jump_down and self.jump_held and self.jump_timer < JUMP_HOLD_TIME and self.body.velocity[1] < 0:
            self.body.velocity[1] += JUMP_HOLD_FORCE * dt
            self.jump_timer += dt

        if jump_released:
            self.jump_held = False
            if self.body.velocity[1] < 0:
                self.body.velocity[1] *= JUMP_CUT
        self.prev_jump = jump_down

        #attack handling with cooldown and short anim window
        if self.attack_timer > 0:
            self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.attacking:
            self.attack_anim_timer -= dt
            if self.attack_anim_timer <= 0:
                self.attacking = False
        if (not self.attacking) and attack_pressed and self.attack_timer <= 0:
            self.attacking = True
            self.attack_timer = self.attack_cooldown
            self.attack_anim_timer = self.attack_anim_time
            if self.spawn_projectile:
                direction = -1 if self.flip else 1
                origin = (self.body.pos[0] + self.body.size[0] / 2, self.body.pos[1] + self.body.size[1] / 2)
                self.spawn_projectile(origin, direction * self.attack_speed)

        #physics update
        horiz_movement = move_x * self.speed
        if self.tilemap:
            self.body.update(self.tilemap, movement=(horiz_movement, 0), dt=dt)

        #facing and anim state
        if horiz_movement != 0:
            self.flip = horiz_movement < 0
        if self.attacking and 'attack' in self.animations:
            self.state = 'attack'
        elif not self.body.collisions['down']:
            self.state = 'jump' if 'jump' in self.animations else 'idle'
        elif abs(move_x) >= 0.5:
            self.state = 'run'
        else:
            self.state = 'idle'
        if self.frames is not self.animations[self.state]:
            self.frames = self.animations[self.state]
            self.frame_index = 0
            self.time_since_last = 0

        #animate
        self.time_since_last += dt
        if self.time_since_last >= self.anim_dt:
            self.time_since_last -= self.anim_dt
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        frame = self.frames[self.frame_index]
        self.image = pygame.transform.flip(frame, self.flip, False)
        self.rect.centerx = int(self.body.pos[0] + self.body.size[0] / 2)
        self.rect.bottom = int(self.body.pos[1] + self.body.size[1])


class Projectile:
    def __init__(self, pos, vx, surf, radius):
        #position and velocity
        self.pos = list(pos)
        self.vx = vx
        self.surf = surf
        self.radius = radius
        self.rect = self.surf.get_rect(center=pos)

    def update(self, dt):
        #move horizontally
        self.pos[0] += self.vx * dt
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])

    def draw(self, surf, cam_x=0):
        #draw with camera offset
        surf.blit(self.surf, self.rect.move(-cam_x, 0))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, frames, tilemap, speed=120):
        super().__init__()
        #anim frames
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        #physics
        body_w = int(40 * SCALE)
        body_h = int(70 * SCALE)
        self.body = PhysicsBody(self, 'enemy', [pos[0] - body_w // 2, pos[1] - body_h], [body_w, body_h])
        self.tilemap = tilemap
        self.speed = speed
        self.flip = False
        self.jump_power = JUMP_VELOCITY * 0.9
        #anim timing
        self.time_since_last = 0
        from boot import ANIM_FPS
        self.anim_dt = 1.0 / ANIM_FPS

    def update(self, dt, target_pos):
        #chase player horizontally and jump when needed
        move_dir = -1 if target_pos[0] < self.body.pos[0] else 1
        horiz_movement = move_dir * self.speed
        self.body.update(self.tilemap, movement=(horiz_movement, 0), dt=dt)
        self.flip = horiz_movement < 0
        self._maybe_jump(move_dir)
        #animate run
        self.time_since_last += dt
        if self.time_since_last >= self.anim_dt:
            self.time_since_last -= self.anim_dt
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        frame = self.frames[self.frame_index]
        self.image = pygame.transform.flip(frame, self.flip, False)
        self.rect.centerx = int(self.body.pos[0] + self.body.size[0] / 2)
        self.rect.bottom = int(self.body.pos[1] + self.body.size[1])

    def draw(self, surf, cam_x=0):
        #draw with camera offset
        surf.blit(self.image, self.rect.move(-cam_x, 0))

    def _maybe_jump(self, move_dir):
        #jump if blocked or gap ahead
        if self.body.collisions['down']:
            blocked = self.body.collisions['left'] or self.body.collisions['right']
            ahead_x = self.body.pos[0] + move_dir * (self.body.size[0] * 0.6)
            feet_y = self.body.pos[1] + self.body.size[1] + 1
            ground_ahead = self.tilemap.is_solid_at(ahead_x, feet_y)
            if blocked or not ground_ahead:
                self.body.velocity[1] = self.jump_power
