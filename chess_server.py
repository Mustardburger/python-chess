from pygame import color
from chessboard import Chessboard
import socket
from _thread import *
import threading
import pickle
import util
import random
import chessPieces as cp

SERVER = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

game_id = 0
games = {
    "standard": {}, "960": {}, "hab": {}, "blind": {}
}
game_types_num_player = {
    "standard": 0, "960": 0, "hab": 0, "blind": 0
}
game_types_waiting_players = {
    "standard": [], "960": [], "hab": [], "blind": []
}
games_id_players_id = {
    "standard": {}, "960": {}, "hab": {}, "blind": {}
}
games_id_players_colors = {
    "standard": {}, "960": {}, "hab": {}, "blind": {}
}
games_hab_id_players_role = {}
games_hab_id_current_turn = {}
games_id_results = {
    "standard": {}, "960": {}, "hab": {}, "blind": {}
}

players = {}
players_in_lobby = {}
current_num_player = 0
thread_lock = threading.Lock()


def _initialize_hab_game(game_id, curr_player_id):
    """ A helper function to initialize the info about the game """

    # Add a new game to the dicts
    if game_id not in games_id_players_colors["hab"]:
        games_id_players_colors["hab"][game_id] = {}
    if game_id not in games_hab_id_players_role:
        games_hab_id_players_role[game_id] = {}

    # if enough players for the game_id then return
    if len(games_hab_id_players_role[game_id]) == 4:
        return 1

    # Choose what color the current player is
    if curr_player_id not in games_id_players_colors["hab"][game_id]:
        avail_colors = list(
            games_id_players_colors["hab"][game_id].values())
        num_white_players = len(
            [player_color for player_color in avail_colors if player_color == "white"])
        num_black_players = len(avail_colors) - num_white_players
        # already 2 white players then remaining players should be black
        if num_white_players == 2:
            current_color = "black"
        # already 2 black players then remaining players should be white
        elif num_black_players == 2:
            current_color = "white"
        # if not, then randomly choose a color
        else:
            current_color = random.choice(["white", "black"])
        # add the new player and his color to the dict
        games_id_players_colors["hab"][game_id][curr_player_id] = current_color

    # Choose whether a player is the hand or the brain
    current_role = None
    if curr_player_id not in games_hab_id_players_role[game_id]:
        # Loop through color dict to find who has the same color
        for p_id, p_color in games_id_players_colors["hab"][game_id].items():
            if p_color == current_color and p_id != curr_player_id:
                p_role = games_hab_id_players_role[game_id][p_id]
                current_role = "hand" if p_role == "brain" else "brain"
                games_hab_id_players_role[game_id][curr_player_id] = current_role
        # after the loop, if cannot find partner, then randomly choose
        if not(current_role):
            current_role = random.choice(["hand", "brain"])
            games_hab_id_players_role[game_id][curr_player_id] = current_role


def _hand_reply(conn, game_id, curr_player_id, message, chessboard):
    """ Handle the message from the hand """

    # Asking the server which piece the brain has chosen
    try:
        if "command" in message:
            color_to_check = message["color"]

            # if at current turn is the same as color_to_check and the brain has also picked a piece
            if game_id in games_hab_id_current_turn:
                if games_hab_id_current_turn[game_id]["role"] == "brain" and "piece" in games_hab_id_current_turn[game_id]:
                    piece_from_brain = games_hab_id_current_turn[game_id]["piece"]
                    # the piece from the brain has valid moves
                    if chessboard._check_selected_piece_by_brain(piece_from_brain, color_to_check):
                        games_hab_id_current_turn[game_id] = {
                            "color": color_to_check, "role": "hand"}
                        conn.sendall(pickle.dumps(piece_from_brain))
                    else:
                        conn.sendall(pickle.dumps("No1"))
                        return False
                # else then send a "no" message to the hand
                else:
                    conn.sendall(pickle.dumps("No2"))
                    return False
            else:
                conn.sendall(pickle.dumps("No3"))
                return False
        else:
            conn.sendall(pickle.dumps("No4"))
            return False

    except Exception as e:
        print("[SERVER] Error in processing the hand message")
        print(e)


