import pygame
import os

pygame.init()
screen = pygame.display.set_mode((500, 500))
screen.fill((255, 255, 255))
pygame.display.set_caption("Practice with images")

# Import an image
link = "img\\blackking.png"
img = pygame.image.load(link)
screen.blit(img, (0, 0))
img_rect = img.get_rect()

# Update view
pygame.display.update()

# Wait for exit
run = True
start_ticks = pygame.time.get_ticks()
clock = pygame.time.Clock()
clock.tick()
while run:

    #seconds=(pygame.time.get_ticks()-start_ticks)/1000
    #if int(seconds) == seconds:
        #print(f"Seconds from get_ticks: {int(seconds)}")
    
    
    pos = pygame.mouse.get_pos()
    for event in pygame.event.get():

        # Quitting the game
        if event.type == pygame.QUIT:
            pygame.quit()
            run = False

        # On click mouse down, move the image
        if event.type == pygame.MOUSEBUTTONDOWN:
            #print("Yo")
            #if img_rect.collidepoint(pos):
            dt = clock.tick() / 1000
            print(f"Seconds from clock.tick: {dt}")
            screen.fill((255,255,255))
            new_pos = pos
            screen.blit(img, new_pos)
            img_rect = img.get_rect()
            pygame.display.update()

        # On click mouse up, settle the image
        if event.type == pygame.MOUSEBUTTONUP:
            pass
            #print("Ya")


    click = pygame.mouse.get_pressed()
    if click[0]:
        #if img_rect.collidepoint(pos):
        #print(True)
        screen.fill((255,255,255))
        new_pos = pos
        img_rect = img.get_rect()
        img_rect.center = new_pos
        screen.blit(img, img_rect)
        img_rect = img.get_rect()
        pygame.display.update()
        
        

            
