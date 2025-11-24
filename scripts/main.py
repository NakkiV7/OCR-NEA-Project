import sys
import pygame
from boot import init_pygame
from game import Game


def main():
    #init pygame and game
    screen, clock = init_pygame()
    game = Game()
    running = True
    while running:
        #delta time
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        #update and draw
        game.update(dt, events)
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