def _brain_reply(conn, game_id, curr_player_id, message, chessboard):
    """ Handle the message from the brain """

    try:
        color_piece = message["color"]
        piece_to_check = message["piece"]

        # Check if there is a piece similar to piece_to_check that can be moved by the hand
        if piece_to_check in ["pawn", "knight", "bishop", "rook", "queen", "king"]:
            if chessboard._check_selected_piece_by_brain(piece_to_check, color_piece):
                games_hab_id_current_turn[game_id] = {
                    "color": color_piece, "role": "brain", "piece": piece_to_check}

                # Sending that the piece has been recorded
                conn.sendall(pickle.dumps("Okay"))
            else:
                conn.sendall(pickle.dumps("Brain No"))

        # else then send the piece has not been recorded
        else:
            conn.sendall(pickle.dumps("Brain No"))

    except Exception as e:
        print("[SERVER] Error in processing the brain message")
        print(e)


def start_game_hab(conn, mode, game_id, players_id, curr_player_id):
    """ Start a hab game on the server """

    # Start a new game
    # Create an instance of the chessboard on the server
    if game_id not in games[mode]:
        current_game = Chessboard()
        games[mode][game_id] = current_game
    else:
        current_game = games[mode][game_id]
    game_end = None
    games_hab_id_current_turn[game_id] = {
        "color": "white", "role": "brain", "piece": "empty"}

    # Initialize result dict
    games_id_results[mode][game_id] = {}

    # Find some information about color, role, and id of friend
    _ = pickle.loads(conn.recv(4096))
    current_color = games_id_players_colors[mode][game_id][curr_player_id]
    current_role = games_hab_id_players_role[game_id][curr_player_id]
    friend_id = None

    # Find opponent ids
    opponent_ids = []
    for id, color in games_id_players_colors[mode][game_id].items():
        if color != current_color:
            opponent_ids.append(id)
        elif id != curr_player_id:
            friend_id = id

    # Find name of each opponent
    for id in opponent_ids:
        if games_hab_id_players_role[game_id][id] == "hand":
            opponent_hand_name = players[id]
        else:
            opponent_brain_name = players[id]

    print("[SERVER] Player id to player name: ", players)
    print("[SERVER] Ground truth information: ",
          games_hab_id_players_role[game_id])

    info_to_send_hab = {
        "opponent_hand_name": opponent_hand_name, "opponent_brain_name": opponent_brain_name,
        "friend_name": players[friend_id],
        "curr_color": current_color,
        "curr_role": current_role
    }
    conn.sendall(pickle.dumps(info_to_send_hab))

    # The main game loop
    while True:
        try:
            # The server receives a notification from one of the player
            message_received = pickle.loads(conn.recv(4096))
            #print("[SERVER] Message received: ", message_received)
            # thread_lock.acquire()
            try:
                # thread_lock.acquire()
                # Game has ended and player returns back to lobby
                if message_received == "!back_lobby":
                    # Send a noti back to the client
                    conn.sendall(pickle.dumps("OK"))
                    # Variables to update
                    # TODO
                    # thread_lock.release()
                    return 1

                if message_received != "wait":
                    role = message_received["role"]

                    # The message is from the brain (giving the server a piece)
                    # The server should only process the info when the current player has same color has game current turn
                    if role == "brain" and isinstance(message_received, dict):
                        #print("[SERVER] Current role is brain")
                        if message_received["color"] == current_game.turn:
                            _brain_reply(conn, game_id, curr_player_id,
                                         message_received, current_game)
                        else:
                            conn.sendall(pickle.dumps("Brain No"))

                    # The message is from the hand
                    if role == "hand" and isinstance(message_received, dict):

                        #print("[SERVER] Current role is hand")
                        if message_received["color"] == current_game.turn:
                            hand_received_piece_from_brain = _hand_reply(conn, game_id, curr_player_id,
                                                                         message_received, current_game)
                        else:
                            hand_received_piece_from_brain = False
                            conn.sendall(pickle.dumps("No"))
                        #print("[SERVER] Move made? ", move_made)

                        # if the message from the hand contains the key command, then the hand is just
                        # asking for the piece from the brain and nothing more
                        if "command" in message_received:
                            pass

                        # Asking the server to make a move
                        else:
                            pass

                        # conn.sendall(pickle.dumps("No"))

                # thread_lock.release()

                # Think carefully what to send back
                try:
                    message_received = pickle.loads(conn.recv(4096))
                    #print("[SERVER] Message received (2): ", message_received)
                    # A player sends a resignation
                    if message_received == "resign":
                        games_id_results[mode][game_id][curr_player_id] = "lose"
                        games_id_results[mode][game_id][friend_id] = "lose"
                        for id in opponent_ids:
                            games_id_results[mode][game_id][id] = "win"
                        game_end = "resignation"

                    elif message_received == "wait":
                        pass

                    elif role == "hand" and isinstance(message_received, dict):
                        # Asking the server to make a move
                        color_to_check = message_received["color"]
                        piece_to_move_coor = message_received["piece"]
                        move = message_received["move"]

                        # Extract the piece
                        y, x = piece_to_move_coor
                        piece = current_game.board[y][x]

                        # Check if that move is actually valid
                        current_possible_moves_all = current_game.find_all_possible_moves(
                            color_to_check)
                        if piece_to_move_coor in current_possible_moves_all:
                            possible_moves_by_piece = current_possible_moves_all[piece_to_move_coor]
                            if move in possible_moves_by_piece:
                                move_valid = True
                            else:
                                move_valid = False
                        else:
                            move_valid = False

                        # Update the chessboard on the server (if the move is valid and game has not ended)
                        if move_valid:
                            if isinstance(piece, cp.Piece):
                                if piece.name == "king":
                                    opponent_color = "white" if current_color == "black" else "black"
                                    opponent_attack_squares_list = util.unravel(
                                        list(current_game.attack_squares[opponent_color].values()))
                                    avail_moves_by_piece = piece.avail_moves(
                                        current_game.board, piece_to_move_coor, None, opponent_attack_squares_list)
                                else:
                                    avail_moves_by_piece = piece.avail_moves(
                                        current_game.board, piece_to_move_coor)

                                current_game.make_move_from_selected_square(
                                    avail_moves_by_piece, piece_to_move_coor, move, True)

                                # After hand makes a move
                                games_hab_id_players_role[game_id] = {
                                    "color": color_to_check, "role": role}

                            games[mode][game_id] = current_game
                        else:
                            pass

                    packed_data_dict = {
                        "game": current_game, "time": None, "pgn": current_game.pgn, "curr_turn": current_game.turn
                    }
                    conn.sendall(pickle.dumps(packed_data_dict))

                except Exception as e:
                    print("[SERVER] (3) An error occured when processing messages")
                    print(e)

                # When the game ends (checkmate, stalemate, draw, or run out of time)
                avail_moves_after_making_move = current_game.find_all_possible_moves(
                    current_game.turn)
                if isinstance(avail_moves_after_making_move, int):
                    # Checkmate
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] The game ends")
                    if avail_moves_after_making_move == -100:
                        game_end = "checkmate"
                    elif avail_moves_after_making_move == -50:
                        game_end = "stalemate"

            except Exception as e:
                print("[SERVER] (1) There's an error somewhere")
                print(e)

            # Update the timer
            # TODO

            # Pack everything and send to the players. The data sent includes a Chessboard object
            # remaining time from each player, the pgn, and possibly the current turn

            # The game has not finished
            if not(game_end) and not(games_id_results[mode][game_id]):
                pass
                # conn.sendall(pickle.dumps(packed_data_dict))
            else:
                # If stalemate or draw then both sides draw
                #print("[SERVER] Game ends")
                # print(
                #    f"[SERVER, sent to {players[curr_player_id]}] Try sending ending game noti")
                if game_end == "stalemate":
                    conn.sendall(pickle.dumps("stalemate"))
                elif game_end == "draw":
                    conn.sendall(pickle.dumps("draw"))
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] Ending game noti sent")

                # Check who wins and who loses
                elif game_end == "checkmate":
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] The game ends in checkmate")
                    current_color = games_id_players_colors[mode][game_id][curr_player_id]
                    if current_color == current_game.turn:
                        games_id_results[mode][game_id][curr_player_id] = "lose"
                        conn.sendall(pickle.dumps("checkmate,lose"))
                    else:
                        games_id_results[mode][game_id][curr_player_id] = "win"
                        conn.sendall(pickle.dumps("checkmate,win"))
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] Ending game noti sent")

                # Game ends by resignation
                elif game_end == "resignation" or games_id_results[mode][game_id]:
                    if games_id_results[mode][game_id][curr_player_id] == "lose":
                        conn.sendall(pickle.dumps("You lost by resignation"))
                    else:
                        conn.sendall(pickle.dumps("You won by resignation"))

                # An error case
                else:
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] Hi there!")
                    conn.sendall(pickle.dumps("Hi,there"))

                pass
            # thread_lock.release()

        except Exception as e:
            print(
                f"[SERVER, sent to {players[curr_player_id]}] There's an error")
            print(e)

