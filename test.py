import pygame
pygame.init()

screen = pygame.display.set_mode((240, 320))
pygame.display.set_caption("Icon Test")

hotspot_icon = pygame.image.load("hotspot-icon.png").convert_alpha()
hotspot_icon = pygame.transform.smoothscale(hotspot_icon, (36, 23))
print("Icon size:", hotspot_icon.get_size())


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))  # Black background
    screen.blit(hotspot_icon, (10, 10))
    pygame.display.flip()

pygame.quit()