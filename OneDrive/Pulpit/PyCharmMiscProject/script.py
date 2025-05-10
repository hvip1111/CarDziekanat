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

# Konfiguracja kwadratów
PE_SQUARES = [
    {"rect": (90, 450, 50, 50), "message": "Siłownia"},
    {"rect": (100, 100, 50, 50), "message": "Ścianka wspinaczkowa"},
    {"rect": (400, 150, 50, 50), "message": "Siatka"},
    {"rect": (620, 250, 50, 50), "message": "Koszykówka"},
    {"rect": (600, 500, 50, 50), "message": "ping-pong"}
]

PAYMENTS_SQUARES = [
    {"rect": (90, 380, 50, 50), "message": "ECTS"},
    {"rect": (270, 380, 50, 50), "message": "Akademik"},
    {"rect": (420, 310, 50, 50), "message": "Ubezpieczenie"},
    {"rect": (640, 380, 50, 50), "message": "Legitymacja"}



]

START_POSITIONS = {
    "payments": (400, 500),
    "pe_enrollments": (100, 500)
}

# Stałe czasowe
MESSAGE_DURATION = 2000  # 2 sekundy

# Wczytanie tła
background = pygame.image.load("map.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background1 = pygame.image.load("payments.png")
background1 = pygame.transform.scale(background1, (WIDTH, HEIGHT))
background2 = pygame.image.load("PE_enrollment.png")
background2 = pygame.transform.scale(background2, (WIDTH, HEIGHT))

# Wczytanie masek kolizji
road_mask = pygame.image.load("map_mask.png").convert()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))

payments_mask = pygame.image.load("payments_mask.png").convert()
payments_mask = pygame.transform.scale(payments_mask, (WIDTH, HEIGHT))

pe_enrollment_mask = pygame.image.load("PE_enrollment_mask.png").convert()
pe_enrollment_mask = pygame.transform.scale(pe_enrollment_mask, (WIDTH, HEIGHT))

# Wczytanie pojazdu
car_left = pygame.image.load("car_left.png")
car_left = pygame.transform.scale(car_left, (60, 60))
car_right = pygame.image.load("car_right.png")
car_right = pygame.transform.scale(car_right, (60, 60))
car_up = pygame.image.load("car_up.png")
car_up = pygame.transform.scale(car_up, (60, 60))
car_down = pygame.image.load("car_down.png")
car_down = pygame.transform.scale(car_down, (60, 60))

car_direction = "right"

# Ładowanie postaci
PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100