# yo
# yo
# yo
# yo
# yo


def start_game(conn, mode, game_id, players_id, curr_player_id):
    """ Start the game on the server """

    # Create an instance of the chessboard on the server
    if game_id not in games[mode]:
        if mode == "standard":
            current_game = Chessboard()
        elif mode == "960":
            current_game = Chessboard(False, False, True)
        games[mode][game_id] = current_game
    else:
        current_game = games[mode][game_id]

    # Initialize result dict
    games_id_results[mode][game_id] = {}

    # Terminal game message
    game_end = None

    # Extracting name of opponent and color
    # Send the name of the opponent to the player
    conn.recv(4096).decode()
    if players_id[0] != curr_player_id:
        opponent_id = players_id[0]
    else:
        opponent_id = players_id[1]
    opponent_name = players[opponent_id]
    conn.send(pickle.dumps(opponent_name))

    # Randomly assign which player is Black and which is White, then send the info back to the player
    conn.recv(4096).decode()
    if game_id not in games_id_players_colors[mode]:
        games_id_players_colors[mode][game_id] = {}
        white_player = random.choice(players_id)
        if white_player == curr_player_id:
            conn.send(pickle.dumps("white"))
            current_color = "white"
            games_id_players_colors[mode][game_id][curr_player_id] = "white"
        else:
            conn.send(pickle.dumps("black"))
            current_color = "black"
            games_id_players_colors[mode][game_id][curr_player_id] = "black"
    else:
        chosen_color = list(
            games_id_players_colors[mode][game_id].values())[0]
        remaining_color = "white" if chosen_color == "black" else "black"
        current_color = remaining_color
        games_id_players_colors[mode][game_id][curr_player_id] = current_color
        conn.send(pickle.dumps(remaining_color))

    # The main game loop
    while True:
        try:
            # The server receives a move from one of the player
            message_received = pickle.loads(conn.recv(4096))
            try:
                # Game has ended and player returns back to lobby
                if message_received == "!back_lobby":
                    # Send a noti back to the client
                    conn.sendall(pickle.dumps("OK"))
                    # Variables to update
                    return 1

                thread_lock.acquire()
                if message_received != "wait":
                    if len(message_received) == 3 and isinstance(message_received, dict):
                        color_to_check = message_received["turn"]
                        piece_to_move_coor = message_received["piece"]
                        move = message_received["move"]

                        # Check if that move is actually valid
                        current_possible_moves_all = current_game.find_all_possible_moves(
                            color_to_check)
                        if piece_to_move_coor in current_possible_moves_all:
                            possible_moves_by_piece = current_possible_moves_all[piece_to_move_coor]
                            if move in possible_moves_by_piece:
                                move_valid = True
                            else:
                                move_valid = False
                        else:
                            move_valid = False
                        #print("[SERVER] Check move complete")

                        # Update the chessboard on the server (if the move is valid and game has not ended)
                        if move_valid:
                            y, x = piece_to_move_coor
                            piece = current_game.board[y][x]
                            if isinstance(piece, cp.Piece):
                                if piece.name == "king":
                                    opponent_color = "white" if current_color == "black" else "black"
                                    opponent_attack_squares_list = util.unravel(
                                        list(current_game.attack_squares[opponent_color].values()))
                                    avail_moves_by_piece = piece.avail_moves(
                                        current_game.board, piece_to_move_coor, None, opponent_attack_squares_list)
                                else:
                                    avail_moves_by_piece = piece.avail_moves(
                                        current_game.board, piece_to_move_coor)

                                current_game.make_move_from_selected_square(
                                    avail_moves_by_piece, piece_to_move_coor, move, True)
                            games[mode][game_id] = current_game
                        else:
                            pass

                        # For debugging: print board to terminal
                        #print("[SERVER] Print board")
                        # current_game.print_board_terminal()

                    # A player sends a resignation
                    elif message_received == "resign":
                        games_id_results[mode][game_id][curr_player_id] = "lose"
                        games_id_results[mode][game_id][opponent_id] = "win"
                        game_end = "resignation"

                packed_data_dict = {
                    "game": current_game, "time": None, "pgn": current_game.pgn, "curr_turn": current_game.turn
                }
                conn.sendall(pickle.dumps(packed_data_dict))

                # When the game ends (checkmate, stalemate, draw, or run out of time)
                avail_moves_after_making_move = current_game.find_all_possible_moves(
                    current_game.turn)
                if isinstance(avail_moves_after_making_move, int):
                    # Checkmate
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] The game ends")
                    if avail_moves_after_making_move == -100:
                        game_end = "checkmate"
                    elif avail_moves_after_making_move == -50:
                        game_end = "stalemate"

            except:
                pass
                #print("[SERVER] The move format is not correct")

            # Update the timer
            # TODO

            # Pack everything and send to the players. The data sent includes a Chessboard object
            # remaining time from each player, the pgn, and possibly the current turn

            # The game has not finished
            if not(game_end) and not(games_id_results[mode][game_id]):
                pass
                # conn.sendall(pickle.dumps(packed_data_dict))
            else:
                # If stalemate or draw then both sides draw
                #print("[SERVER] Game ends")
                # print(
                #    f"[SERVER, sent to {players[curr_player_id]}] Try sending ending game noti")
                if game_end == "stalemate":
                    conn.sendall(pickle.dumps("stalemate"))
                elif game_end == "draw":
                    conn.sendall(pickle.dumps("draw"))
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] Ending game noti sent")

                # Check who wins and who loses
                elif game_end == "checkmate":
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] The game ends in checkmate")
                    current_color = games_id_players_colors[mode][game_id][curr_player_id]
                    if current_color == current_game.turn:
                        games_id_results[mode][game_id][curr_player_id] = "lose"
                        conn.sendall(pickle.dumps("checkmate,lose"))
                    else:
                        games_id_results[mode][game_id][curr_player_id] = "win"
                        conn.sendall(pickle.dumps("checkmate,win"))
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] Ending game noti sent")

                # Game ends by resignation
                elif game_end == "resignation" or games_id_results[mode][game_id]:
                    if games_id_results[mode][game_id][curr_player_id] == "lose":
                        conn.sendall(pickle.dumps("You lost by resignation"))
                    else:
                        conn.sendall(pickle.dumps("You won by resignation"))

                # An error case
                else:
                    print(
                        f"[SERVER, sent to {players[curr_player_id]}] Hi there!")
                    conn.sendall(pickle.dumps("Hi,there"))

                pass
            thread_lock.release()

        except Exception as e:
            print(
                f"[SERVER, sent to {players[curr_player_id]}] There's an error")
            print(e)


