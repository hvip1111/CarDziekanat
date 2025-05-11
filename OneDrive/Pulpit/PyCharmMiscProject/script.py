import pygame
import random
import sys

clock = pygame.time.Clock()
FPS = 60
pygame.init()

# Ustawienia ekranu
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gra Uczelniana")

# Kolory
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
BLUE = (100, 100, 255)

font = pygame.font.Font('munro.ttf', 18)
subject_font = pygame.font.Font('munro.ttf', 17)


# Funkcje pomocnicze
def render_text_with_outline(font, text, text_color, outline_color, outline_thickness=1):
    text_width, text_height = font.size(text)
    surface_size = (text_width + 2 * outline_thickness, text_height + 2 * outline_thickness)
    text_surface = pygame.Surface(surface_size, pygame.SRCALPHA)

    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx != 0 or dy != 0:
                text_outline = font.render(text, True, outline_color)
                text_surface.blit(text_outline, (dx + outline_thickness, dy + outline_thickness))

    text_main = font.render(text, True, text_color)
    text_surface.blit(text_main, (outline_thickness, outline_thickness))
    return text_surface


def get_clamped_text_rect(text_surface, pos):
    x, y = pos
    text_rect = text_surface.get_rect(center=(x + 30, y - 20))

    if text_rect.left < 0: text_rect.left = 0
    if text_rect.right > WIDTH: text_rect.right = WIDTH
    if text_rect.top < 0: text_rect.top = 0
    if text_rect.bottom > HEIGHT: text_rect.bottom = HEIGHT
    return text_rect


# Konfiguracja obiektów
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

GRADES_SQUARES = [
    {"rect": (700, 470, 50, 50), "message": "Tablica ocen"}
]

START_POSITIONS = {
    "payments": (400, 500),
    "pe_enrollments": (400, 500),
    "grades": (400, 500)
}

# Grafiki
background = pygame.image.load("map.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background1 = pygame.image.load("payments.png").convert()
background1 = pygame.transform.scale(background1, (WIDTH, HEIGHT))
background2 = pygame.image.load("PE_enrollment.png").convert()
background2 = pygame.transform.scale(background2, (WIDTH, HEIGHT))
background3 = pygame.image.load("grades.png").convert()
background3 = pygame.transform.scale(background3, (WIDTH, HEIGHT))

# Maski kolizji
road_mask = pygame.image.load("map_mask.png").convert()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))
payments_mask = pygame.image.load("payments_mask.png").convert()
payments_mask = pygame.transform.scale(payments_mask, (WIDTH, HEIGHT))
pe_enrollment_mask = pygame.image.load("PE_enrollment_mask.png").convert()
pe_enrollment_mask = pygame.transform.scale(pe_enrollment_mask, (WIDTH, HEIGHT))
grades_mask = pygame.image.load("grades_mask.png").convert()
grades_mask = pygame.transform.scale(grades_mask, (WIDTH, HEIGHT))

