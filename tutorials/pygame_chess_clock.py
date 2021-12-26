import pygame
import os

pygame.init()

WHITE = (255, 255, 255)
YELLOW = (241, 194, 125)
BLACK = (0, 0, 0)
FONT = pygame.font.Font("OpenSans-Regular.ttf", 50)

screen = pygame.display.set_mode((500, 500))
screen.fill(WHITE)

pygame.display.set_caption("Chess clock")
clock = pygame.time.Clock()
run = True

upper_rect = pygame.Rect(0, 0, 500, 250)
lower_rect = pygame.Rect(0, 250, 500, 250)
upper_color, lower_color = YELLOW, WHITE

upper_time_text = FONT.render("10:00", True, BLACK)
upper_time_text_rect = upper_time_text.get_rect()
upper_time_text_rect.center = (250, 125)

lower_time_text = FONT.render("10:00", True, BLACK)
lower_time_text_rect = lower_time_text.get_rect()
lower_time_text_rect.center = (250, 375)

curr_rect = "upper"
upper_time = 600
lower_time = 600

def from_sec_to_minsec(sec):
    sec = int(sec) + 1
    curr_sec = sec % 60
    curr_min = sec // 60

    return (curr_min, curr_sec)

def display_time(screen, time, center_pos):
    global BLACK
    curr_min, curr_sec = from_sec_to_minsec(time)
    text = f"{curr_min}:{curr_sec}"

    time_text = FONT.render(text, True, BLACK)
    time_text_rect = time_text.get_rect()
    time_text_rect.center = center_pos
    screen.blit(time_text, time_text_rect)

start_tick = pygame.time.get_ticks()
clock.tick()

while run:

    screen.fill(WHITE)
    tick = pygame.time.get_ticks()
    time_passed = (tick - start_tick) / 1000

    sec_elapsed = clock.tick() / 1000

    if curr_rect == "upper":
        upper_time = upper_time - sec_elapsed
    else:
        lower_time = lower_time - sec_elapsed

    pygame.draw.rect(screen, upper_color, upper_rect)
    pygame.draw.rect(screen, lower_color, lower_rect)

    display_time(screen, upper_time, (250, 125))
    display_time(screen, lower_time, (250, 375))

    pos = pygame.mouse.get_pos()
    for event in pygame.event.get():

        # Quitting the game
        if event.type == pygame.QUIT:
            pygame.quit()
            run = False

        # On click mouse down
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pos
            # Upper rect
            if y < 250:
                upper_color = YELLOW
                lower_color = WHITE
                clicked_rect = "upper"
            # Lower rect
            else:
                upper_color = WHITE
                lower_color = YELLOW
                clicked_rect = "lower"

            # Change current chosen time
            if clicked_rect != curr_rect:
                curr_rect = clicked_rect

    if run:
        pygame.display.update()