def mode_login(conn, player_id, mode):
    """ Allows a player to login a specific mode """

    current_player_name = players[player_id]
    if mode == "hab":
        min_num_players_to_start_game = 4
    else:
        min_num_players_to_start_game = 2

    if player_id not in game_types_waiting_players[mode]:
        if player_id not in util.unravel(list(games_id_players_id[mode].values())):
            print("[SERVER] Unravelled list: ", util.unravel(
                list(games_id_players_id[mode].values())))
            game_types_waiting_players[mode].append(
                player_id)
            game_types_num_player[mode] += 1

            print("[SERVER] Num of players in the game mode: ",
                  game_types_num_player[mode])

            # Game does not have enough player yet
            if game_types_num_player[mode] % min_num_players_to_start_game != 0:
                conn.sendall(pickle.dumps("!wait"))

    if game_types_num_player[mode] % min_num_players_to_start_game == 0:

        # thread_lock.acquire()
        # Start a new game
        reply = "!wait"
        #print("[SERVER] Start a new game")

        # Create a new game id (need fix)
        # TODO
        game_id = (game_types_num_player[mode] //
                   min_num_players_to_start_game) + 1

        # Assign the players in waiting queue to this specified game ID
        if len(game_types_waiting_players[mode]) == min_num_players_to_start_game:
            games_id_players_id[mode][game_id] = game_types_waiting_players[mode].copy(
            )
            # print(
            #   f"[SERVER] Game {game_id} starts with players {game_types_waiting_players[mode]}")

        # Return the name of the opponent
        if mode != "hab":
            # For 2-player mode like Standard, 960, and Blind
            for id in games_id_players_id[mode].keys():
                if player_id in games_id_players_id[mode][id]:
                    for p in games_id_players_id[mode][id]:
                        name = players[p]
                        if name != current_player_name:
                            opponent_name = name
                            reply = opponent_name
                    break
        else:
            # For 4-player mode (hab)
            try:
                _initialize_hab_game(game_id, player_id)
                # print(
                #   f"[SERVER, sent to {players[player_id]}]: ", games_hab_id_players_role[game_id])

            except Exception as e:
                print("[SERVER] Error caught")
                print(e)

        # Remove the players from the waiting queue and the lobby after they join a game
        thread_lock.acquire()
        try:
            # print(
            #   "[SERVER] Players in lobby before removing: ", players_in_lobby)
            # print(
            #   "[SERVER] Players in queue for waiting before removing: ", game_types_waiting_players)

            # For hab mode
            if mode == "hab":
                if len(games_hab_id_players_role[game_id]) == min_num_players_to_start_game:
                    if player_id in players_in_lobby:
                        del players_in_lobby[player_id]
                    if player_id in game_types_waiting_players[mode]:
                        game_types_waiting_players[mode].remove(
                            player_id)
            else:
                # Remove the player from the lobby
                key_to_del = util.from_value_to_key(
                    players_in_lobby, opponent_name)
                del players_in_lobby[key_to_del]
                game_types_waiting_players[mode].remove(
                    key_to_del)

            # print(
             #   "[SERVER] Players in lobby after removing: ", players_in_lobby)
            # print(
             #   "[SERVER] Players in queue for waiting after removing: ", game_types_waiting_players)
        except Exception as e:
            print(
                "[SERVER] There is an error in removing player from lobby")
            print(e)
        thread_lock.release()

        # Send the opponent's name
        if mode != "hab":
            conn.sendall(pickle.dumps(reply))
        # thread_lock.release()

        # Conditions tp start the game
        # thread_lock.acquire()
        if mode != "hab":
            back_to_lobby = start_game(conn, mode, game_id,
                                       games_id_players_id[mode][game_id], player_id)
        else:
            if len(games_hab_id_players_role[game_id]) == min_num_players_to_start_game:
                #print("[SERVER] Start new hab game")
                conn.sendall(pickle.dumps(
                    games_hab_id_players_role[game_id][player_id]))
                back_to_lobby = start_game_hab(conn, mode, game_id,
                                               games_id_players_id[mode][game_id], player_id)
            else:
                conn.sendall(pickle.dumps("yo"))
        # thread_lock.release()

        # After they finish the game and return back to lobby
        if (back_to_lobby == 1):
            # Add that player to lobby
            players_in_lobby[player_id] = current_player_name
            # Remove that player from games_id_players_id
            games_id_players_id[mode][game_id].remove(player_id)
            # if with that game id no players left (in Standard, 960, and Blind) then delete that game id
            # and any info that is associated with that game
            if len(games_id_players_id[mode][game_id]) == 0:
                del games_id_players_id[mode][game_id]
                del games[mode][game_id]
                del games_id_results[mode][game_id]
                del games_id_players_colors[mode][game_id]

    else:
        conn.sendall(pickle.dumps("!wait"))

    return 0


