import util


class Piece():
    def __init__(self):
        self.name = None
        self.value = None


class Pawn(Piece):
    def __init__(self, color):
        # super.__init__()
        self.name = "pawn"
        self.value = 1
        self.color = color
        self.en_passant = False

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.name == other.name and self.color == other.color
        return False

    def __repr__(self):
        text = "A " + self.color + " " + self.name
        return text

    def avail_moves(self, board, coor, attack=None):
        """ Input a Chessboard object and find avail moves for the piece
        If no moves available, return None """

        avail_moves_list = []
        y, x = coor
        width, height = len(board[0]), len(board)

        # White's pawn moves up the board
        if self.color == "white":
            move_1_square, move_2_squares = -1, -2
            start_pos = 6

        # Black's pawn moves down the board
        elif self.color == "black":
            move_1_square, move_2_squares = 1, 2
            start_pos = 1

        # First two-square move
        if y == start_pos:
            if board[y + move_1_square][x] == 0 and board[y + move_2_squares][x] == 0:
                avail_moves_list.append((y + move_2_squares, x))

        # Normal forward move
        if board[y + move_1_square][x] == 0:
            avail_moves_list.append((y + move_1_square, x))

        # Capture (remember to check for flank pawns)
        if x - 1 > -1:
            if board[y + move_1_square][x - 1] != 0:
                if board[y + move_1_square][x - 1].color != self.color or attack:
                    avail_moves_list.append((y + move_1_square, x - 1))

        if x + 1 < width:
            if board[y + move_1_square][x + 1] != 0:
                if board[y + move_1_square][x + 1].color != self.color or attack:
                    avail_moves_list.append((y + move_1_square, x + 1))

        # En passant
        if self.en_passant:
            avail_moves_list.append(self.en_passant)

        return avail_moves_list

    # Some ideas for methods in each piece class
    # def find: return the coors of this specific piece instance on the board object
    # def avail_move: given def find returns a none-type value, return the avail moves for the piece


class Knight(Piece):
    def __init__(self, color):
        # super.__init__()
        self.name = "knight"
        self.value = 3
        self.color = color

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.name == other.name and self.color == other.color
        return False

    def avail_moves(self, board, coor, attack=None):
        width, height = len(board[0]), len(board)
        index = util.cartesian_to_sequential(coor, width, height)
        avail_moves_list = []

        # Extract squares the Knight can jump to
        # Going from 11 hour direction and clockwise
        indices_around = [15, 17, 10, -6, -15, -17, -10, 6]

        pos_y, pos_x = coor
        # Check for edge positions (row)
        if pos_y == 0:
            indices_around[0], indices_around[1], indices_around[2], indices_around[7] = 0, 0, 0, 0
        elif pos_y == 1:
            indices_around[0], indices_around[1] = 0, 0
        elif pos_y == height - 2:
            indices_around[4], indices_around[5] = 0, 0
        elif pos_y == height - 1:
            indices_around[4], indices_around[5], indices_around[3], indices_around[6] = 0, 0, 0, 0

        # Check for edge positions (file)
        if pos_x == 0:
            indices_around[7], indices_around[6], indices_around[0], indices_around[5] = 0, 0, 0, 0
        elif pos_x == 1:
            indices_around[7], indices_around[6] = 0, 0
        elif pos_x == width - 2:
            indices_around[2], indices_around[3] = 0, 0
        elif pos_x == width - 1:
            indices_around[1], indices_around[4], indices_around[2], indices_around[3] = 0, 0, 0, 0

        for index_around in indices_around:
            if index_around != 0:
                square_to_check = index + index_around
                y, x = util.sequential_to_cartesian(
                    square_to_check, width, height)
                if board[y][x] != 0:
                    if board[y][x].color != self.color or attack:
                        avail_moves_list.append((y, x))
                else:
                    avail_moves_list.append((y, x))

        return avail_moves_list


class Bishop(Piece):
    def __init__(self, color):
        # super.__init__()
        self.name = "bishop"
        self.value = 3.5
        self.color = color

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.name == other.name and self.color == other.color
        return False

    def avail_moves(self, board, coor, attack=None):
        avail_moves_list = []
        opponent_color = "white" if self.color == "black" else "black"
        width, height = len(board[0]), len(board)

        # Diag left up
        run_y, run_x = coor
        while run_x > 0 and run_y > 0:
            run_x -= 1
            run_y -= 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        # Diag right up
        run_y, run_x = coor
        while run_x < width - 1 and run_y > 0:
            run_x += 1
            run_y -= 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        # Diag left down
        run_y, run_x = coor
        while run_x > 0 and run_y < height - 1:
            run_x -= 1
            run_y += 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        # Diag right down
        run_y, run_x = coor
        while run_x < width - 1 and run_y < height - 1:
            run_x += 1
            run_y += 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        return avail_moves_list


