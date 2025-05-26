import socket
import pickle
import threading

# Konfiguracja serwera
SERVER_HOST = "127.0.0.1"  # Nasłuchuj na wszystkich dostępnych interfejsach
SERVER_PORT = 5555
BUFFER_SIZE = 4096 # Rozmiar bufora dla odbieranych danych, można dostosować

# Przechowywanie danych graczy (klucz: adres klienta, wartość: dane gracza)
# Dane gracza mogą być słownikiem, np. {'id': id, 'x': x, 'y': y, 'color': color, ...}
players_data = {}
player_id_counter = 0
lock = threading.Lock() # Do synchronizacji dostępu do players_data

def handle_client(client_socket, client_address):
    global player_id_counter
    print(f"[NOWE POŁĄCZENIE] Połączono z {client_address}")

    with lock:
        current_player_id = player_id_counter
        player_id_counter += 1
        # Inicjalne dane gracza - klient może je zaktualizować
        # Kolor można przypisać na serwerze lub klient może go wybrać
        initial_player_state = {
            "id": current_player_id,
            "x": 50, # Pozycja startowa X
            "y": 50, # Pozycja startowa Y
            "color": (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
            "message": "Połączono"
        }
        players_data[client_address] = initial_player_state

    # Wyślij ID do klienta zaraz po połączeniu
    try:
        client_socket.send(pickle.dumps({"id": current_player_id, "initial_state": players_data[client_address]}))
    except socket.error as e:
        print(f"[BŁĄD WYSYŁANIA ID] {e}")
        # Zakończ obsługę tego klienta jeśli nie można wysłać ID
        if client_address in players_data:
            with lock:
                del players_data[client_address]
        client_socket.close()
        return

    connected = True
    while connected:
        try:
            # Odbierz dane od klienta
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                print(f"[ROZŁĄCZONO] {client_address} rozłączył się (brak danych).")
                break # Klient zamknął połączenie

            received_player_state = pickle.loads(data)
            # print(f"[ODEBRANO OD {client_address}] {received_player_state}")

            # Zaktualizuj dane tego gracza
            with lock:
                if client_address in players_data: # Upewnij się, że klient wciąż istnieje
                    players_data[client_address].update(received_player_state)
                else:
                    # To nie powinno się zdarzyć jeśli klient nie został usunięty wcześniej
                    print(f"[OSTRZEŻENIE] Otrzymano dane od nieznanego klienta {client_address}")
                    continue

            # Przygotuj dane wszystkich graczy do wysłania
            # Wysyłamy listę słowników, a nie słownik słowników, aby ułatwić iterację po stronie klienta
            with lock:
                all_players_list = list(players_data.values())

            # Wyślij zaktualizowany stan gry do *tego* klienta
            # Można też wysyłać do wszystkich, ale wtedy każdy klient dostaje też swoje dane
            # Dla uproszczenia, wysyłamy pełny stan do każdego
            client_socket.sendall(pickle.dumps(all_players_list))
            # print(f"[WYSŁANO DO {client_address}] Stan wszystkich graczy")

        except socket.error as e:
            print(f"[BŁĄD SOCKETU] {client_address}: {e}")
            break # Błąd komunikacji, zakończ pętlę
        except pickle.PickleError as e:
            print(f"[BŁĄD DESERIALIZACJI] {client_address}: {e}")
            # Możliwe uszkodzone dane, kontynuuj lub rozłącz
            continue
        except EOFError:
             print(f"[ROZŁĄCZONO] {client_address} zamknął połączenie (EOF).")
             break
        except Exception as e:
            print(f"[NIEOCZEKIWANY BŁĄD] {client_address}: {e}")
            break

    # Sprzątanie po rozłączeniu klienta
    print(f"[ROZŁĄCZONO] {client_address} zakończył połączenie.")
    with lock:
        if client_address in players_data:
            del players_data[client_address]
    client_socket.close()


import random # Dla kolorów graczy

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Umożliwia ponowne użycie adresu natychmiast po zamknięciu serwera
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((SERVER_HOST, SERVER_PORT))
    except socket.error as e:
        print(f"[BŁĄD BINDOWANIA] Nie udało się zbindować adresu {SERVER_HOST}:{SERVER_PORT} - {e}")
        return

    server_socket.listen()
    print(f"[NASŁUCHIWANIE] Serwer nasłuchuje na {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            # Uruchom nowy wątek do obsługi klienta
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.daemon = True # Wątek zakończy się, gdy główny program się zakończy
            thread.start()
            print(f"[AKTYWNE POŁĄCZENIA] {threading.active_count() - 1}") # -1 bo główny wątek
    except KeyboardInterrupt:
        print("\n[ZAMYKANIE] Serwer jest zamykany...")
    finally:
        server_socket.close()
        print("[ZAMKNIĘTY] Serwer został zamknięty.")

if __name__ == "__main__":
    main()

