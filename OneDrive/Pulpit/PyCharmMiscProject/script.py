import pygame

pygame.init()

# Ustawienia ekranu
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gra z określonymi ścieżkami")

# Kolory
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Wczytanie tła
background = pygame.image.load("mapa.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background1 = pygame.image.load("background1.png")
background1 = pygame.transform.scale(background1, (WIDTH, HEIGHT))
background2 = pygame.image.load("zapisynawf.png")
background2 = pygame.transform.scale(background2, (WIDTH, HEIGHT))

# Wczytanie maski kolizji
road_mask = pygame.image.load("maskbackground.png").convert()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))

# Wczytanie pojazdu (zachowujemy oryginalny rozmiar 50x50)
car = pygame.image.load("car.png")
car = pygame.transform.scale(car, (50, 50))

# Ładowanie animacji postaci z większym rozmiarem (75x75)
PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100  # Nowy rozmiar postaci (150% z 50x50)

prawo_img = pygame.image.load("prawo.png").convert_alpha()
prawo_img = pygame.transform.scale(prawo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
prawo_idzie_img = pygame.image.load("prawo_idzie.png").convert_alpha()
prawo_idzie_img = pygame.transform.scale(prawo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_img = pygame.image.load("lewo.png").convert_alpha()
lewo_img = pygame.transform.scale(lewo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_idzie_img = pygame.image.load("lewo_idzie.png").convert_alpha()
lewo_idzie_img = pygame.transform.scale(lewo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

# Zmienne animacji
facing = "prawo"
is_moving = False
animation_counter = 0
animation_delay = 10
current_frame = 0

# Pozycja początkowa i zmienne
car_x, car_y = 400, 300
speed = 5
buildings = [(100, 0), (730, 225)]
current_background = background
inside_building = False
entry_position = None
near_building = False
font = pygame.font.Font(None, 36)


def update_animation():
    global animation_counter, current_frame
    if is_moving:
        animation_counter += 1
        if animation_counter >= animation_delay:
            animation_counter = 0
            current_frame = 1 - current_frame
    else:
        current_frame = 0


def get_player_image():
    if facing == "prawo":
        return prawo_idzie_img if current_frame else prawo_img
    else:
        return lewo_idzie_img if current_frame else lewo_img


def draw_squares():
    if not inside_building:
        pygame.draw.rect(screen, RED, (100, 0, 50, 50))
        pygame.draw.rect(screen, RED, (730, 225, 50, 50))


running = True
while running:
    screen.blit(current_background, (0, 0))
    draw_squares()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and inside_building:
                inside_building = False
                current_background = background
                if entry_position:
                    car_x, car_y = entry_position
            elif event.key == pygame.K_e and near_building and not inside_building:
                inside_building = True
                car_x, car_y = WIDTH // 2 - PLAYER_WIDTH // 2, HEIGHT // 2 - PLAYER_HEIGHT // 2  # Centrowanie większej postaci
                if near_building == (100, 0):
                    current_background = background1
                elif near_building == (730, 225):
                    current_background = background2

    keys = pygame.key.get_pressed()
    new_x, new_y = car_x, car_y
    is_moving = False

    if inside_building:
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed
            facing = "lewo"
            is_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed
            facing = "prawo"
            is_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed
            is_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed
            is_moving = True

        car_x, car_y = new_x, new_y
        update_animation()
    else:
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed

        if road_mask.get_at((new_x + 25, new_y + 25)) == (255, 255, 255, 255):
            car_x, car_y = new_x, new_y

        entry_position = (car_x, car_y)
        near_building = None

        for building in buildings:
            if (building[0] - 25 <= car_x <= building[0] + 25 and
                    building[1] - 25 <= car_y <= building[1] + 25):
                near_building = building
                break

    if inside_building:
        screen.blit(get_player_image(), (car_x, car_y))
    else:
        screen.blit(car, (car_x, car_y))

        if near_building:
            text = font.render("Wciśnij E, aby wejść", True, BLACK)
            text_width, text_height = text.get_size()
            text_x = max(0, min(car_x - 50, WIDTH - text_width))
            text_y = max(0, min(car_y - 40, HEIGHT - text_height))
            screen.blit(text, (text_x, text_y))

    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()