class Rook(Piece):
    def __init__(self, color):
        # super.__init__()
        self.name = "rook"
        self.value = 5
        self.color = color

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.name == other.name and self.color == other.color
        return False

    def avail_moves(self, board, coor, attack=None):
        avail_moves_list = []
        opponent_color = "white" if self.color == "black" else "black"
        width, height = len(board[0]), len(board)

        # Left
        run_y, run_x = coor
        while run_x > 0:
            run_x -= 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        # Right
        run_y, run_x = coor
        while run_x < width - 1:
            run_x += 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        # Up
        run_y, run_x = coor
        while run_y > 0:
            run_y -= 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        # Down
        run_y, run_x = coor
        while run_y < height - 1:
            run_y += 1
            if board[run_y][run_x] != 0:
                piece = board[run_y][run_x]
                if piece.color == opponent_color or attack:
                    avail_moves_list.append((run_y, run_x))
                if attack and piece.color == opponent_color and piece.name == "king":
                    pass
                else:
                    break
            avail_moves_list.append((run_y, run_x))

        return avail_moves_list


class Queen(Rook, Bishop):
    def __init__(self, color):
        # super.__init__()
        self.name = "queen"
        self.value = 9
        self.color = color

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.name == other.name and self.color == other.color
        return False

    def avail_moves(self, board, coor, attack=None):
        """
        Call avail_moves from Rook and Bishop and append the results 
        """
        avail_moves_list = []
        for cls in Queen.__bases__:
            avail_moves = cls(self.color).avail_moves(board, coor, attack)
            avail_moves_list.extend(avail_moves)

        return avail_moves_list


class King(Piece):
    def __init__(self, color):
        # super.__init__()
        self.name = "king"
        self.value = 100
        self.color = color
        self.short_castle = True
        self.long_castle = True

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.name == other.name and self.color == other.color
        return False

    def avail_moves(self, board, coor, attack=None, opponent_attacks=None, in_check=False):
        """ 
        Input a board and find avail moves for the piece
        If no moves available, return None
        """
        width, height = len(board[0]), len(board)
        curr_y, curr_x = coor

        avail_moves_list = []   # Avail moves

        # Extract all the squares around the king
        ind_around = [-1, 0, 1]

        for ind_y in ind_around:
            for ind_x in ind_around:
                if not(ind_y == 0 and ind_x == 0):
                    if (curr_x + ind_x > -1) and (curr_x + ind_x < width) and (curr_y + ind_y > -1) and (curr_y + ind_y < height):
                        piece = board[curr_y + ind_y][curr_x + ind_x]
                        # if the move is not in the attacks of the opponent:
                        if opponent_attacks:
                            if (curr_y + ind_y, curr_x + ind_x) not in opponent_attacks and not(attack):
                                if piece == 0:
                                    avail_moves_list.append(
                                        (curr_y + ind_y, curr_x + ind_x))
                                elif piece.color != self.color:
                                    avail_moves_list.append(
                                        (curr_y + ind_y, curr_x + ind_x))
                        elif attack:
                            avail_moves_list.append(
                                (curr_y + ind_y, curr_x + ind_x))

        # If attack is not True, and king not in check, then castle is valid
        if not(attack) and not(in_check):

            # Short castle
            # if still have short castle rights
            if self.short_castle:

                short_castle_able = True

                # Color of the king matters
                if self.color == "black":
                    king_coor = (0, 4)
                    rook_coor = (0, 7)
                else:
                    king_coor = (7, 4)
                    rook_coor = (7, 7)

                # There's piece on the way of castle so cannot castle
                if self.color == "black":
                    squares = util.find_in_between_squares(
                        king_coor, rook_coor, False)
                else:
                    squares = util.find_in_between_squares(
                        king_coor, rook_coor, False)
                for square in squares:
                    y, x = square
                    if board[y][x] != 0:
                        short_castle_able = False

                # Squares of castle on the attack squares of opponent
                for square in squares:
                    y, x = square
                    if (y, x) in opponent_attacks:
                        short_castle_able = False

                if short_castle_able:
                    king_y, king_x = king_coor
                    king_x += 2
                    avail_moves_list.append((king_y, king_x))

            # Long castle
            if self.long_castle:

                long_castle_able = True

                # Color of the king matters
                if self.color == "black":
                    king_coor = (0, 4)
                    rook_coor = (0, 0)
                else:
                    king_coor = (7, 4)
                    rook_coor = (7, 0)

                # There's piece on the way of castle so cannot castle
                if self.color == "black":
                    squares = util.find_in_between_squares(
                        king_coor, rook_coor, False)
                else:
                    squares = util.find_in_between_squares(
                        king_coor, rook_coor, False)
                for square in squares:
                    y, x = square
                    if board[y][x] != 0:
                        long_castle_able = False

                # Squares of castle on the attack squares of opponent
                # These squares are different from the squares above because the opponent can attack the b1 square
                # but White can still long castle, same thing for b8 square for Black

                rook_y, rook_x = rook_coor
                squares = util.find_in_between_squares(
                    king_coor, (rook_y, rook_x + 1), False)

                for square in squares:
                    y, x = square
                    if (y, x) in opponent_attacks:
                        long_castle_able = False

                if long_castle_able:
                    king_y, king_x = king_coor
                    king_x -= 2
                    avail_moves_list.append((king_y, king_x))

        return avail_moves_list
