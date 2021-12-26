import chessPieces as cp
import util
import random
import copy


class Chessboard():
    def __init__(self, standard=True, custom=False, chess960=False):
        """
        Initialize the board
        """
        # Variables of the board
        self.turn = "white"   # "white" for White, "black" for Black
        self.current_chosen_square = None     # Current selected piece
        self.pgn = []       # Pgn of the game
        self.num_of_moves = 0
        self.prev_board_states = []     # used to check 3-fold repetition
        self.chess960 = chess960

        # Coors of pieces and squares
        self.pieces_coor = {
            "black": {
                "pawn": [], "knight": [], "bishop": [], "rook": [], "queen": [], "king": []
            },
            "white": {
                "pawn": [], "knight": [], "bishop": [], "rook": [], "queen": [], "king": []
            }
        }
        self.possible_moves = {
            "black": {},
            "white": {}
        }
        self.attack_squares = {
            "white": {},
            "black": {}
        }

        # If standard mode
        if standard:
            # FEN for starting position
            self.standard_starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            #self.standard_starting_fen = "rnbqkbn1/5r2/1p6/p1p1p1p1/P1P1P1Pp/3QpPPP/1N2B3/R1BK2NR w KQq - 0 1"
        elif chess960:
            heavy_pieces = "rnbqkbnr"
            l = list(heavy_pieces)
            random.shuffle(l)
            heavy_pieces_shuffled = ''.join(l)
            self.standard_starting_fen = heavy_pieces_shuffled + \
                "/pppppppp/8/8/8/8/PPPPPPPP/" + heavy_pieces_shuffled.upper() + " w KQkq - 0 1"

        self.height, self.width = 8, 8
        self.size = (self.height, self.width)
        self.board = [[0 for i in range(self.width)]
                      for j in range(self.height)]

        # Initialize the board from FEN
        self.load_position_from_fen(self.standard_starting_fen)

        # Find positions of pieces on the board
        self.find_pieces()

        # Feed initial state into list
        self.prev_board_states.append(self.load_fen_from_position())

        # if chess960 then castle not possible (update in the future)
        if self.chess960:
            white_king_y, white_king_x = self.pieces_coor["white"]["king"][0]
            black_king_y, black_king_x = self.pieces_coor["black"]["king"][0]
            white_king_piece, black_king_piece = self.board[white_king_y][
                white_king_x], self.board[black_king_y][black_king_x]
            white_king_piece.short_castle, white_king_piece.long_castle = False, False
            black_king_piece.short_castle, black_king_piece.long_castle = False, False

        # Find attacking squares
        self.find_all_attacking_squares("black")
        self.find_all_attacking_squares("white")

    def __eq__(self, other):
        if isinstance(other, Chessboard):
            return self.board == other.board
        return False

    def _cartesian_to_sequential(self, coor):
        """ 
        Change from (x, y) position coordinate to the sequential index of the same square
        """
        y, x = coor
        return (self.height - y - 1) * self.width + x

    def _sequential_to_cartesian(self, num):
        """ 
        Change from the sequential index to the (x, y) position coordinate of the same square
        """
        x = num % self.width
        y = self.height - int(num / 8) - 1
        return (y, x)

    def _check_selected_piece_by_brain(self, selected_piece_by_brain, color):
        """ Return True if there is a selected piece on the board, and also if there is at least one piece that can move """
        okay = False
        opponent_color = "white" if color == "black" else "black"

        # The brain has not chosen a piece
        if selected_piece_by_brain == "empty":
            return False

        candidate_pieces = self.pieces_coor[color][selected_piece_by_brain]
        # There are candidate pieces
        if candidate_pieces:
            # Candidate pieces have possible moves
            for piece_coor in candidate_pieces:
                y, x = piece_coor
                piece = self.board[y][x]
                if piece.name == "king":
                    moves = piece.avail_moves(
                        self.board, piece_coor, None, util.unravel(
                            list(self.attack_squares[opponent_color].values()))
                    )
                else:
                    moves = piece.avail_moves(
                        self.board, piece_coor)
                if moves:
                    okay = True
                    break
        return okay

    def find_pieces(self):
        """ Find the pieces on the board """
        self.pieces_coor = {
            "black": {
                "pawn": [], "knight": [], "bishop": [], "rook": [], "queen": [], "king": []
            },
            "white": {
                "pawn": [], "knight": [], "bishop": [], "rook": [], "queen": [], "king": []
            }
        }

        for y in range(self.height):
            for x in range(self.width):
                if self.board[y][x] != 0:
                    piece = self.board[y][x]
                    piece_name, piece_color = piece.name, piece.color
                    self.pieces_coor[piece_color][piece_name].append((y, x))

    def set_turn(self, turn):
        """ Set the turn of the game """
        if turn == "w":
            self.turn = "white"
        elif turn == "b":
            self.turn = "black"

    def get_pieces_based_on_color(self, color, opposite=False):
        """
        Get the seq. coors of the pieces given the colors
        """
        # if opposite is true, then flip color
        if opposite:
            if color.lower() == "white" or color.lower() == "w":
                color = "black"
            else:
                color = "white"

        # check color of pieces to return correct list
        if color.lower() == "white" or color.lower() == "w":
            return self.white_pieces_coor
        elif color.lower() == "black" or color.lower() == "b":
            return self.black_pieces_coor
        else:
            return None

    def get_attack_squares(self, color, opposite=False):
        """
        Get the seq. coors of attacking squares given the colors
        """
        # if opposite is true, then flip color
        if opposite:
            if color.lower() == "white" or color.lower() == "w":
                color = "black"
            else:
                color = "white"

        # check color of pieces to return correct list
        if color.lower() == "white" or color.lower() == "w":
            return self.white_attack_squares
        elif color.lower() == "black" or color.lower() == "b":
            return self.black_attack_squares
        else:
            return None

    def load_position_from_fen(self, fen):
        """
        Set the pieces on the board according to FEN
        """
        fen_preprocessed = fen.split(" ")
        all_rows, turn, castle_rights = fen_preprocessed[0], fen_preprocessed[1], fen_preprocessed[2]
        all_rows_list = all_rows.split("/")

        white_short_castle_right, white_long_castle_right, black_short_castle_right, black_long_castle_right = False, False, False, False
        if castle_rights == "-":
            pass
        else:
            for castle_right in castle_rights:

                # Castle right for White
                if castle_right == "K":
                    white_short_castle_right = True
                if castle_right == "Q":
                    white_long_castle_right = True
                if castle_right == "k":
                    black_short_castle_right = True
                if castle_right == "q":
                    black_long_castle_right = True

        # Set the current turn based on FEN
        self.set_turn(turn)

        for y, row in enumerate(all_rows_list):
            x = 0
            for character in row:
                # Check for number
                if character.isdigit():
                    x += int(character)

                else:
                    # Create piece instance
                    piece = self._create_piece_instance_fen(character)
                    if piece.name == "king":
                        if piece.color == "white":
                            piece.short_castle = white_short_castle_right
                            piece.long_castle = white_long_castle_right
                        else:
                            piece.short_castle = black_short_castle_right
                            piece.long_castle = black_long_castle_right

                    self.board[y][x] = piece
                    x += 1

    def load_fen_from_position(self):
        """ From the current position, create its FEN """
        fen_string = ""
        for y in range(self.height):
            empty_square = 0
            for x in range(self.width):
                if self.board[y][x] != 0:
                    if empty_square != 0:
                        fen_string = fen_string + str(empty_square)
                    empty_square = 0
                    piece = self.board[y][x]
                    name, color = piece.name, piece.color

                    # Based on name, create the letter
                    if name == "pawn":
                        ch = "p"
                    if name == "knight":
                        ch = "n"
                    if name == "bishop":
                        ch = "b"
                    if name == "rook":
                        ch = "r"
                    if name == "king":
                        ch = "k"
                    if name == "queen":
                        ch = "q"

                    # Based on color, decide upper or not
                    if color == "white":
                        ch = ch.upper()

                    fen_string = fen_string + ch
                else:
                    empty_square += 1
            if empty_square != 0:
                fen_string = fen_string + str(empty_square)
            fen_string = fen_string + "/"

        return fen_string

    def _create_piece_instance_fen(self, text):

        # Uppercase is White
        if text.isupper():
            color = "white"
        # Lowercase is Black
        else:
            color = "black"

        # Create piece instrance
        if text.lower() == "p":
            return cp.Pawn(color)
        if text.lower() == "b":
            return cp.Bishop(color)
        if text.lower() == "r":
            return cp.Rook(color)
        if text.lower() == "n":
            return cp.Knight(color)
        if text.lower() == "q":
            return cp.Queen(color)
        if text.lower() == "k":
            return cp.King(color)

    def _from_move_to_pgn(self, piece, curr_square, square_to_move, capture=False, short_castle=False, long_castle=False, promote=False):
        """ 
        Generate the PGN of the game 
        """
        curr_y, curr_x = curr_square
        move_y, move_x = square_to_move
        #piece = self.board[curr_y][curr_x]
        piece_name = piece.name
        move_pgn, promote_pgn = "", ""

        # Notation of the move order
        turn_num = str(int((self.num_of_moves - 1) / 2) + 1)
        if self.turn == "white":
            dot = "."
        else:
            dot = "..."
        turn_pgn = turn_num + dot + " "

        # Short and long castle have special notation
        if short_castle:
            move_pgn = "O-O"
        elif long_castle:
            move_pgn = "O-O-O"

        else:

            # Get the name of the piece
            piece_name_dist = {
                "king": "K", "queen": "Q", "knight": "N", "bishop": "B", "rook": "R", "pawn": ""
            }
            file_text_dist = {
                0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"
            }

            if not(promote):
                piece_name_pgn = piece_name_dist[piece_name]
            else:
                piece_name_pgn = piece_name_dist["pawn"]
            move_x_pgn = file_text_dist[move_x]
            move_y_pgn = str(self.height - move_y)

            if capture:
                if piece_name == "pawn" or promote:
                    piece_name_pgn = file_text_dist[curr_x]
                capture_pgn = "x"
            else:
                capture_pgn = ""

            if promote:
                promote_pgn = "=" + piece_name_dist[piece.name]

            # Notation of the move
            move_pgn = piece_name_pgn + capture_pgn + move_x_pgn + move_y_pgn + promote_pgn

        # Final pgn result
        pgn_result = turn_pgn + move_pgn

        # Append to the list of self.pgn and return the current move pgn
        self.pgn.append(pgn_result)
        return pgn_result

    def print_board_terminal(self):
        """
        Print the board to the terminal
        """
        for i in range(self.height):
            print("------------------")
            for j in range(self.width):

                # Without any piece
                if self.board[i][j] == 0:
                    character = " "

                # There's a piece
                else:
                    if isinstance(self.board[i][j], cp.Pawn):
                        character = "p"
                    elif isinstance(self.board[i][j], cp.Queen):
                        character = "q"
                    elif isinstance(self.board[i][j], cp.Knight):
                        character = "n"
                    elif isinstance(self.board[i][j], cp.Bishop):
                        character = "b"
                    elif isinstance(self.board[i][j], cp.Rook):
                        character = "r"
                    elif isinstance(self.board[i][j], cp.King):
                        character = "k"
                    else:
                        pass

                    if self.board[i][j].color == "white":
                        character = character.upper()

                print("|" + character, end="")
            print("|")
        print("------------------")

    def _move_piece(self, chosen_square, clicked_square, promotion_piece=None):
        """ 
        Move a piece from the self.current_chosen_square to the clicked square 
        This method is only called when make_move_from_selected_square has the param change_board = true
        """
        # Check for special moves to update the PGN
        last_move_is_short_castle = False
        last_move_is_long_castle = False
        last_move_is_capture = False
        promoted = False
        en_passant_maybe = False

        # Move a piece and update the board
        curr_y, curr_x = chosen_square
        clicked_y, clicked_x = clicked_square
        piece = self.board[curr_y][curr_x]
        self.board[curr_y][curr_x] = 0

        # Check for capture
        if self.board[clicked_y][clicked_x] != 0:
            last_move_is_capture = True
            # if a capture happens then the position cannot be repeated (avoid 3-fold repetition)
            self.prev_board_states = []

        # A capture also happens when there is en passant
        if self.board[clicked_y][clicked_x] == 0 and piece.name == "pawn" and clicked_x != curr_x:
            last_move_is_capture = True
            if piece.color == "white":
                self.board[clicked_y + 1][clicked_x] = 0
            else:
                self.board[clicked_y - 1][clicked_x] = 0
        self.board[clicked_y][clicked_x] = piece
        color = piece.color

        # Move of a pawn then check en passant and promotion
        if piece.name == "pawn":
            # if a pawn moves then the position cannot be repeated (avoid 3-fold repetition)
            self.prev_board_states = []

            # Check for promotion piece
            if promotion_piece and (clicked_y == 0 or clicked_y == 7):
                if promotion_piece == "knight":
                    promotion_piece_obj = cp.Knight(color)
                if promotion_piece == "rook":
                    promotion_piece_obj = cp.Rook(color)
                if promotion_piece == "queen":
                    promotion_piece_obj = cp.Queen(color)
                if promotion_piece == "bishop":
                    promotion_piece_obj = cp.Bishop(color)
                piece = promotion_piece_obj
                self.board[clicked_y][clicked_x] = promotion_piece_obj
                promoted = True

            # Check for en passant in the next move by the opponent
            if piece.color == "black" and not(last_move_is_capture):
                if curr_y == 1 and clicked_y == 3:
                    en_passant_maybe = True
            elif piece.color == "white" and not(last_move_is_capture):
                if curr_y == 6 and clicked_y == 4:
                    en_passant_maybe = True

            # En passant possible for nearby opponent pawns
            if en_passant_maybe:
                if curr_x > 0:
                    if isinstance(self.board[clicked_y][curr_x - 1], cp.Pawn):
                        opponent_pawn = self.board[clicked_y][curr_x - 1]
                        if opponent_pawn.color != piece.color and opponent_pawn.color == "white":
                            opponent_pawn.en_passant = (
                                clicked_y - 1, curr_x)
                        elif opponent_pawn.color != piece.color and opponent_pawn.color == "black":
                            opponent_pawn.en_passant = (
                                clicked_y + 1, curr_x)
                if curr_x < self.width - 2:
                    if isinstance(self.board[clicked_y][curr_x + 1], cp.Pawn):
                        opponent_pawn = self.board[clicked_y][curr_x + 1]
                        if opponent_pawn.color != piece.color and opponent_pawn.color == "white":
                            opponent_pawn.en_passant = (
                                clicked_y - 1, curr_x)
                        elif opponent_pawn.color != piece.color and opponent_pawn.color == "black":
                            opponent_pawn.en_passant = (
                                clicked_y + 1, curr_x)

        # If the rook moves, then lose castle right on that side
        if piece.name == "rook":
            king_coor = self.pieces_coor[color]["king"][0]
            king_y, king_x = king_coor
            king_piece = self.board[king_y][king_x]

            if curr_x == self.width - 1:
                king_piece.short_castle = False
            elif curr_x == 0:
                king_piece.long_castle = False

        # If the king moves, then check for castle moves
        if piece.name == "king":
            if abs(clicked_x - curr_x) == 2:
                if clicked_x == 6:
                    piece_on_edge = self.board[curr_y][7]
                    if piece_on_edge != 0:
                        if piece_on_edge.color == color and piece_on_edge.name == "rook":
                            self.board[curr_y][7] = 0
                            self.board[curr_y][curr_x + 1] = piece_on_edge
                            piece.short_castle = False
                            last_move_is_short_castle = True
                            # if last move is castle then the position cannot be repeated
                            self.prev_board_states = []

                elif clicked_x == 2:
                    piece_on_edge = self.board[curr_y][0]
                    if piece_on_edge != 0:
                        if piece_on_edge.color == color and piece_on_edge.name == "rook":
                            self.board[curr_y][0] = 0
                            self.board[curr_y][curr_x - 1] = piece_on_edge
                            piece.long_castle = False
                            last_move_is_long_castle = True
                            # if last move is castle then the position cannot be repeated
                            self.prev_board_states = []
            else:
                piece.short_castle = False
                piece.long_castle = False

        # When a piece is moved, update the following:

        # Add current board to the prev board states (this is not thread-safe, need to find an alternative)
        self.prev_board_states.append(self.load_fen_from_position())

        # The number of moves 2 players have made
        self.num_of_moves += 1

        # The pgn list
        self._from_move_to_pgn(piece, chosen_square, clicked_square,
                               last_move_is_capture, last_move_is_short_castle, last_move_is_long_castle, promoted)

        # The current turn of the game
        self.turn = "white" if self.turn == "black" else "black"

        # Current positions of the pieces
        self.find_pieces()

        # After a move then disable all en passants
        for pawn_coor in self.pieces_coor[color]["pawn"]:
            pawn_y, pawn_x = pawn_coor
            pawn = self.board[pawn_y][pawn_x]
            pawn.en_passant = False

        # self.white_attack_squares, self.black_attack_squares
        self.find_all_attacking_squares("black")
        self.find_all_attacking_squares("white")

    def find_all_attacking_squares(self, color):
        """ Find all the attacking squares of the side that has the color """
        self.attack_squares[color] = {}
        for y in range(self.height):
            for x in range(self.width):
                piece = self.board[y][x]
                if piece != 0:
                    if piece.color == color:
                        # If piece is a pawn, then there's some problem
                        if piece.name == "pawn":
                            attacks = util.find_pawn_attack((y, x), color)
                        else:
                            attacks = piece.avail_moves(
                                self.board, (y, x), True)
                        self.attack_squares[color][(y, x)] = attacks

    def is_draw_by_3_fold(self):
        """ Check the 3-fold repetition drawing condition """
        # 3-fold repetition rule
        curr_board_repetitions = [i for i, prev_board_state in enumerate(
            self.prev_board_states) if prev_board_state == self.load_fen_from_position()]
        if len(curr_board_repetitions) >= 3:
            return True
        else:
            return False

    def make_move_from_selected_square(self, available_moves, chosen_square, clicked_square, change_board=False, promotion_piece=None):
        """ Make a move based on the piece at the selected square"""

        # Convert everything to cartesian
        try:
            curr_y, curr_x = chosen_square
        except:
            chosen_square = self._sequential_to_cartesian(chosen_square)
            curr_y, curr_x = chosen_square

        piece = self.board[curr_y][curr_x]

        # There's a selected piece
        if piece != 0:

            # Check if the clicked square is actually movable for the piece
            possible_moves = self.find_all_possible_moves(piece.color)
            if clicked_square in available_moves and chosen_square in possible_moves:
                if clicked_square in possible_moves[chosen_square]:
                    if change_board:
                        self._move_piece(
                            chosen_square, clicked_square, promotion_piece)
                    return True
                else:
                    return False
            else:
                return False

        # There's no selected piece
        else:
            return False

    def find_all_possible_moves(self, color):
        """ Find all the possible moves of the pieces on the color """
        avail_moves_all = {}
        opponent_color = "white" if color == "black" else "black"

        # Some rules not implemented yet
        # Loss by running out of time
        # Resignation
        # Draw by agreement
        # 50-move rule
        # Draw by insufficient material

        # Find king
        king_coor = self.pieces_coor[color]["king"][0]
        king_y, king_x = king_coor
        king = self.board[king_y][king_x]

        # Characteristics of the pieces on the chessboard
        opponent_attack_squares = self.attack_squares[opponent_color]
        opponent_attack_squares_list = util.unravel(
            list(opponent_attack_squares.values()))
        checking_pieces_coor = []
        friendly_pieces_coor = util.unravel(
            list(self.pieces_coor[color].values()))

        # Check for pieces that can pin on the opponent side (sliding pieces)
        opponent_queen, opponent_rooks, opponent_bishops = self.pieces_coor[opponent_color][
            "queen"], self.pieces_coor[opponent_color]["rook"], self.pieces_coor[opponent_color]["bishop"]

        # Create list of pieces that can pin
        pieces_can_pin, pinned_pieces = [], {}
        pieces_can_pin.extend(opponent_queen)
        pieces_can_pin.extend(opponent_rooks)
        pieces_can_pin.extend(opponent_bishops)

        for piece_can_pin in pieces_can_pin:
            pinned_squares = util.find_in_between_squares(
                piece_can_pin, king_coor, False)
            if pinned_squares:

                piece_can_pin_y, piece_can_pin_x = piece_can_pin
                the_piece = self.board[piece_can_pin_y][piece_can_pin_x]
                piece_can_pin_attacks = the_piece.avail_moves(
                    self.board, piece_can_pin, True)

                if list(set(piece_can_pin_attacks).intersection(set(pinned_squares))):

                    # Find the pieces on the pinned squares
                    ind_list = []
                    for i, square in enumerate(pinned_squares):
                        y, x = square
                        if self.board[y][x] != 0:
                            ind_list.append(i)

                    if len(ind_list) > 1:
                        # No pin at all
                        pass
                    elif ind_list == []:
                        pass
                    else:
                        # The pinned piece has same color as piece_can_pin, then no pin
                        y, x = pinned_squares[ind_list[0]]
                        piece = self.board[y][x]
                        if piece.color == opponent_color:
                            pass
                        else:
                            # Check for possible moves by pinned piece
                            #pinned_pieces.append((y, x))
                            avail_moves_pinned_piece = piece.avail_moves(
                                self.board, (y, x))
                            pinned_squares.append(piece_can_pin)
                            possible_moves_pinned_piece = list(
                                set(avail_moves_pinned_piece).intersection(set(pinned_squares)))
                            pinned_pieces[(y, x)] = possible_moves_pinned_piece
                            #avail_moves_all[(y, x)] = possible_moves_pinned_piece

        # Check if king is in check
        if king_coor in opponent_attack_squares_list:

            # Move king out of check (including capturing the piece)
            avail_king_moves = king.avail_moves(
                self.board, king_coor, None, opponent_attack_squares_list, True)
            for move in avail_king_moves.copy():
                if move in opponent_attack_squares_list:
                    avail_king_moves.remove(move)
            if avail_king_moves:
                avail_moves_all[king_coor] = avail_king_moves

            # Block check (not avail for pawn and knight, and close-up queen, rook, bishop)
            # Find the checking piece(s)
            for coor, attack_squares in self.attack_squares[opponent_color].items():
                if king_coor in attack_squares:
                    checking_pieces_coor.append(coor)

            # Double check then cannot block
            if len(checking_pieces_coor) > 1:
                pass

            # Check from a single piece
            else:
                y, x = checking_pieces_coor[0]
                piece = self.board[y][x]

                # Check from bishop or rook or queen then the check can be blocked
                if piece.name == "bishop" or piece.name == "rook" or piece.name == "queen":
                    in_between_squares = util.find_in_between_squares(
                        checking_pieces_coor[0], king_coor)
                else:
                    in_between_squares = []
                    in_between_squares.append((y, x))

                # Loop over the pieces besides the king which can block the check or capture the checking piece
                for piece_coor in friendly_pieces_coor:
                    y, x = piece_coor
                    piece = self.board[y][x]
                    if piece.name != "king":

                        # Check for pinned piece
                        if piece_coor in pinned_pieces:
                            moves = pinned_pieces[piece_coor]
                        else:
                            moves = piece.avail_moves(self.board, piece_coor)

                        possible_moves = list(
                            set(moves).intersection(set(in_between_squares)))
                        if possible_moves:
                            avail_moves_all[piece_coor] = possible_moves

            # No moves are possible, and in check, then checkmate
            if avail_moves_all == {}:
                return -100

        else:

            for piece_coor in friendly_pieces_coor:
                y, x = piece_coor
                piece = self.board[y][x]

                # if piece is king then king cannot walk into check
                if piece.name == "king":
                    moves = piece.avail_moves(
                        self.board, piece_coor, None, opponent_attack_squares_list)
                    for move in moves.copy():
                        if move in opponent_attack_squares_list:
                            moves.remove(move)

                    if moves != []:
                        avail_moves_all[piece_coor] = moves

                elif piece_coor not in pinned_pieces:
                    avail_moves_all[piece_coor] = piece.avail_moves(
                        self.board, piece_coor)
                else:
                    avail_moves_all[piece_coor] = pinned_pieces[piece_coor]

            # No moves are possible, and not in check, then stalemate
            if avail_moves_all == {}:
                return -50

        return avail_moves_all


if __name__ == "__main__":
    # For debugging purposes
    a = Chessboard()
    # print(a.load_fen_from_position())
    # a.print_board_terminal()
    # print(a.find_all_possible_moves("black"))
    print(a._check_selected_piece_by_brain("pawn", "white"))
