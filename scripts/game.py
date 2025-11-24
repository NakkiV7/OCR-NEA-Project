import pygame
from scripts.boot import VIEW_COLS, TILE_SIZE
from scripts.level import Level, MovingPlatform
from scripts.timing import RunTimer
import scripts.data_manager as data_manager
import scripts.ui as ui
import scripts.assets as assets

#game states
STATE_MENU = 'menu'
STATE_PLAY = 'play'
STATE_FINISH = 'finish'
STATE_FAIL = 'fail'
STATE_MENU = 'menu'


class Game:
    def __init__(self):
        #create timer and levels
        self.timer = RunTimer()
        self.level = None
        self.level_layouts = self._build_levels()
        self.selected_level = 0
        self.state = STATE_MENU
        self.font = pygame.font.SysFont(None, 24)
        self.menu_tile = assets.load_menu_tile()

    def _build_levels(self):
        #define seven levels (level 1 is the current full course)
        level1_layout = [
            '000000000000000000000000000000000000000000000000000000000000',
            '000000000000000000000000000000000000000000000000000000000000',
            '000000000000000000000000000000000000000000000000000000000000',
            '000000000000000000000000000000000000000000000000000000000000',
            '000000000000000000000000000000000000000000000000000000000000',
            '000000000000000000000000000000000000000011100000000000000000',
            '000000000000000000000000000000000000011100000000000000000000',
            '000000000011000000000000011100000011100000000000000001111000',
            '0001111100000000011111110000000111000000000000001111100000F0',
            '111111111111111111111111111111111111111111111111111111111111',
            '111111111111111111111111111111111111111111111111111111111111',
        ]
        #level 2: dusk palette, varied tiles, moving platforms, longer run (~40s)
        level2_layout = [
            '0000000000000000000000000000000000000000000000000000000000000000000000000000',
            '0000000000000000000000000000000000000000000000000000000000000000000000000000',
            '0000000000000000000000000000000000000000000000000000000000000000000000000000',
            '0000000000000000000000000000000000000000000000000000000000000000000000000000',
            '0000000000000000000000000000000000000000000000000000000000000000000000000000',
            '0000000000000000222000000000000000000011111000000000222000000000000000000000',
            '0000000000000000111000000000022200000011111000000000111000000000000000000000',
            '00000000002220001110000000000111000000222220000000001110000000000000000000F0',
            '0001111100011111111111111111111111111111111111111111111111111111100000000000',
            '1111111111111111111111111111111111111111111111111111111111111111110000000000',
            '1111111111111111111111111111111111111111111111111111111111111111111111111111',
        ]
        plat_size = (TILE_SIZE * 2, TILE_SIZE // 2)
        platforms_level2 = [
            MovingPlatform(pos=(TILE_SIZE * 14, TILE_SIZE * 5), size=plat_size, delta=(TILE_SIZE * 6, 0), speed=90),
            MovingPlatform(pos=(TILE_SIZE * 30, TILE_SIZE * 4), size=plat_size, delta=(-TILE_SIZE * 5, 0), speed=110),
            MovingPlatform(pos=(TILE_SIZE * 52, TILE_SIZE * 5), size=plat_size, delta=(TILE_SIZE * 6, 0), speed=120),
        ]
        level2_cfg = {
            'layout': level2_layout,
            'bg_top': (40, 60, 120),
            'bg_bottom': (120, 80, 150),
            'platforms': platforms_level2,
            'player_start': (TILE_SIZE * 2, TILE_SIZE * 6),
        }
        level1_cfg = {'layout': level1_layout, 'bg_top': (70, 120, 190), 'bg_bottom': (130, 170, 210), 'platforms': [], 'player_start': (TILE_SIZE * 2, TILE_SIZE * 6)}
        placeholder_cfg = level1_cfg
        return [level1_cfg, level2_cfg, placeholder_cfg, placeholder_cfg, placeholder_cfg, placeholder_cfg, placeholder_cfg]

    def start_level(self, idx):
        #start selected level
        cfg = self.level_layouts[idx % len(self.level_layouts)]
        self.level = Level(cfg['layout'], bg_top=cfg.get('bg_top', (70, 120, 190)), bg_bottom=cfg.get('bg_bottom', (130, 170, 210)), platforms=cfg.get('platforms'), player_start=cfg.get('player_start'))
        self.timer.reset()
        self.timer.start()
        self.state = STATE_PLAY
        self.selected_level = idx

    def update(self, dt, events):
        #update based on state
        if self.state == STATE_MENU:
            self._handle_menu(events)
        elif self.state == STATE_PLAY:
            self.level.update(dt)
            if self.level.finished:
                self.timer.stop()
                self.state = STATE_FINISH
                data_manager.save_personal_best(f'level{self.selected_level+1}', self.timer.elapsed())
            if self.level.failed:
                self._restart_level()

    def draw(self, screen):
        #draw current state
        if self.state == STATE_MENU:
            ui.draw_menu(screen, self.font, [f'level {i+1}' for i in range(len(self.level_layouts))], self.selected_level, self.menu_tile)
        else:
            if self.state in (STATE_PLAY, STATE_FINISH):
                self.level.draw(screen)
                self._draw_hud(screen)
            if self.state == STATE_FINISH:
                self._draw_finish_overlay(screen)

    def _draw_hud(self, screen):
        #simple hud with timer and finish message
        timer_text = self.font.render(f'time: {self.timer.elapsed():0.2f}s', True, (255, 255, 255))
        screen.blit(timer_text, (10, 10))
        cd = max(0.0, self.level.player.attack_timer)
        cd_text = self.font.render(f'attack cd: {cd:0.1f}s', True, (255, 255, 255))
        screen.blit(cd_text, (10, 30))
        if self.state == STATE_FINISH:
            win_text = self.font.render('finish!', True, (80, 255, 120))
            screen.blit(win_text, (VIEW_COLS * TILE_SIZE // 2 - win_text.get_width() // 2, 40))

    def _restart_level(self):
        #reset level and timer after fail
        self.level = self._build_level()
        self.timer.reset()
        self.timer.start()
        self.state = STATE_PLAY

    def _draw_finish_overlay(self, screen):
        #large popup overlay indicating level end
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        box_rect = pygame.Rect(0, 0, screen.get_width() * 0.7, screen.get_height() * 0.4)
        box_rect.center = (screen.get_width() // 2, screen.get_height() // 2)
        pygame.draw.rect(overlay, (240, 230, 120, 230), box_rect)
        pygame.draw.rect(overlay, (255, 255, 200, 255), box_rect, 6)
        text = self.font.render('level ended', True, (60, 40, 10))
        overlay.blit(text, (box_rect.centerx - text.get_width() // 2, box_rect.centery - text.get_height() // 2))
        screen.blit(overlay, (0, 0))

    def _handle_menu(self, events):
        #navigate menu and start level
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    self.selected_level = (self.selected_level - 1) % len(self.level_layouts)
                elif ev.key == pygame.K_DOWN:
                    self.selected_level = (self.selected_level + 1) % len(self.level_layouts)
                elif pygame.K_1 <= ev.key <= pygame.K_7:
                    digit = ev.key - pygame.K_1
                    if digit < len(self.level_layouts):
                        self.selected_level = digit
                        self.start_level(self.selected_level)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start_level(self.selected_level)