# Postać i pojazd
PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100
prawo_img = pygame.image.load("character_right.png").convert_alpha()
prawo_img = pygame.transform.scale(prawo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
prawo_idzie_img = pygame.image.load("character_right_move.png").convert_alpha()
prawo_idzie_img = pygame.transform.scale(prawo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_img = pygame.image.load("character_left.png").convert_alpha()
lewo_img = pygame.transform.scale(lewo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_idzie_img = pygame.image.load("character_left_move.png").convert_alpha()
lewo_idzie_img = pygame.transform.scale(lewo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

car_left = pygame.image.load("car_left.png")
car_left = pygame.transform.scale(car_left, (60, 60))
car_right = pygame.transform.scale(pygame.image.load("car_right.png"), (60, 60))
car_up = pygame.transform.scale(pygame.image.load("car_up.png"), (60, 60))
car_down = pygame.transform.scale(pygame.image.load("car_down.png"), (60, 60))

# Zmienne stanu
current_background = background
inside_building = False
entry_position = None
near_building = False
active_message = None
action_message = None
action_message_time = 0
show_grades = False
car_direction = "right"
car_x, car_y = 400, 280
character_x, character_y = 350, 450
speed_outside = 10
speed_inside = 4
buildings = [(100, 0), (730, 225), (390, 380)]
facing = "prawo"
is_moving = False
animation_counter = 0
current_frame = 0

# System ocen
subjects = [
    "podstawy /programowania",
    "analiza /matematyczna",
    "programowanie /obiektowe",
    "angielski",
    "Fizyka"
]
grades = {
    subject: [random.randint(1, 5) for _ in range(random.randint(3, 5))]
    for subject in subjects
}

grades = {
    subject: [random.randint(1, 5) for _ in range(random.randint(3, 5))]
    for subject in subjects
}

grades_bg = pygame.Surface((420, 230))
grades_bg.fill((160, 82, 45))


def update_animation():
    global animation_counter, current_frame
    if is_moving:
        animation_counter += 1
        if animation_counter >= 10:
            animation_counter = 0
            current_frame = 1 - current_frame
    else:
        current_frame = 0


def get_player_image():
    if facing == "prawo":
        return prawo_idzie_img if current_frame else prawo_img
    return lewo_idzie_img if current_frame else lewo_img


def draw_squares():
    if inside_building:
        if current_background == background1:
            [pygame.draw.rect(screen, RED, sq["rect"]) for sq in PAYMENTS_SQUARES]
        elif current_background == background2:
            [pygame.draw.rect(screen, RED, sq["rect"]) for sq in PE_SQUARES]
        elif current_background == background3:
            [pygame.draw.rect(screen, RED, sq["rect"]) for sq in GRADES_SQUARES]
    else:
        for x, y in [(100, 0), (730, 225), (390, 380)]:
            pygame.draw.rect(screen, RED, (x, y, 50, 50))


def handle_grades_display():
    grades_bg_rect = grades_bg.get_rect(topleft=(192, 162))
    screen.blit(grades_bg, grades_bg_rect)
    pygame.draw.rect(screen, BLACK, grades_bg_rect, 2)

    y = grades_bg_rect.y + 30
    x = grades_bg_rect.x + 30

    for subject, grades_list in grades.items():
        if '/' in subject:
            parts = subject.split('/')
            part1 = subject_font.render(parts[0].strip(), True, BLACK)
            part2 = subject_font.render(parts[1].strip(), True, BLACK)
            screen.blit(part1, (x, y))
            screen.blit(part2, (x, y + part1.get_height()))
            line_height = part1.get_height() + part2.get_height()
        else:
            text = subject_font.render(subject, True, BLACK)
            screen.blit(text, (x, y))
            line_height = text.get_height()

        grade_x = x + 250
        for grade in grades_list:
            color = GREEN if grade >= 4 else RED
            grade_text = subject_font.render(str(grade), True, color)
            screen.blit(grade_text, (grade_x, y))
            grade_x += 30

        y += line_height + 15


running = True
while running:
    screen.blit(current_background, (0, 0))
    current_time = pygame.time.get_ticks()
    active_message = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and inside_building:
                inside_building = False
                show_grades = False
                current_background = background
                if entry_position:
                    car_x, car_y = entry_position

            elif event.key == pygame.K_e:
                if inside_building:
                    player_rect = pygame.Rect(character_x, character_y, PLAYER_WIDTH, PLAYER_HEIGHT)

                    if current_background == background3:
                        for square in GRADES_SQUARES:
                            if player_rect.colliderect(pygame.Rect(square["rect"])):
                                show_grades = not show_grades
                    else:
                        squares = PAYMENTS_SQUARES if current_background == background1 else PE_SQUARES
                        for square in squares:
                            if player_rect.colliderect(pygame.Rect(square["rect"])):
                                action_message = "Akcja wykonana!"
                                action_message_time = current_time
                elif near_building:
                    inside_building = True
                    if near_building == (100, 0):
                        current_background = background1
                        character_x, character_y = START_POSITIONS["payments"]
                    elif near_building == (730, 225):
                        current_background = background2
                        character_x, character_y = START_POSITIONS["pe_enrollments"]
                    elif near_building == (390, 380):
                        current_background = background3
                        character_x, character_y = START_POSITIONS["grades"]

    keys = pygame.key.get_pressed()
    is_moving = False

    if inside_building:
        new_x, new_y = character_x, character_y

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed_inside
            facing = "lewo"
            is_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed_inside
            facing = "prawo"
            is_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed_inside
            is_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed_inside
            is_moving = True

        mask = None
        if current_background == background1:
            mask = payments_mask
        elif current_background == background2:
            mask = pe_enrollment_mask
        elif current_background == background3:
            mask = grades_mask

        if mask and mask.get_at((new_x + PLAYER_WIDTH // 2, new_y + PLAYER_HEIGHT // 2)) == (255, 255, 255, 255):
            character_x, character_y = new_x, new_y

        update_animation()
        screen.blit(get_player_image(), (character_x, character_y))

        if current_background == background3 and show_grades:
            handle_grades_display()

        player_rect = pygame.Rect(character_x, character_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        squares = []
        if current_background == background1:
            squares = PAYMENTS_SQUARES
        elif current_background == background2:
            squares = PE_SQUARES
        elif current_background == background3:
            squares = GRADES_SQUARES

        for square in squares:
            if player_rect.colliderect(pygame.Rect(square["rect"])):
                active_message = square["message"]
                break

    else:
        new_x, new_y = car_x, car_y
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed_outside
            car_direction = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed_outside
            car_direction = "right"
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed_outside
            car_direction = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed_outside
            car_direction = "down"

        if 0 <= new_x <= WIDTH - 60 and 0 <= new_y <= HEIGHT - 60:
            try:
                if road_mask.get_at((new_x + 30, new_y + 30)) == (255, 255, 255, 255):
                    car_x, car_y = new_x, new_y
            except:
                pass

        near_building = None
        for building in buildings:
            if (building[0] - 50 <= car_x <= building[0] + 50 and
                    building[1] - 50 <= car_y <= building[1] + 50):
                near_building = building
                break

        car_image = {
            "left": car_left,
            "right": car_right,
            "up": car_up,
            "down": car_down
        }[car_direction]
        screen.blit(car_image, (car_x, car_y))

        if near_building:
            text = render_text_with_outline(font, "Wciśnij E", BLACK, YELLOW)
            text_rect = get_clamped_text_rect(text, (car_x, car_y))
            screen.blit(text, text_rect)

    draw_squares()

    if active_message:
        text = render_text_with_outline(font, active_message, BLACK, YELLOW)
        text_rect = get_clamped_text_rect(text, (character_x, character_y))
        screen.blit(text, text_rect)

    if action_message and (current_time - action_message_time) < 2000:
        text = render_text_with_outline(font, action_message, BLACK, YELLOW)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()