def draw_menu(surf, font, options, selected, tile):
    #draw menu with tiled background
    surf.fill((25, 35, 70))
    if tile:
        tw, th = tile.get_size()
        for y in range(0, surf.get_height(), th):
            for x in range(0, surf.get_width(), tw):
                surf.blit(tile, (x, y))
    overlay = surf.copy()
    overlay.fill((0, 0, 0, 120))
    surf.blit(overlay, (0, 0))
    title = font.render('select level', True, (255, 245, 180))
    surf.blit(title, (surf.get_width() // 2 - title.get_width() // 2, 40))
    start_y = 100
    for idx, label in enumerate(options):
        color = (255, 255, 255) if idx == selected else (200, 200, 200)
        text = font.render(label, True, color)
        x = surf.get_width() // 2 - text.get_width() // 2
        y = start_y + idx * 32
        surf.blit(text, (x, y))
