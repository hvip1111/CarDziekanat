import pygame
import random
import sys
from PIL import Image  # Odkomentowane i używane
import time

clock = pygame.time.Clock()
FPS = 60
pygame.init()

# Ustawienia ekranu
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gra Uczelniana")

# --- Zmiany dla Animacji Monety ---
COIN_SIZE = (40, 40)
coin_frames = []
try:
    gif_image = Image.open("coin.gif")
    if gif_image.n_frames > 0:  # Upewnij się, że GIF ma klatki
        for frame_num in range(gif_image.n_frames):
            gif_image.seek(frame_num)
            # Konwertuj klatkę Pillow do RGBA, aby zachować przezroczystość
            frame_rgba = gif_image.convert("RGBA")
            # Stwórz powierzchnię Pygame z danych klatki
            pygame_frame = pygame.image.fromstring(
                frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode
            )
            pygame_frame = pygame.transform.scale(pygame_frame, COIN_SIZE)
            pygame_frame = pygame_frame.convert_alpha()  # Ważne dla przezroczystości i wydajności
            coin_frames.append(pygame_frame)
    else:  # Jeśli GIF nie ma klatek (np. jest to statyczny obraz zapisany jako GIF)
        print("Ostrzeżenie: coin.gif nie zawiera klatek animacji lub jest niepoprawny. Ładowanie jako statyczny obraz.")
        # Wczytaj jako statyczny obraz, jeśli nie ma klatek
        static_coin_img = pygame.image.load("coin.gif").convert_alpha()
        static_coin_img = pygame.transform.scale(static_coin_img, COIN_SIZE)
        coin_frames.append(static_coin_img)

