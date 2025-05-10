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
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background1 = pygame.image.load("background1.png")
background1 = pygame.transform.scale(background1, (WIDTH, HEIGHT))
background2 = pygame.image.load("background2.png")
background2 = pygame.transform.scale(background2, (WIDTH, HEIGHT))

# Wczytanie maski kolizji
road_mask = pygame.image.load("maskbackground.png").convert()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))

# Wczytanie pojazdu i ludka
car = pygame.image.load("car.png")
car = pygame.transform.scale(car, (50, 50))
player = pygame.image.load("character.png")
player = pygame.transform.scale(player, (50, 50))

# Pozycja początkowa i zmienne
car_x, car_y = 400, 300
speed = 5
buildings = [(100, 0), (730, 225)]
current_background = background
inside_building = False
entry_position = None  # Pozycja auta przed wejściem do budynku
near_building = False  # Flaga informująca, czy gracz jest blisko budynku
font = pygame.font.Font(None, 36)  # Czcionka dla tekstu

def draw_squares():
    """Rysuje czerwone prostokąty jako punkty wejścia do budynków."""
    if not inside_building:
        pygame.draw.rect(screen, RED, (100, 0, 50, 50))  # Punkt wejścia 1
        pygame.draw.rect(screen, RED, (730, 225, 50, 50))  # Punkt wejścia 2

running = True
while running:
    screen.blit(current_background, (0, 0))
    draw_squares()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and inside_building:
                # Wyjście z budynku
                inside_building = False
                current_background = background
                if entry_position:
                    car_x, car_y = entry_position  # Przywróć pozycję samochodu sprzed wejścia
            elif event.key == pygame.K_e and near_building and not inside_building:
                # Wejście do budynku po wciśnięciu "E"
                inside_building = True
                car_x, car_y = WIDTH // 2, HEIGHT // 2  # Przenieś postać do środka budynku
                if near_building == (100, 0):
                    current_background = background1
                elif near_building == (730, 225):
                    current_background = background2

    keys = pygame.key.get_pressed()
    new_x, new_y = car_x, car_y

    if inside_building:
        # Ruch postaci w budynku
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed
        car_x, car_y = new_x, new_y  # Aktualizuj pozycję postaci w budynku
    else:
        # Ruch samochodu na zewnątrz
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += speed

        # Sprawdzenie kolizji z maską drogi
        if road_mask.get_at((new_x + 25, new_y + 25)) == (255, 255, 255, 255):
            car_x, car_y = new_x, new_y

        entry_position = (car_x, car_y)  # Zapisz pozycję samochodu przed wejściem
        near_building = None  # Resetowanie flagi

        # Sprawdzanie, czy gracz jest blisko budynku
        for building in buildings:
            if (building[0] - 25 <= car_x <= building[0] + 25 and
                building[1] - 25 <= car_y <= building[1] + 25):
                near_building = building  # Zapamiętaj, że gracz jest przy budynku
                break

    # Rysowanie pojazdu lub ludka
    if inside_building:
        screen.blit(player, (car_x, car_y))  # Postać w budynku
    else:
        screen.blit(car, (car_x, car_y))  # Samochód na zewnątrz

        if near_building:
            text = font.render("Wciśnij E, aby wejść", True, BLACK)

            # Pobranie szerokości i wysokości tekstu
            text_width, text_height = text.get_size()

            # Korekta pozycji, jeśli tekst wychodzi poza ekran
            text_x = max(0, min(car_x - 50, WIDTH - text_width))
            text_y = max(0, min(car_y - 40, HEIGHT - text_height))

            # Wyświetlenie tekstu w poprawnej pozycji
            screen.blit(text, (text_x, text_y))

    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()
