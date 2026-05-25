import pygame
import time

from src.draw_win import *
from src.tcp import *

FPS = 10

pygame.init()

white_color = (255,255,255)
black_color = (0, 0, 0)

# CREATING CANVAS
canvas = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
# DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

# TITLE OF CANVAS
pygame.display.set_caption("Monitory Client")

# image = pygame.image.load("assets/Screenshot.png")
exit = False

app_window = AppWindow()

tcp_thread = start_tcp_client("0.0.0.0")

# /home/asus-pc/Documents/bay/dev/sync/monitory_app_pygame/assets/ttf/FiraCode-Light.ttf

# font = pygame.font.Font('assets/ttf/FiraCode-Light.ttf', 32)
# text = font.render('GeeksForGeeks', True, green, blue)
# textRect = text.get_rect()
    
render = True
nextRender = time.time()

while not exit:
    loopTime = time.time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit = True
        # Redraw the window after resize to avoid graphical artefacts
        elif event == pygame.WINDOWRESIZED:
            render = True
    
    # check if its time to render
    if loopTime > nextRender:
        render = True
        nextRender = loopTime + 1 / FPS
    # wait about 2 ms if its not render time to avoid wasting of CPU cycles
    else:
        time.sleep(0.002)
    
    # Render the window
    if render:
        canvas.fill((0,0,0))
        app_window.draw_window(canvas)
        pygame.display.flip()
        render = False
    
# At this point something crashed or we exit
# Close the Window and quit pygame
pygame.quit()
# End networking thread
stop_tcp_client()
  