prawo_img = pygame.image.load("character_right.png").convert_alpha()
prawo_img = pygame.transform.scale(prawo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
prawo_idzie_img = pygame.image.load("character_right_move.png").convert_alpha()
prawo_idzie_img = pygame.transform.scale(prawo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_img = pygame.image.load("character_left.png").convert_alpha()
lewo_img = pygame.transform.scale(lewo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_idzie_img = pygame.image.load("character_left_move.png").convert_alpha()
lewo_idzie_img = pygame.transform.scale(lewo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

# Zmienne animacji
facing = "prawo"
is_moving = False
animation_counter = 0
animation_delay = 10
current_frame = 0

# Pozycje i zmienne
car_x, car_y = 400, 280
character_x, character_y = 350, 450
speed = 15
buildings = [(100, 0), (730, 225)]
current_background = background
inside_building = False
entry_position = None
near_building = False
font = pygame.font.Font(None, 36)
active_message = None
action_message = None
action_message_time = 0


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
    if inside_building:
        if current_background == background1:
            for square in PAYMENTS_SQUARES:
                pygame.draw.rect(screen, RED, square["rect"])
        elif current_background == background2:
            for square in PE_SQUARES:
                pygame.draw.rect(screen, RED, square["rect"])
    else:
        pygame.draw.rect(screen, RED, (100, 0, 50, 50))
        pygame.draw.rect(screen, RED, (730, 225, 50, 50))


running = True
while running:
    screen.blit(current_background, (0, 0))
    draw_squares()

    current_time = pygame.time.get_ticks()
    active_message = None

    # Obsługa zdarzeń
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and inside_building:
                inside_building = False
                current_background = background
                if entry_position:
                    car_x, car_y = entry_position

            elif event.key == pygame.K_e and inside_building:
                # Sprawdź kolizję z kwadratami
                player_rect = pygame.Rect(character_x, character_y, PLAYER_WIDTH, PLAYER_HEIGHT)
                squares = PAYMENTS_SQUARES if current_background == background1 else PE_SQUARES if current_background == background2 else []

                for square in squares:
                    square_rect = pygame.Rect(square["rect"])
                    if player_rect.colliderect(square_rect):
                        action_message = "Kliknales w kwadracik essa!"
                        action_message_time = current_time
                        break

            elif event.key == pygame.K_e and near_building and not inside_building:
                inside_building = True
                if near_building == (100, 0):
                    current_background = background1
                    character_x, character_y = START_POSITIONS["payments"]
                elif near_building == (730, 225):
                    current_background = background2
                    character_x, character_y = START_POSITIONS["pe_enrollments"]

    # Aktualizacja stanu gry
    keys = pygame.key.get_pressed()
    is_moving = False

    if inside_building:
        new_x, new_y = character_x, character_y
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

        # Sprawdzanie kolizji z maską
        player_center = (new_x + PLAYER_WIDTH // 2, new_y + PLAYER_HEIGHT // 2)
        if current_background == background1:
            pixel_color = payments_mask.get_at(player_center)
        elif current_background == background2:
            pixel_color = pe_enrollment_mask.get_at(player_center)
        else:
            pixel_color = (0, 0, 0, 0)

        if pixel_color == (255, 255, 255, 255):
            character_x, character_y = new_x, new_y

        # Sprawdzanie kolizji z kwadratami
        player_rect = pygame.Rect(character_x, character_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        squares = PAYMENTS_SQUARES if current_background == background1 else PE_SQUARES if current_background == background2 else []

        for square in squares:
            square_rect = pygame.Rect(square["rect"])
            if player_rect.colliderect(square_rect):
                active_message = square["message"]
                break

        update_animation()

    else:
        # Poruszanie się pojazdem
        new_x, new_y = car_x, car_y
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed
            car_direction = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed
            car_direction = "right"
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed
            car_direction = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed
            car_direction = "down"

        if road_mask.get_at((new_x + 25, new_y + 25)) == (255, 255, 255, 255):
            car_x, car_y = new_x, new_y

        entry_position = (car_x, car_y)
        near_building = None
        for building in buildings:
            if (building[0] - 25 <= car_x <= building[0] + 25 and
                    building[1] - 25 <= car_y <= building[1] + 25):
                near_building = building
                break

    # Renderowanie
    if inside_building:
        screen.blit(get_player_image(), (character_x, character_y))

        # Wyświetlanie komunikatów
        if active_message:
            text = font.render(active_message, True, BLACK, WHITE)
            text_rect = text.get_rect(center=(character_x + PLAYER_WIDTH // 2, character_y - 20))
            screen.blit(text, text_rect)

        if action_message and (current_time - action_message_time) < MESSAGE_DURATION:
            text = font.render(action_message, True, BLACK, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, 50))
            screen.blit(text, text_rect)
        else:
            action_message = None

    else:
        # Renderowanie pojazdu
        if car_direction == "left":
            screen.blit(car_left, (car_x, car_y))
        elif car_direction == "right":
            screen.blit(car_right, (car_x, car_y))
        elif car_direction == "up":
            screen.blit(car_up, (car_x, car_y))
        elif car_direction == "down":
            screen.blit(car_down, (car_x, car_y))

        if near_building:
            text = font.render("Wciśnij E, aby wejść", True, BLACK)
            text_rect = text.get_rect(center=(car_x + 30, car_y - 20))
            screen.blit(text, text_rect)

    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()