except FileNotFoundError:
    print("Błąd: Nie znaleziono pliku coin.gif. Tworzenie zastępczej monety.")
    # Zastępcza moneta, jeśli GIF nie zostanie znaleziony
    fallback_coin_img = pygame.Surface(COIN_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(fallback_coin_img, (255, 223, 0), (COIN_SIZE[0] // 2, COIN_SIZE[1] // 2), COIN_SIZE[0] // 2)
    coin_frames.append(fallback_coin_img)
except Exception as e:  # Łapanie innych potencjalnych błędów z Pillow
    print(f"Błąd podczas ładowania coin.gif: {e}. Tworzenie zastępczej monety.")
    fallback_coin_img = pygame.Surface(COIN_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(fallback_coin_img, (255, 223, 0), (COIN_SIZE[0] // 2, COIN_SIZE[1] // 2), COIN_SIZE[0] // 2)
    coin_frames.append(fallback_coin_img)

if not coin_frames:  # Ostateczny fallback, jeśli lista klatek jest pusta
    print("Nie udało się załadować żadnych klatek monety. Tworzenie domyślnej.")
    fallback_coin_img = pygame.Surface(COIN_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(fallback_coin_img, (255, 223, 0), (COIN_SIZE[0] // 2, COIN_SIZE[1] // 2),
                       COIN_SIZE[0] // 2)  # Użyłem koloru podobnego do złota
    coin_frames.append(fallback_coin_img)

current_coin_frame_index = 0
coin_animation_timer = pygame.time.get_ticks()
COIN_ANIMATION_SPEED = 100  # Czas w ms między klatkami animacji monety (np. 100ms)
# --- Koniec Zmian dla Animacji Monety ---

coins = 0  # Początkowa ilość monet

# Kolory
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)  # Używany do obrysu tekstu
GREEN = (0, 128, 0)
BLUE = (100, 100, 255)

font = pygame.font.Font('munro.ttf', 18)
subject_font = pygame.font.Font('munro.ttf', 17)


# Funkcje pomocnicze
def render_text_with_outline(font_obj, text, text_color, outline_color,
                             outline_thickness=1):  # Zmieniono nazwę font na font_obj
    text_width, text_height = font_obj.size(text)
    surface_size = (text_width + 2 * outline_thickness, text_height + 2 * outline_thickness)
    text_surface = pygame.Surface(surface_size, pygame.SRCALPHA)

    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx != 0 or dy != 0:  # Rysuj tylko jeśli jest przesunięcie (dla efektu obrysu)
                # Renderowanie cienia/obrysu tylko raz nie jest optymalne, ale dla małego outline_thickness jest OK
                text_outline = font_obj.render(text, True, outline_color)
                text_surface.blit(text_outline, (dx + outline_thickness, dy + outline_thickness))

    text_main = font_obj.render(text, True, text_color)
    text_surface.blit(text_main, (outline_thickness, outline_thickness))
    return text_surface


def get_clamped_text_rect(text_surface, pos):
    x, y = pos
    # Pozycjonowanie tekstu nad graczem/samochodem, nieco na prawo
    text_rect = text_surface.get_rect(center=(x + 30, y - 20))  # 30 to połowa szerokości auta/gracza, -20 by było nad

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
PE_SQUARES_2 = [  # Te są używane gdy current_background == background2
    {"rect": (90, 460, 50, 50), "message": "Siłownia"},  # Dostosuj pozycje do background2
    {"rect": (140, 195, 50, 50), "message": "Ścianka wspinaczkowa"},
    {"rect": (440, 230, 50, 50), "message": "Siatka"},
    {"rect": (620, 260, 50, 50), "message": "Koszykówka"},
    {"rect": (600, 530, 50, 50), "message": "ping-pong"}
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
    "payments": (WIDTH // 2 - 50, HEIGHT - 150),  # Przykładowe pozycje startowe w budynkach
    "pe_enrollments": (WIDTH // 2 - 50, HEIGHT - 150),
    "grades": (WIDTH // 2 - 50, HEIGHT - 150)
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
road_mask = pygame.image.load("map_mask.png").convert_alpha()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))
payments_mask = pygame.image.load("payments_mask.png").convert_alpha()
payments_mask = pygame.transform.scale(payments_mask, (WIDTH, HEIGHT))
pe_enrollment_mask = pygame.image.load("PE_enrollment_mask.png").convert_alpha()
pe_enrollment_mask = pygame.transform.scale(pe_enrollment_mask, (WIDTH, HEIGHT))
grades_mask = pygame.image.load("grades_mask.png").convert_alpha()
grades_mask = pygame.transform.scale(grades_mask, (WIDTH, HEIGHT))

# Postać i pojazd
PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100  # Rozmiar obrazka postaci
prawo_img = pygame.image.load("character_right.png").convert_alpha()
prawo_img = pygame.transform.scale(prawo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
prawo_idzie_img = pygame.image.load("character_right_move.png").convert_alpha()
prawo_idzie_img = pygame.transform.scale(prawo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_img = pygame.image.load("character_left.png").convert_alpha()
lewo_img = pygame.transform.scale(lewo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_idzie_img = pygame.image.load("character_left_move.png").convert_alpha()
lewo_idzie_img = pygame.transform.scale(lewo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

CAR_SIZE = (70, 70)  # Rozmiar samochodu
car_left = pygame.image.load("car_left.png").convert_alpha()
car_left = pygame.transform.scale(car_left, CAR_SIZE)
car_right = pygame.image.load("car_right.png").convert_alpha()
car_right = pygame.transform.scale(car_right, CAR_SIZE)
car_up = pygame.image.load("car_up.png").convert_alpha()
car_up = pygame.transform.scale(car_up, CAR_SIZE)
car_down = pygame.image.load("car_down.png").convert_alpha()
car_down = pygame.transform.scale(car_down, CAR_SIZE)

# Zmienne stanu
current_background = background
inside_building = False
entry_position = None  # Pozycja samochodu przed wejściem do budynku
near_building = None  # Przechowuje krotkę (x,y) budynku, jeśli jest blisko, inaczej None
active_message = None  # Komunikat wyświetlany nad obiektem interakcji
action_message = None  # Komunikat o wykonanej akcji
action_message_time = 0
show_grades = False
car_direction = "right"
car_x, car_y = 1000, 530  # Startowa pozycja samochodu
character_x, character_y = 350, 450  # Startowa pozycja postaci (używana w budynkach)

# --- Zmiany dla płynniejszego ruchu ---
velocity_x_char, velocity_y_char = 0, 0
velocity_x_car, velocity_y_car = 0, 0

acceleration_char = 0.5
deceleration_char = 0.2  # Zwiększono, aby postać szybciej się zatrzymywała
max_speed_char = 4

acceleration_car = 0.3  # Zmniejszono, aby auto nie przyspieszało zbyt gwałtownie
deceleration_car = 0.2  # Zwiększono, aby auto szybciej hamowało
max_speed_car = 5  # Zmniejszono dla lepszej kontroli
# --- Koniec zmian dla płynniejszego ruchu ---

buildings = [(275, 20), (1800, 400), (1050, 650)]  # Pozycje (x,y) lewego górnego rogu budynków
facing = "prawo"  # Kierunek postaci
is_moving = False  # Czy postać się porusza (dla animacji)
animation_counter = 0
current_frame = 0  # Dla animacji postaci (0 lub 1)

# System ocen
subjects = [
    "podstawy /programowania",
    "analiza /matematyczna",
    "programowanie /obiektowe",
    "angielski",
    "Fizyka"
]
grades = {
    subject: [random.randint(2, 5) for _ in range(random.randint(3, 5))]
    for subject in subjects
}

grades_bg_width, grades_bg_height = 420, 230  # Rozmiar tła dla ocen
grades_bg_x = (WIDTH - grades_bg_width) // 2
grades_bg_y = (HEIGHT - grades_bg_height) // 2
grades_bg = pygame.Surface((grades_bg_width, grades_bg_height))
grades_bg.fill((160, 82, 45))  # Kolor brązowy (saddlebrown)


def update_animation():
    global animation_counter, current_frame
    if is_moving:
        animation_counter += 1
        if animation_counter >= 10:  # Co 10 klatek gry zmień klatkę animacji postaci
            animation_counter = 0
            current_frame = 1 - current_frame  # Przełącz między 0 a 1
    else:
        current_frame = 0  # Postać stoi


def get_player_image():
    if facing == "prawo":
        return prawo_idzie_img if current_frame == 1 else prawo_img
    return lewo_idzie_img if current_frame == 1 else lewo_img


LIGHT_GREEN_ALPHA = (144, 238, 144, 150)  # Lekko przezroczysty zielony


def draw_interaction_indicators():  # Zmieniono nazwę z draw_squares
    indicator_radius = 25
    indicator_width = 3

    if inside_building:
        squares_to_draw = []
        if current_background == background1:  # Payments
            squares_to_draw = PAYMENTS_SQUARES
        elif current_background == background2:  # PE enrollments
            squares_to_draw = PE_SQUARES_2  # Używamy PE_SQUARES_2
        elif current_background == background3:  # Grades
            squares_to_draw = GRADES_SQUARES

        for sq_info in squares_to_draw:
            x, y, w, h = sq_info["rect"]
            center = (x + w // 2, y + h // 2)
            pygame.draw.circle(screen, LIGHT_GREEN_ALPHA, center, min(w, h) // 2 + 5,
                               indicator_width)  # Trochę większy okrąg
    else:  # Na zewnątrz, rysuj wskaźniki przy budynkach
        for bx, by in buildings:
            # Rysuj okrąg wokół wejścia do budynku (przyjmując, że wejście jest w lewym górnym rogu budynku)
            center_x = bx + CAR_SIZE[0] // 2  # Dostosuj do środka miejsca, gdzie parkuje auto
            center_y = by + CAR_SIZE[1] // 2
            pygame.draw.circle(screen, LIGHT_GREEN_ALPHA, (center_x, center_y), indicator_radius, indicator_width)


def handle_grades_display():
    grades_bg_rect = grades_bg.get_rect(topleft=(grades_bg_x, grades_bg_y))
    screen.blit(grades_bg, grades_bg_rect)
    pygame.draw.rect(screen, BLACK, grades_bg_rect, 2)  # Ramka wokół

    y_offset = grades_bg_rect.y + 20  # Zwiększony margines
    x_start = grades_bg_rect.x + 20

    for subject, grades_list in grades.items():
        # Rysowanie nazwy przedmiotu
        max_subject_width = grades_bg_width * 0.5  # Ograniczenie szerokości dla nazwy przedmiotu
        if '/' in subject:
            parts = subject.split('/')
            part1_surf = subject_font.render(parts[0].strip(), True, BLACK)
            part2_surf = subject_font.render(parts[1].strip(), True, BLACK)
            screen.blit(part1_surf, (x_start, y_offset))
            screen.blit(part2_surf, (x_start, y_offset + part1_surf.get_height()))
            line_height = part1_surf.get_height() + part2_surf.get_height()
        else:
            text_surf = subject_font.render(subject, True, BLACK)
            screen.blit(text_surf, (x_start, y_offset))
            line_height = text_surf.get_height()

        # Rysowanie ocen
        grade_x = x_start + max_subject_width + 30  # Pozycja X dla pierwszej oceny
        for grade_val in grades_list:
            color = GREEN if grade_val >= 3 else RED  # 3 jako próg zaliczenia
            grade_text_surf = subject_font.render(str(grade_val), True, color)
            screen.blit(grade_text_surf, (
            grade_x, y_offset + (line_height - grade_text_surf.get_height()) // 2))  # Wyśrodkowanie ocen w pionie
            grade_x += 30  # Odstęp między ocenami

        y_offset += line_height + 10  # Odstęp między przedmiotami


# --- Elementy dla monet ---
all_possible_coin_spawn_locations = [
    (50, 50), (150, 100), (250, 50), (350, 100), (450, 50),
    (550, 100), (650, 50), (750, 100), (50, 200), (150, 250),
    (250, 200), (350, 250), (450, 200), (550, 250), (650, 200),
    (750, 250), (50, 350), (150, 400), (250, 350), (350, 400),
    (450, 350), (550, 400), (650, 350), (750, 400), (50, 500),
    (150, 550), (250, 500), (350, 550), (450, 500), (550, 550),
    (650, 500), (750, 550), (100, 300), (700, 300), (400, 150),
    (400, 450)
]

road_mask_locations = []
# --- INICJALIZACJA: FILTROWANIE PUNKTÓW SPAWNU MONET NA DRODZE ---
# Potrzebujemy pierwszej klatki monety do określenia jej rozmiaru dla road_mask
temp_coin_img_for_size = coin_frames[0] if coin_frames else pygame.Surface(COIN_SIZE)

for x, y in all_possible_coin_spawn_locations:
    check_x, check_y = x + temp_coin_img_for_size.get_width() // 2, y + temp_coin_img_for_size.get_height() // 2
    if 0 <= check_x < WIDTH and 0 <= check_y < HEIGHT:
        try:
            pixel_color = road_mask.get_at((check_x, check_y))
            if pixel_color[0:3] == (255, 255, 255):
                road_mask_locations.append((x, y))
        except IndexError:  # Na wszelki wypadek, gdyby check_x, check_y były poza granicami maski
            pass

active_coins = []
MAX_ACTIVE_COINS = 10
COIN_SPAWN_INTERVAL = 5000
last_coin_spawn_time = pygame.time.get_ticks()


def spawn_coin():
    global active_coins
    if len(active_coins) < MAX_ACTIVE_COINS and road_mask_locations:
        available_locations = [loc for loc in road_mask_locations if loc not in active_coins]
        if available_locations:
            new_coin_pos = random.choice(available_locations)
            active_coins.append(new_coin_pos)


running = True
while running:
    current_time = pygame.time.get_ticks()
    active_message = None  # Resetuj active_message w każdej klatce

    # --- Aktualizacja animacji monety ---
    if pygame.time.get_ticks() - coin_animation_timer > COIN_ANIMATION_SPEED:
        current_coin_frame_index = (current_coin_frame_index + 1) % len(coin_frames)
        coin_animation_timer = pygame.time.get_ticks()

    active_coin_image = coin_frames[current_coin_frame_index]
    # --- Koniec aktualizacji animacji monety ---

    screen.blit(current_background, (0, 0))

    # Rysowanie interfejsu monet
    coins_text_surf = font.render(f"{coins}", True, BLACK)  # Używamy font, a nie subject_font
    coins_text_rect = coins_text_surf.get_rect(topright=(WIDTH - 10, 10))
    screen.blit(coins_text_surf, coins_text_rect)

    # Rysowanie obrazka monety obok licznika
    coin_display_rect = active_coin_image.get_rect(topright=(
    coins_text_rect.left - 5, coins_text_rect.top + (coins_text_rect.height - active_coin_image.get_height()) // 2))
    screen.blit(active_coin_image, coin_display_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and inside_building:
                inside_building = False
                show_grades = False  # Ukryj oceny przy wyjściu
                current_background = background
                if entry_position:  # Jeśli mamy zapisaną pozycję auta
                    car_x, car_y = entry_position
                velocity_x_char, velocity_y_char = 0, 0  # Reset prędkości postaci

            elif event.key == pygame.K_e:
                player_rect_center_x = character_x + PLAYER_WIDTH // 2
                player_rect_center_y = character_y + PLAYER_HEIGHT // 2
                player_interaction_rect = pygame.Rect(player_rect_center_x - 10, player_rect_center_y - 10, 20,
                                                      20)  # Mniejszy prostokąt interakcji

                if inside_building:
                    # Interakcje wewnątrz budynków
                    target_squares = []
                    if current_background == background1:
                        target_squares = PAYMENTS_SQUARES
                    elif current_background == background2:
                        target_squares = PE_SQUARES_2
                    elif current_background == background3:
                        target_squares = GRADES_SQUARES

                    for sq_info in target_squares:
                        sq_rect = pygame.Rect(sq_info["rect"])
                        if player_interaction_rect.colliderect(sq_rect):
                            if current_background == background3 and sq_info["message"] == "Tablica ocen":
                                show_grades = not show_grades
                                action_message = "Oceny " + ("pokazane" if show_grades else "ukryte")
                            else:
                                action_message = f"{sq_info['message']}: Akcja!"  # Ogólna akcja
                            action_message_time = current_time
                            break  # Tylko jedna interakcja na raz
                elif near_building:  # Wejście do budynku (near_building to krotka (x,y) budynku)
                    inside_building = True
                    entry_position = (car_x, car_y)  # Zapisz pozycję auta

                    # Ustaw tło i pozycję gracza
                    if near_building == buildings[0]:  # Payments
                        current_background = background1
                        character_x, character_y = START_POSITIONS["payments"]
                    elif near_building == buildings[1]:  # PE
                        current_background = background2
                        character_x, character_y = START_POSITIONS["pe_enrollments"]
                    elif near_building == buildings[2]:  # Grades
                        current_background = background3
                        character_x, character_y = START_POSITIONS["grades"]

                    velocity_x_car, velocity_y_car = 0, 0  # Zatrzymaj auto
                    is_moving = False  # Postać nie rusza się przy wejściu
                    current_frame = 0  # Reset animacji postaci

    keys = pygame.key.get_pressed()

    if inside_building:
        # Logika ruchu postaci wewnątrz budynku
        new_velocity_x_char, new_velocity_y_char = velocity_x_char, velocity_y_char

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_velocity_x_char = max(-max_speed_char, new_velocity_x_char - acceleration_char)
            facing = "lewo"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_velocity_x_char = min(max_speed_char, new_velocity_x_char + acceleration_char)
            facing = "prawo"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_velocity_y_char = max(-max_speed_char, new_velocity_y_char - acceleration_char)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_velocity_y_char = min(max_speed_char, new_velocity_y_char + acceleration_char)

        # Spowolnienie (deceleracja)
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if new_velocity_x_char > 0:
                new_velocity_x_char = max(0, new_velocity_x_char - deceleration_char)
            elif new_velocity_x_char < 0:
                new_velocity_x_char = min(0, new_velocity_x_char + deceleration_char)
        if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
            if new_velocity_y_char > 0:
                new_velocity_y_char = max(0, new_velocity_y_char - deceleration_char)
            elif new_velocity_y_char < 0:
                new_velocity_y_char = min(0, new_velocity_y_char + deceleration_char)

        velocity_x_char, velocity_y_char = new_velocity_x_char, new_velocity_y_char
        is_moving = abs(velocity_x_char) > 0.1 or abs(velocity_y_char) > 0.1

        prev_char_x, prev_char_y = character_x, character_y
        character_x += velocity_x_char
        character_y += velocity_y_char

        # Kolizje postaci z maską budynku
        mask_to_check = None
        if current_background == background1:
            mask_to_check = payments_mask
        elif current_background == background2:
            mask_to_check = pe_enrollment_mask
        elif current_background == background3:
            mask_to_check = grades_mask

        if mask_to_check:
            # Sprawdzanie kolizji dla rogów postaci i środka dolnej krawędzi
            # (bardziej zaawansowane niż tylko środek)
            player_points_to_check = [
                (int(character_x + PLAYER_WIDTH * 0.25), int(character_y + PLAYER_HEIGHT * 0.9)),  # lewy dół
                (int(character_x + PLAYER_WIDTH * 0.75), int(character_y + PLAYER_HEIGHT * 0.9)),  # prawy dół
                (int(character_x + PLAYER_WIDTH * 0.5), int(character_y + PLAYER_HEIGHT * 0.95))  # środek dół
            ]
            collision_detected = False
            for p_x, p_y in player_points_to_check:
                if not (0 <= p_x < WIDTH and 0 <= p_y < HEIGHT) or \
                        mask_to_check.get_at((p_x, p_y))[0:3] != (255, 255, 255):
                    collision_detected = True
                    break

            if collision_detected:
                character_x, character_y = prev_char_x, prev_char_y
                velocity_x_char, velocity_y_char = 0, 0  # Zatrzymaj przy kolizji

        character_x = max(0, min(character_x, WIDTH - PLAYER_WIDTH))
        character_y = max(0, min(character_y, HEIGHT - PLAYER_HEIGHT))

        update_animation()
        screen.blit(get_player_image(), (character_x, character_y))

        if current_background == background3 and show_grades:
            handle_grades_display()

        # Sprawdzenie interakcji z kwadratami (dla wyświetlania komunikatu "Nazwa obiektu")
        player_rect_center_x = character_x + PLAYER_WIDTH // 2
        player_rect_center_y = character_y + PLAYER_HEIGHT // 2
        player_interaction_rect = pygame.Rect(player_rect_center_x - 5, player_rect_center_y - 5, 10,
                                              10)  # Mały prostokąt na środku postaci

        target_squares_for_msg = []
        if current_background == background1:
            target_squares_for_msg = PAYMENTS_SQUARES
        elif current_background == background2:
            target_squares_for_msg = PE_SQUARES_2
        elif current_background == background3:
            target_squares_for_msg = GRADES_SQUARES

        for sq_info in target_squares_for_msg:
            if player_interaction_rect.colliderect(pygame.Rect(sq_info["rect"])):
                active_message = sq_info["message"]
                break


    else:  # Poza budynkiem (sterowanie samochodem)
        new_car_direction = car_direction
        new_velocity_x_car, new_velocity_y_car = velocity_x_car, velocity_y_car

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_velocity_x_car = max(-max_speed_car, new_velocity_x_car - acceleration_car)
            new_car_direction = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_velocity_x_car = min(max_speed_car, new_velocity_x_car + acceleration_car)
            new_car_direction = "right"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_velocity_y_car = max(-max_speed_car, new_velocity_y_car - acceleration_car)
            new_car_direction = "up"
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_velocity_y_car = min(max_speed_car, new_velocity_y_car + acceleration_car)
            new_car_direction = "down"

        # Spowolnienie samochodu
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if new_velocity_x_car > 0:
                new_velocity_x_car = max(0, new_velocity_x_car - deceleration_car)
            elif new_velocity_x_car < 0:
                new_velocity_x_car = min(0, new_velocity_x_car + deceleration_car)
        if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
            if new_velocity_y_car > 0:
                new_velocity_y_car = max(0, new_velocity_y_car - deceleration_car)
            elif new_velocity_y_car < 0:
                new_velocity_y_car = min(0, new_velocity_y_car + deceleration_car)

        car_direction = new_car_direction
        velocity_x_car, velocity_y_car = new_velocity_x_car, new_velocity_y_car

        prev_car_x, prev_car_y = car_x, car_y
        car_x += velocity_x_car
        car_y += velocity_y_car

        # Kolizje samochodu z maską drogi
        car_center_x = int(car_x + CAR_SIZE[0] // 2)
        car_center_y = int(car_y + CAR_SIZE[1] // 2)

        if not (0 <= car_center_x < WIDTH and 0 <= car_center_y < HEIGHT) or \
                road_mask.get_at((car_center_x, car_center_y))[0:3] != (255, 255, 255):
            car_x, car_y = prev_car_x, prev_car_y
            velocity_x_car, velocity_y_car = 0, 0  # Zatrzymaj przy kolizji

        car_x = max(0, min(car_x, WIDTH - CAR_SIZE[0]))
        car_y = max(0, min(car_y, HEIGHT - CAR_SIZE[1]))

        # Sprawdzenie bliskości budynku
        near_building = None  # Resetuj w każdej klatce
        car_rect_check = pygame.Rect(car_x, car_y, CAR_SIZE[0], CAR_SIZE[1])
        for b_idx, (bx, by) in enumerate(buildings):
            # Definiujemy obszar wejścia do budynku (np. prostokąt 50x50 przy jego rogu)
            building_entry_rect = pygame.Rect(bx, by, 50, 50)  # Możesz dostosować rozmiar obszaru wejścia
            if car_rect_check.colliderect(building_entry_rect):
                near_building = (bx, by)  # Zapisz koordynaty budynku
                break

        car_image_to_blit = {
            "left": car_left, "right": car_right, "up": car_up, "down": car_down
        }[car_direction]
        screen.blit(car_image_to_blit, (car_x, car_y))

        if near_building:  # Jeśli jesteśmy blisko budynku, który został zidentyfikowany
            text_surf = render_text_with_outline(font, "Wciśnij E", BLACK, YELLOW)
            # Wyświetl tekst nad samochodem
            text_rect_clamped = get_clamped_text_rect(text_surf, (car_x, car_y))
            screen.blit(text_surf, text_rect_clamped)

        # --- Logika monet na mapie głównej ---
        if current_time - last_coin_spawn_time > COIN_SPAWN_INTERVAL:
            spawn_coin()
            last_coin_spawn_time = current_time

        car_collision_rect = pygame.Rect(car_x, car_y, CAR_SIZE[0], CAR_SIZE[1])
        coins_to_remove = []
        for coin_pos_idx, coin_p in enumerate(active_coins):  # Używamy enumerate dla bezpiecznego usuwania
            coin_on_map_rect = active_coin_image.get_rect(topleft=coin_p)
            screen.blit(active_coin_image, coin_on_map_rect)

            if car_collision_rect.colliderect(coin_on_map_rect):
                coins_to_remove.append(coin_p)
                coins += 1

        for collected_coin_pos in coins_to_remove:
            if collected_coin_pos in active_coins:  # Sprawdź, czy moneta wciąż jest na liście
                active_coins.remove(collected_coin_pos)
        # --- Koniec logiki monet ---

    draw_interaction_indicators()

    if active_message:  # Wyświetlanie nazwy obiektu, gdy postać jest blisko w budynku
        text_surf = render_text_with_outline(font, active_message, BLACK, YELLOW)
        # Wyświetl tekst nad postacią
        text_pos_x = character_x + PLAYER_WIDTH // 2
        text_pos_y = character_y - 10  # Nad głową postaci
        text_rect_clamped = get_clamped_text_rect(text_surf, (
        text_pos_x - 30, text_pos_y + 20))  # Korekta, bo get_clamped_text_rect dodaje offset
        screen.blit(text_surf, text_rect_clamped)

    if action_message and (current_time - action_message_time) < 2000:
        text_surf = render_text_with_outline(font, action_message, BLACK, YELLOW, 2)  # Grubszy obrys
        text_rect = text_surf.get_rect(center=(WIDTH // 2, 50))  # Na górze, na środku
        screen.blit(text_surf, text_rect)
    elif action_message and (current_time - action_message_time) >= 2000:
        action_message = None  # Wyczyść wiadomość po czasie

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()