def threaded_clients(conn, player_id):
    """
    Handle the requests from each player logging in the server
    Some specific commands:
        - None 
    """
    global current_num_player
    # A message that confirms the connection
    try:
        conn.send(str.encode("Connected!"))
        lobby = True
    except:
        lobby = False

    # If connected, then server receives the name from the user

    # For each player, there are 2 waiting loops
    # The first is when the player enters the lobby but has not got any pairing
    # The second is when the players get the pairing and start the game
    # When the game is finished, the players get out of their game loop and enter the lobby loop
    # When they quit the game, they get out of the lobby loop, and the connection is closed

    reply = ""
    current_player_name = None
    current_game_type = None

    while lobby:
        try:
            command_received = conn.recv(2048).decode()

            if not command_received:
                print("Player disconnected")
                break

            elif command_received == "!standard":
                # Put the player to a standard game room

                # Conditions to register a new player:
                # If the player is not waiting in the waiting queue (game_types_waiting_players)
                # If the player is not in the waiting queue, but already has an opponent, then skip
                _ = mode_login(conn, player_id, "standard")

            elif command_received == "!960":
                # Put the player to a chess960 game room
                _ = mode_login(conn, player_id, "960")

            elif command_received == "!hab":
                # Put the player to a hand-and-brain game room
                _ = mode_login(conn, player_id, "hab")
            elif command_received == "!blind":
                # Put the player to a blind game room
                pass
            elif command_received == "!get_player":
                # The player wants a list of current online players
                reply = players_in_lobby
                conn.sendall(pickle.dumps(reply))
            else:
                # New player signs in and sends a name
                current_player_name = command_received
                players[player_id] = current_player_name
                players_in_lobby[player_id] = current_player_name
                reply = "OK"
                conn.sendall(pickle.dumps(reply))

        except:
            pass

    # When a player disconnects, update the following

    # Remove the player from the dict of players and the dict of players in lobby
    key_to_del = util.from_value_to_key(
        players, current_player_name)
    del players[key_to_del]
    del players_in_lobby[key_to_del]
    print("[SERVER] Player dict after someone logged off: ", players)

    # Reduce the total number of players
    current_num_player -= 1

    # Remove the num of player in a game type (if there is any)
    if current_game_type:
        game_types_num_player[current_game_type] -= 1
        if player_id in game_types_waiting_players[current_game_type]:
            game_types_waiting_players[current_game_type].remove(player_id)

    # Close connection
    conn.close()


def start():
    """ Start the server """
    global current_num_player
    player_id = 0
    game_id = 0
    server.listen()
    print("[SERVER] Server is listening to new players")

    while True:
        # Listen to a new player connecting
        conn, addr = server.accept()
        print("Connected to: ", addr)
        current_num_player += 1
        player_id += 1
        game_id += 1
        print(f"Current number of players in the lobby: {current_num_player}")

        # Start a thread for the new player
        #p = threading.Thread(target=threaded_clients, args=(conn, player_id))
        # p.start()
        start_new_thread(threaded_clients, (conn, player_id))
        # If num_player is divisible by 2, then start ordinary game
        # If num_player is divisible by 4, then start hand and brain game


if __name__ == "__main__":
    print("[SERVER] Server is starting")
    start()

    # For debugging
    """
    g_id = 1
    player_id_list = [1, 2, 3, 4]
    for i in player_id_list:
        _initialize_hab_game(g_id, i)
    print(games_hab_id_players_role)
    """
