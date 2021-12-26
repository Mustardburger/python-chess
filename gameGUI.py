import pygame
import chessboard as cb
import chessPieces as cp
from saveChessPGN import saveChessPGN
import util
import pickle
import chessGUI as cg
from voiceChess import voiceChess
import time


class mainGameGUI():
    def __init__(self, mode, screen, network_api=None):

        self.mode = mode
        if mode == "standard" or mode == "hab":
            self.board = cb.Chessboard()
        elif mode == "960":
            self.board = cb.Chessboard(False, False, True)

        # Multiplayer mode (including variables only used for multiplayer game)
        if network_api:
            self.multiplayer = True
            self.n = network_api
        else:
            self.multiplayer = False
        self.multiplayer_color, self.opponent_name = None, None
        self.hab = True if mode == "hab" else False

        self.board_width, self.board_height = 8, 8
        self.board_square_rects = [
            [0 for i in range(self.board_width)] for j in range(self.board_height)]
        self.board_piece_imgs = [
            [0 for i in range(self.board_width)] for j in range(self.board_height)]
        self.board_surface = None
        self.flipped_view = False
        self.screen = screen
        self.squares = {}
        self.WHITE = (255, 255, 255)
        self.BLACK = (100, 100, 100)
        self.DARK_BLACK = (0, 0, 0)
        self.SKIN_COLOR = (241, 194, 125)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BOARD_POS = (100, 100)
        self.SQUARE_SIZE = (50, 50)
        self.LARGE_FONT = pygame.font.Font("OpenSans-Regular.ttf", 30)
        self.SMALL_FONT = pygame.font.Font("OpenSans-Regular.ttf", 20)
        self.TIME_LIMIT = 600
        self.TIME_INCREMENT = 0

    def _get_opponent_name(self):
        """ Send a request to get the opponent from the server """
        try:
            self.opponent_name = self.n.send_request("!opponent")
            print("[CLIENT] Opponent's name is: " + self.opponent_name)
        except:
            print("[CLIENT] Cannot get opponent name, cannot start game!")

    def _get_my_color(self):
        """ Send a request to get the color side from the server """
        try:
            self.multiplayer_color = self.n.send_request("!my_color")
            print("[CLIENT] My color is: " + self.multiplayer_color)

            # if color is Black then flip view
            if self.multiplayer_color == "black":
                self.flipped_view = True
        except:
            print("[CLIENT] Cannot get player color, cannot start game!")

    def _from_0_0_coor_to_current_coor(self, coor_to_translate, origin_coor, reversed_translate=False):
        """ 
        Translate the coor of a point from the main (0,0) coordinates (based on self.screen)
        to the coordinates specified by the new origin
        Do the opposite if the argument reversed_translate = True
        """
        y_origin, x_origin = origin_coor
        y_curr, x_curr = coor_to_translate
        if not(reversed_translate):
            return (y_curr - y_origin, x_curr - x_origin)
        else:
            return (y_curr + y_origin, x_curr + x_origin)

    def _draw_result(self, result):
        """ Draw a red text to notify the result once the game is over """
        self._draw_text(self.screen, result,
                        self.RED, (300, 300))

    def _draw_square(self, screen, color, center_pos, width, height, square_yx_coor=None):
        """ Draw a rectangle with center_pos and width and height """

        # Create the square
        center_x, center_y = center_pos
        top_x = center_x - (width / 2)
        top_y = center_y - (height / 2)
        rect = pygame.draw.rect(screen, color, (top_x, top_y, width, height))

        # Record the square
        if square_yx_coor:
            y, x = square_yx_coor
            if self.board_square_rects[y][x] == 0:
                self.board_square_rects[y][x] = rect

        # Update the view
        pygame.display.update()

    def _draw_selected_square(self, screen, coor):
        """ Draw a red bounding box around the selected square """
        y, x = coor
        sq_w, sq_h = self.SQUARE_SIZE
        rect = self.board_square_rects[y][x]
        center_pos = self._from_0_0_coor_to_current_coor(
            rect.center, self.BOARD_POS, True)
        cen_y, cen_x = center_pos
        top_y, top_x = cen_y - (sq_h / 2), cen_x - (sq_w / 2)
        pygame.draw.rect(screen, self.RED, (top_y, top_x, sq_w, sq_h), 2)

    def _draw_piece(self, screen, piece, center_pos, piece_yx_coor=None):
        """ Draw the piece at the given location """

        # Check which piece is it
        try:
            name, color = piece.name, piece.color
            full_name = color + name
            link = "img" + "\\" + full_name + ".png"

        except:
            raise TypeError("This is not a piece")
            return

        # Import an image
        img = pygame.image.load(link)
        img_rect = img.get_rect()
        # If the pieces use the main screen instead of the board_surface
        if screen == self.screen:
            center_pos = self._from_0_0_coor_to_current_coor(
                center_pos, self.BOARD_POS, True)
        img_rect.center = center_pos
        screen.blit(img, img_rect)

        # Record the piece
        if piece_yx_coor:
            y, x = piece_yx_coor
            self.board_piece_imgs[y][x] = img

    def _draw_text(self, screen, text, color, center_pos, draw_rect=False):
        """ Draw the text onto the screen at center_pos """
        button = self.LARGE_FONT.render(text, True, color)
        button_rect = button.get_rect()
        button_rect.center = center_pos

        # Draw a background rect
        if draw_rect:
            pygame.draw.rect(screen, self.WHITE, button_rect)

        screen.blit(button, button_rect)
        return (button, button_rect)

    def _draw_pgn(self, screen, pgn_starting_point=None):
        """ 
        Draw the PGN of the game. The PGN screen only contains at most 16 moves
        """
        pgn_box_top_left_x, pgn_box_top_left_y = 550, 165
        pgn_box_width, pgn_box_height = 230, 265

        # Draw a bounding box of the PGN display frame
        pgn_screen_rect = pygame.Rect(
            (pgn_box_top_left_x, pgn_box_top_left_y, pgn_box_width, pgn_box_height))
        pygame.draw.rect(screen, self.DARK_BLACK, pgn_screen_rect, 5)
        max_moves = 16

        # A list of PGN of the game
        pgn_list = self.board.pgn

        if self.board.num_of_moves < max_moves + 1:
            # Draw move by move onto the screen
            for i, pgn in enumerate(pgn_list):
                if (i % 2) == 0:
                    img_x = pgn_box_top_left_x + 10
                else:
                    img_x = pgn_box_top_left_x + 100

                img_y = pgn_box_top_left_y + int((i // 2))*30 + 10
                img = self.SMALL_FONT.render(pgn, True, self.DARK_BLACK)
                screen.blit(img, (img_x, img_y))

        else:
            for j, i in enumerate(range(pgn_starting_point*2, len(pgn_list))):
                if j == max_moves:
                    break
                if (i % 2) == 0:
                    img_x = pgn_box_top_left_x + 10
                else:
                    img_x = pgn_box_top_left_x + 100

                pgn = pgn_list[i]
                img_y = pgn_box_top_left_y + int((j // 2))*30 + 10
                img = self.SMALL_FONT.render(pgn, True, self.DARK_BLACK)
                screen.blit(img, (img_x, img_y))

        return pgn_screen_rect

    def _display_time(self, screen, time, center_pos, current_turn):
        """ Display the time """

        # Draw the text
        curr_min, curr_sec = util.from_sec_to_minsec(time)
        text = f"{curr_min}:{curr_sec}"
        time_text, time_text_rect = self._draw_text(
            screen, text, self.DARK_BLACK, center_pos, True)

        # If current turn then draw a green bounding box
        if current_turn:
            pygame.draw.rect(screen, self.GREEN, time_text_rect, 4)

    def _detect_square_on_mouse_hover(self, pos):
        """ Detect the square on which the mouse is hovering """

        # Detect the square
        # Not the optimal implementation here, since still using for loop
        for i in range(self.board_height):
            for j in range(self.board_width):
                if self.board_square_rects[i][j].collidepoint(self._from_0_0_coor_to_current_coor(pos, self.BOARD_POS)):
                    return (i, j)

    def draw_chessboard(self, start_center_pos, square_size, fill_screen=False):
        """ Draw an empty chessboard """

        # Fill screen before drawing
        if fill_screen:
            self.screen.fill(self.SKIN_COLOR)
            pass

        # Initialize starting position of the first square
        start_center_x, start_center_y = start_center_pos
        run_x, run_y = start_center_x, start_center_y
        square_width, square_height = square_size

        # Create the board surface
        board_surface = pygame.Surface(
            (square_width * self.board_width, square_height * self.board_height))

        for i in range(self.board_height):
            for j in range(self.board_width):

                # Alternating black and white
                if (i + j) % 2 == 0:
                    color = self.WHITE
                else:
                    color = self.BLACK

                center_pos = (run_x, run_y)
                self._draw_square(board_surface, color, center_pos,
                                  square_width, square_height, (i, j))
                run_x += square_width

            run_y += square_height
            run_x = start_center_x

        return board_surface

    def draw_all_pieces(self, screen, start_center_pos, square_size, moving_piece_coor=None):
        """ Draw the pieces on the chessboard """

        # Initialize starting position of the first square
        start_center_x, start_center_y = start_center_pos
        run_x, run_y = start_center_x, start_center_y
        square_width, square_height = square_size
        invert_y, invert_x = self.board_height, self.board_width

        for i in range(self.board_height):
            invert_y -= 1
            for j in range(self.board_width):
                invert_x -= 1
                if self.flipped_view:
                    piece = self.board.board[invert_y][invert_x]
                else:
                    piece = self.board.board[i][j]
                center_pos = (run_x, run_y)
                if piece != 0 and (i, j) != moving_piece_coor:
                    self._draw_piece(screen, piece, center_pos, (i, j))
                else:
                    self.board_piece_imgs[i][j] = 0
                run_x += square_width

            invert_x = self.board_width
            run_y += square_height
            run_x = start_center_x

    def _draw_dragging_piece(self, screen, selected_piece_img, pos):
        """ Draw the dragging piece to simulate the drag and drop animation """
        if selected_piece_img:
            selected_piece_img_rect = selected_piece_img.get_rect()
            selected_piece_img_rect.center = pos
            screen.blit(selected_piece_img, selected_piece_img_rect)

    def _draw_possible_square_moves(self, screen, coor, radius=10):
        """ Given the position of the square on the board with a piece,
        draw a circle on the squares where the piece can move
        Returns the coors of the possible moves of a given piece
        Returns None if no piece is on the square
        """
        y, x = coor
        possible_moves = []
        piece = self.board.board[y][x]
        opponent_color = "white" if piece.color == "black" else "black"
        if piece != 0:
            # Find possible moves for the piece
            possible_moves_all = self.board.find_all_possible_moves(
                piece.color)

            # Checkmate
            if possible_moves_all == -100:
                return -100

            # Stalemate
            if possible_moves_all == -50:
                return -50

            # If piece is king, then check for castle
            if piece.name == "king":
                opponent_attack_squares_list = util.unravel(
                    list(self.board.attack_squares[opponent_color].values()))
                possible_moves_piece = piece.avail_moves(
                    self.board.board, coor, None, opponent_attack_squares_list)
            else:
                possible_moves_piece = piece.avail_moves(
                    self.board.board, coor)

            if (y, x) in possible_moves_all:
                possible_moves = list(set(possible_moves_piece).intersection(
                    set(possible_moves_all[(y, x)])))
            for move in possible_moves:
                move_y, move_x = move
                if self.flipped_view:
                    move_y, move_x = util.flipped_view_coor((move_y, move_x))
                else:
                    pass
                rect = self.board_square_rects[move_y][move_x]
                rect_center_pos = self._from_0_0_coor_to_current_coor(
                    rect.center, self.BOARD_POS, True)
                pygame.draw.circle(screen, self.GREEN, rect_center_pos, radius)

        return possible_moves

    def initialize(self):
        """ 
        Draw the chessboard, load the pieces, create the chessboard object 
        If multiplayer, then request opponent name and player color
        """
        self.board_surface = self.draw_chessboard((25, 25), self.SQUARE_SIZE)
        if self.multiplayer:
            self._get_opponent_name()
            self._get_my_color()

    def event_listener(self):
        """ Launch the GUI of the chess board
        This method is also the listener to most of the events """
        hover = True
        selected_piece_img = None
        checkmate, stalemate, draw_by_3_fold = False, False, False
        game_saved = False
        save_game_text = None
        possible_moves = None
        coor_square_on_hover = None
        pgn_screen_rect = None
        ran_out_of_time = None
        move_message_for_server = "wait"
        promotion_piece = "queen"
        pgn_starting_point = 0

        # For multiplayer only
        online_result = None
        back_to_lobby = None

        # Names of both players
        opponent_name_text = cg.Button_Text(self.opponent_name, self.screen)
        my_name_text = cg.Button_Text("You", self.screen)
        resign = cg.Button_Text("Resign", self.screen)
        offer_draw = cg.Button_Text("Offer draw", self.screen)

        # Text for saving game
        game_saved_text = cg.Button_Text("Game has been saved", self.screen)

        # Implement timer
        clock = pygame.time.Clock()
        white_time, black_time = self.TIME_LIMIT, self.TIME_LIMIT
        clock.tick()

        while True:

            # Multiplayer sending and receiving data
            if self.multiplayer:

                try:
                    # Player has pressed the back to lobby button
                    if move_message_for_server == "!back_lobby":
                        reply_from_server = self.n.send(
                            move_message_for_server)
                        self.screen.fill((self.SKIN_COLOR))
                        return 1
                    # Send the move_pgn to the server if a valid move has been made
                    reply_from_server = self.n.send(move_message_for_server)
                    # print("[CLIENT] Message received from server: ",
                    #     reply_from_server)
                    # if game has not ended, the reply is a dict
                    if isinstance(reply_from_server, dict):
                        game_from_server = reply_from_server["game"]
                        curr_turn_server_board = reply_from_server["curr_turn"]

                        # if game from server is different from local game then make an update
                        if game_from_server != self.board:
                            self.board = game_from_server       # Need copy.deepcopy() here?
                            self.board.turn = curr_turn_server_board
                            #print("[CLIENT] Chessboard updated")

                        # Set the message to "wait"
                        if move_message_for_server != "wait" and move_message_for_server != "resign" and move_message_for_server != "!back_lobby":
                            move_message_for_server = "wait"

                    # else, then the game has ended
                    elif isinstance(reply_from_server, str):
                        print("[CLIENT] Game ends")

                        # Draw by stalemate
                        if reply_from_server == "stalemate":
                            online_result = cg.Button_Text(
                                "Stalemate: You draw", self.screen)

                        # Draw by some other draw
                        elif reply_from_server == "draw":
                            online_result = cg.Button_Text(
                                "You draw", self.screen)

                        # Game ended by resignation
                        elif reply_from_server.find("resignation") >= 0:
                            online_result = cg.Button_Text(
                                reply_from_server, self.screen)

                        # Game ended by checkmate
                        else:
                            reason_game_end, win_loss = reply_from_server.split(
                                ",")[0], reply_from_server.split(",")[1]
                            online_result = cg.Button_Text(
                                reason_game_end + ": You " + win_loss, self.screen)

                except:
                    print(
                        "[CLIENT] An error occurred while sending move or retrieving data")

            # Time passed (in second)
            sec_elapsed = clock.tick() / 1000

            # Check for whose turn it is to subtract the time (and when the game is not over)
            if not(checkmate) and not(stalemate) and not(draw_by_3_fold) and not(isinstance(ran_out_of_time, int)):
                if self.board.turn == "white":
                    white_time = white_time - sec_elapsed
                else:
                    black_time = black_time - sec_elapsed

                # Check when one of the clocks runs out (not for multiplayer)
                if not(self.multiplayer):
                    if white_time < 0:
                        ran_out_of_time = 1
                    elif black_time < 0:
                        ran_out_of_time = -1

            # Get mouse current position
            mouse_pos = pygame.mouse.get_pos()

            # Draw everything
            self.screen.fill((self.SKIN_COLOR))
            self.screen.blit(self.board_surface, self.BOARD_POS)
            self.draw_all_pieces(self.screen, (25, 25), self.SQUARE_SIZE)
            pgn_screen_rect = self._draw_pgn(self.screen, pgn_starting_point)
            if game_saved:
                game_saved_text.draw(self.screen, self.RED,
                                     self.SMALL_FONT, (670, 550), None, False)

            if self.multiplayer:
                # Draw name of opponent
                opponent_name_text.draw(
                    self.screen, self.DARK_BLACK, self.LARGE_FONT, (160, 50), None, False)
                my_name_text.draw(
                    self.screen, self.DARK_BLACK, self.LARGE_FONT, (160, 550), None, False)

                # Draw resign and offer draw button
                resign.draw(self.screen, self.DARK_BLACK,
                            self.LARGE_FONT, (600, 550), self.WHITE, False)
                offer_draw.draw(self.screen, self.DARK_BLACK,
                                self.LARGE_FONT, (750, 550), self.WHITE, False)

                # Change color when mouse hovers
                if resign.on_clicked(mouse_pos):
                    resign.toggle_color(True, False)
                else:
                    resign.toggle_color(False, False)
                if offer_draw.on_clicked(mouse_pos):
                    offer_draw.toggle_color(True, False)
                else:
                    offer_draw.toggle_color(False, False)

                # if the game ends
                if online_result:
                    online_result.draw(self.screen, self.RED,
                                       self.LARGE_FONT, (300, 300), None, False)
                    back_to_lobby = cg.Button_Text(
                        "Back to lobby", self.screen)
                    back_to_lobby.draw(self.screen, self.DARK_BLACK,
                                       self.LARGE_FONT, (675, 600), self.WHITE, False)
                    if back_to_lobby.on_clicked(mouse_pos):
                        back_to_lobby.toggle_color(True, False)
                    else:
                        back_to_lobby.toggle_color(False, False)

            if self.board.turn == "white":
                if self.flipped_view:
                    white_timer_pos = (575, 125)
                    black_timer_pos = (575, 475)
                else:
                    white_timer_pos = (575, 475)
                    black_timer_pos = (575, 125)
                self._display_time(self.screen, black_time,
                                   black_timer_pos, False)
                self._display_time(self.screen, white_time,
                                   white_timer_pos, True)
            else:
                if self.flipped_view:
                    white_timer_pos = (575, 125)
                    black_timer_pos = (575, 475)
                else:
                    white_timer_pos = (575, 475)
                    black_timer_pos = (575, 125)
                self._display_time(self.screen, black_time,
                                   black_timer_pos, True)
                self._display_time(self.screen, white_time,
                                   white_timer_pos, False)

            # if not multiplayer game then check this
            if not(self.multiplayer):
                # Checkmate
                if checkmate:
                    self._draw_text(self.screen, "Checkmate",
                                    self.RED, (300, 300))

                # Stalemate
                if stalemate:
                    self._draw_text(self.screen, "Stalemate",
                                    self.RED, (300, 300))

                # 3-fold draw
                if draw_by_3_fold:
                    self._draw_text(self.screen, "Draw by 3-fold repetition",
                                    self.RED, (300, 300))

                # Someone runs out of time
                if isinstance(ran_out_of_time, int):
                    if ran_out_of_time == 1:
                        self._draw_text(self.screen, "White runs out of time",
                                        self.RED, (300, 300))
                    elif ran_out_of_time == -1:
                        self._draw_text(self.screen, "Black runs out of time",
                                        self.RED, (300, 300))

                # Game ends then draw the save pgn button
                if checkmate or stalemate or draw_by_3_fold or isinstance(ran_out_of_time, int):
                    save_game_text = cg.Button_Text("Save game", self.screen)
                    save_game_text.draw(
                        self.screen, self.DARK_BLACK, self.LARGE_FONT, (670, 600), self.WHITE, False)
                    if save_game_text.on_clicked(mouse_pos):
                        save_game_text.toggle_color(True, False)
                    else:
                        save_game_text.toggle_color(False, False)

            # Find the square the mouse is on
            if hover:
                coor_square_on_hover = self._detect_square_on_mouse_hover(
                    mouse_pos)
            click = pygame.mouse.get_pressed()

            # Find the piece on the hovered square
            if coor_square_on_hover and click[0] and not(checkmate) and not(stalemate) and not(draw_by_3_fold) and not(isinstance(ran_out_of_time, int)):
                y, x = coor_square_on_hover
                selected_piece_img = self.board_piece_imgs[y][x]
                self._draw_selected_square(self.screen, coor_square_on_hover)

                # If there is a piece:
                if selected_piece_img != 0:
                    if self.flipped_view:
                        invert_y, invert_x = util.flipped_view_coor((y, x))
                        actual_piece = self.board.board[invert_y][invert_x]
                    else:
                        actual_piece = self.board.board[y][x]

                    # Offline game
                    if not(self.multiplayer):
                        # If the turn is the same as the color of the piece picked then allow the piece to be picked
                        if self.board.turn == actual_piece.color:
                            if self.flipped_view:
                                possible_moves = self._draw_possible_square_moves(
                                    self.screen, util.flipped_view_coor((y, x)))
                            else:
                                possible_moves = self._draw_possible_square_moves(
                                    self.screen, (y, x))
                            self._draw_dragging_piece(
                                self.screen, selected_piece_img, mouse_pos)

                    # Online game
                    elif not(online_result):
                        # If the current turn is the same as the board's current turn
                        if self.multiplayer_color == self.board.turn:
                            # If the piece picked has the same color as self.multiplayer_color
                            if self.multiplayer_color == actual_piece.color:
                                if self.flipped_view:
                                    possible_moves = self._draw_possible_square_moves(
                                        self.screen, util.flipped_view_coor((y, x)))
                                else:
                                    possible_moves = self._draw_possible_square_moves(
                                        self.screen, (y, x))
                                self._draw_dragging_piece(
                                    self.screen, selected_piece_img, mouse_pos)

            # Detect events in the menu
            for event in pygame.event.get():

                # Quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return -1

                # When holding the mouse down, disable hover update
                if event.type == pygame.MOUSEBUTTONDOWN:
                    hover = False

                    # For multiplayer,
                    if self.multiplayer:

                        # Check for clicking resign or offer draw button
                        if resign.on_clicked(mouse_pos):
                            print("Resign button pressed")
                            move_message_for_server = "resign"
                        if offer_draw.on_clicked(mouse_pos):
                            print("Offer draw button pressed")
                        # Check for back to lobby button

                        if isinstance(back_to_lobby, cg.Button_Text):
                            if back_to_lobby.on_clicked(mouse_pos):
                                print("Back to lobby button pressed")
                                move_message_for_server = "!back_lobby"

                    # Press the save button
                    if isinstance(save_game_text, cg.Button_Text):
                        if save_game_text.on_clicked(mouse_pos) and not(self.multiplayer) and not(game_saved):

                            # Start the saving process
                            if draw_by_3_fold or stalemate:
                                result = 0
                            elif checkmate:
                                result = 1 if self.board.turn == "black" else -1
                            elif isinstance(ran_out_of_time, int):
                                result = 1 if ran_out_of_time == -1 else -1
                            save_pgn = saveChessPGN(
                                self.board.pgn, result, self.mode, False)
                            save_pgn.save()
                            game_saved = True

                # When lifting the mouse up, enable hover update and record new piece
                if event.type == pygame.MOUSEBUTTONUP:
                    hover = True

                    # Update the board
                    mouse_pos_when_lifted = self._detect_square_on_mouse_hover(
                        mouse_pos)
                    if self.flipped_view and mouse_pos_when_lifted:
                        mouse_pos_when_lifted = util.flipped_view_coor(
                            mouse_pos_when_lifted)
                    else:
                        pass
                    if isinstance(possible_moves, list):
                        if mouse_pos_when_lifted in possible_moves:

                            # The move is valid, make the move in self.board
                            if self.flipped_view:
                                coor_square_on_hover_flipped = util.flipped_view_coor(
                                    coor_square_on_hover)
                                move_success = self.board.make_move_from_selected_square(
                                    possible_moves, coor_square_on_hover_flipped, mouse_pos_when_lifted, True, promotion_piece)
                            else:
                                move_success = self.board.make_move_from_selected_square(
                                    possible_moves, coor_square_on_hover, mouse_pos_when_lifted, True, promotion_piece)

                            # For multiplayer chess game
                            if self.multiplayer and move_success:

                                #   extract the move
                                if self.flipped_view:
                                    piece_to_move = coor_square_on_hover_flipped
                                else:
                                    piece_to_move = coor_square_on_hover
                                move = mouse_pos_when_lifted

                                # if the online_result has not been updated and resign button not pressed
                                if not(online_result) and move_message_for_server != "resign" and move_message_for_server != "!back_lobby":
                                    move_message_for_server = {
                                        "turn": self.multiplayer_color, "piece": piece_to_move, "move": move
                                    }
                                elif move_message_for_server != "resign" and move_message_for_server != "!back_lobby":
                                    move_message_for_server = "wait"
                                else:
                                    pass

                            # Check for checkmate or stalemate
                            opponent_possible_moves = self.board.find_all_possible_moves(
                                self.board.turn)
                            # No possible moves then checkmate or stalemate
                            if opponent_possible_moves == -100:
                                checkmate = True
                            if opponent_possible_moves == -50:
                                stalemate = True

                            # 3-fold repetition
                            if self.board.is_draw_by_3_fold():
                                draw_by_3_fold = True

                    # Reset the values of the variables
                    possible_moves = None
                    coor_square_on_hover = None
                    selected_piece_img = None

                if event.type == pygame.MOUSEWHEEL:

                    if pgn_screen_rect.collidepoint(mouse_pos):

                        # Scroll down then take the threshold
                        if event.y == -1 and pgn_starting_point < (self.board.num_of_moves - 16) / 2:
                            pgn_starting_point += -(event.y)
                        elif event.y == 1 and pgn_starting_point > 0:
                            pgn_starting_point += -(event.y)

                    # Scroll down is -1
                    # Scroll up is 1

                # Hold down a key for promotion piece (if there is any)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        promotion_piece = "knight"
                    if event.key == pygame.K_q:
                        promotion_piece = "queen"
                    if event.key == pygame.K_b:
                        promotion_piece = "bishop"
                    if event.key == pygame.K_r:
                        promotion_piece = "rook"
                    if event.key == pygame.K_SPACE:
                        self.flipped_view = not(self.flipped_view)

            #self._draw_dragging_piece(self.screen, selected_piece_img, mouse_pos)
            pygame.display.update()


class mainGameGUI_hab(mainGameGUI):
    def __init__(self, mode, screen, network_api):
        super().__init__(mode, screen, network_api)
        self.curr_role, self.curr_color = None, None
        self.friend_name, self.friend_role = None, None
        self.opponent_hand_name, self.opponent_brain_name = None, None
        self.opponent_color = None

    def _get_data(self):
        """ Get the data from the server about the 4 players """
        try:
            data = self.n.send("data")
            self.opponent_hand_name = data["opponent_hand_name"]
            self.opponent_brain_name = data["opponent_brain_name"]
            self.friend_name = data["friend_name"]
            self.curr_color = data["curr_color"]
            self.curr_role = data["curr_role"]
            self.opponent_color = "white" if self.curr_color == "black" else "black"
            self.friend_role = "hand" if self.curr_role == "brain" else "brain"

            # if color is Black then flip view
            if self.curr_color == "black":
                self.flipped_view = True

            print("[CLIENT Hab] Opponent hand: " + self.opponent_hand_name)
            print("[CLIENT Hab] Opponent brain: " + self.opponent_brain_name)
            print("[CLIENT Hab] Friend: " + self.friend_name)
            print("[CLIENT Hab] Friend role: " + self.friend_role)
            print("[CLIENT Hab] Current color: " + self.curr_color)

        except Exception as e:
            print("[CLIENT Hab] Cannot send or receive data")
            print(e)

    def initialize(self):
        """ Get the color and role of all 4 players """
        self.board_surface = self.draw_chessboard((25, 25), self.SQUARE_SIZE)
        self._get_data()
        print("[CLIENT hab] Done extracting data")

    def event_listener(self):
        """ Launch the GUI of the chess board
        This method is also the listener to most of the events """
        hover = True
        selected_piece_img = None
        checkmate, stalemate, draw_by_3_fold = False, False, False
        possible_moves = None
        coor_square_on_hover = None
        pgn_screen_rect = None
        selected_piece_by_brain = "empty"
        move_message_for_server = "wait"
        promotion_piece = "queen"
        pgn_starting_point = 0

        # Only draw a set of pieces when curr_role is the brain
        online_result = None
        back_to_lobby = None
        if self.curr_role == "brain":
            pieces_img_hab = [
                cg.Button_Img("img\\" + self.curr_color +
                              "pawn.png", self.screen),
                cg.Button_Img("img\\" + self.curr_color +
                              "knight.png", self.screen),
                cg.Button_Img("img\\" + self.curr_color +
                              "bishop.png", self.screen),
                cg.Button_Img("img\\" + self.curr_color +
                              "rook.png", self.screen),
                cg.Button_Img("img\\" + self.curr_color +
                              "king.png", self.screen),
                cg.Button_Img("img\\" + self.curr_color +
                              "queen.png", self.screen),
            ]

        # Names of players
        opponent_brain_text = cg.Button_Text(
            self.opponent_brain_name + " (brain)", self.screen)
        opponent_hand_text = cg.Button_Text(
            self.opponent_hand_name + " (hand)", self.screen)
        curr_text = cg.Button_Text(
            "You" + " (" + self.curr_role + ")", self.screen)
        friend_text = cg.Button_Text(
            self.friend_name + " (" + self.friend_role + ")", self.screen)

        # Waiting text
        brain_is_deciding_text = cg.Button_Text(
            "Brain is choosing a piece", self.screen)
        hand_is_making_move_text = cg.Button_Text(
            "Hand is making a move", self.screen)

        # Resign and offer draw button
        resign = cg.Button_Text("Resign", self.screen)
        offer_draw = cg.Button_Text("Offer draw", self.screen)

        # Implement timer
        clock = pygame.time.Clock()
        white_time, black_time = self.TIME_LIMIT, self.TIME_LIMIT
        clock.tick()

        while True:

            # Reset the screen
            self.screen.fill((self.SKIN_COLOR))

            try:
                # Player has pressed the back to lobby button
                if move_message_for_server == "!back_lobby":
                    reply_from_server = self.n.send(
                        move_message_for_server)
                    self.screen.fill((self.SKIN_COLOR))
                    return 1

                # if curr_role is hand then receive the piece from the brain (if any)
                try:
                    if self.curr_role == "hand":
                        #print("[CLIENT] Current role is hand, sending request")
                        piece_from_brain = self.n.send(
                            {"command": "!piece", "color": self.curr_color, "role": "hand"})
                        # print("[CLIENT hab] Piece from brain: ",
                        #     piece_from_brain)
                        if piece_from_brain == "No" and self.curr_color == self.board.turn:
                            piece_from_brain = None
                            # (725, 640)
                            brain_is_deciding_text.draw(
                                self.screen, self.RED, self.LARGE_FONT, (600, 600), None, None)

                except Exception as e:
                    print("[CLIENT Hab] (1) An error occurred")
                    print(e)

                # if curr_role is brain then receive the noti from the server saying it has received the piece by the brain
                try:
                    if self.curr_role == "brain":
                        reply = self.n.send(
                            {"role": "brain", "color": self.curr_color, "piece": selected_piece_by_brain})

                        if reply != "Brain No" and self.curr_color == self.board.turn:
                            hand_is_making_move_text.draw(
                                self.screen, self.RED, self.LARGE_FONT, (600, 600), None, None)
                            #print("[CLIENT hab] Reply: ", reply)

                except Exception as e:
                    print("[CLIENT Hab] (2) An error occurred")
                    print(e)

                # Send the move_pgn to the server if a valid move has been made
                reply_from_server = self.n.send(move_message_for_server)
                # print("[CLIENT] Message received from server: ",
                #     reply_from_server)

                # if game has not ended, the reply is a dict
                if isinstance(reply_from_server, dict):
                    #print("[CLIENT hab] Reply from server: ", reply_from_server)
                    game_from_server = reply_from_server["game"]
                    curr_turn_server_board = reply_from_server["curr_turn"]

                    # if game from server is different from local game then make an update
                    if game_from_server != self.board:
                        self.board = game_from_server       # Need copy.deepcopy() here?
                        self.board.turn = curr_turn_server_board
                        #print("[CLIENT] Chessboard updated")

                    # Set the message to "wait"
                    if move_message_for_server != "wait" and move_message_for_server != "resign" and move_message_for_server != "!back_lobby" and self.curr_role == "hand":
                        move_message_for_server = "wait"

                # else,
                elif isinstance(reply_from_server, str):

                    # The game ends
                    print("[CLIENT] Game ends")

                    # Draw by stalemate
                    if reply_from_server == "stalemate":
                        online_result = cg.Button_Text(
                            "Stalemate: You draw", self.screen)

                    # Draw by some other draw
                    elif reply_from_server == "draw":
                        online_result = cg.Button_Text(
                            "You draw", self.screen)

                    # Game ended by resignation
                    elif reply_from_server.find("resignation") >= 0:
                        online_result = cg.Button_Text(
                            reply_from_server, self.screen)

                    # Game ended by checkmate
                    else:
                        reason_game_end, win_loss = reply_from_server.split(
                            ",")[0], reply_from_server.split(",")[1]
                        online_result = cg.Button_Text(
                            reason_game_end + ": You " + win_loss, self.screen)

            except:
                print(
                    "[CLIENT] An error occurred while sending move or retrieving data")

            # Time passed (in second)
            sec_elapsed = clock.tick() / 1000

            # Check for whose turn it is to subtract the time (and when the game is not over)
            if not(checkmate) and not(stalemate) and not(draw_by_3_fold):
                if self.board.turn == "white":
                    white_time = white_time - sec_elapsed
                else:
                    black_time = black_time - sec_elapsed

            # Get mouse current position
            mouse_pos = pygame.mouse.get_pos()

            # Draw everything
            self.screen.blit(self.board_surface, self.BOARD_POS)
            self.draw_all_pieces(self.screen, (25, 25), self.SQUARE_SIZE)
            pgn_screen_rect = self._draw_pgn(self.screen, pgn_starting_point)

            # Draw the names (50, 550)
            opponent_brain_text.draw(
                self.screen, self.DARK_BLACK, self.SMALL_FONT, (150, 50), None, False)
            opponent_hand_text.draw(
                self.screen, self.DARK_BLACK, self.SMALL_FONT, (350, 50), None, False)
            curr_text.draw(
                self.screen, self.DARK_BLACK, self.SMALL_FONT, (150, 550), None, False)
            friend_text.draw(
                self.screen, self.DARK_BLACK, self.SMALL_FONT, (350, 550), None, False)

            # Draw resign and offer draw button (only for the brain)
            if self.curr_role == "brain":
                resign.draw(self.screen, self.DARK_BLACK,
                            self.LARGE_FONT, (600, 550), self.WHITE, False)
                offer_draw.draw(self.screen, self.DARK_BLACK,
                                self.LARGE_FONT, (750, 550), self.WHITE, False)

                # Change color when mouse hovers
                if resign.on_clicked(mouse_pos):
                    resign.toggle_color(True, False)
                else:
                    resign.toggle_color(False, False)
                if offer_draw.on_clicked(mouse_pos):
                    offer_draw.toggle_color(True, False)
                else:
                    offer_draw.toggle_color(False, False)

            # if current mode is hand and brain, and this is the brain
            if self.curr_role == "brain":
                for i, piece_img_hab in enumerate(pieces_img_hab):
                    piece_img_hab.draw((175 + i*50, 620))
                    piece_img_hab.toggle_color(mouse_pos)

            # if the game ends
            if online_result:
                online_result.draw(self.screen, self.RED,
                                   self.LARGE_FONT, (300, 300), None, False)
                back_to_lobby = cg.Button_Text(
                    "Back to lobby", self.screen)
                back_to_lobby.draw(self.screen, self.DARK_BLACK,
                                   self.LARGE_FONT, (675, 600), self.WHITE, False)
                if back_to_lobby.on_clicked(mouse_pos):
                    back_to_lobby.toggle_color(True, False)
                else:
                    back_to_lobby.toggle_color(False, False)

            if self.board.turn == "white":
                if self.flipped_view:
                    white_timer_pos = (575, 125)
                    black_timer_pos = (575, 475)
                else:
                    white_timer_pos = (575, 475)
                    black_timer_pos = (575, 125)
                self._display_time(self.screen, black_time,
                                   black_timer_pos, False)
                self._display_time(self.screen, white_time,
                                   white_timer_pos, True)
            else:
                if self.flipped_view:
                    white_timer_pos = (575, 125)
                    black_timer_pos = (575, 475)
                else:
                    white_timer_pos = (575, 475)
                    black_timer_pos = (575, 125)
                self._display_time(self.screen, black_time,
                                   black_timer_pos, True)
                self._display_time(self.screen, white_time,
                                   white_timer_pos, False)

            # Find the square the mouse is on
            if hover:
                coor_square_on_hover = self._detect_square_on_mouse_hover(
                    mouse_pos)
            click = pygame.mouse.get_pressed()

            # The current role is the brain
            if self.curr_role == "brain":
                if selected_piece_by_brain != "empty":
                    selected_piece_has_possible_moves = self.board._check_selected_piece_by_brain(
                        selected_piece_by_brain, self.curr_color)
                    if not(selected_piece_has_possible_moves):
                        print("[CLIENT] Oh no")
                        selected_piece_by_brain = "empty"

            # Find the piece on the hovered square
            if coor_square_on_hover and click[0] and not(checkmate) and not(stalemate) and self.curr_role == "hand" and selected_piece_by_brain:
                y, x = coor_square_on_hover
                selected_piece_img = self.board_piece_imgs[y][x]
                self._draw_selected_square(self.screen, coor_square_on_hover)

                # If there is a piece:
                if selected_piece_img != 0 and piece_from_brain in ["pawn", "knight", "bishop", "rook", "king", "queen"]:
                    if self.flipped_view:
                        invert_y, invert_x = util.flipped_view_coor((y, x))
                        actual_piece = self.board.board[invert_y][invert_x]
                    else:
                        actual_piece = self.board.board[y][x]

                    # Online game
                    if not(online_result):
                        # If the current turn is the same as the board's current turn
                        if self.curr_color == self.board.turn:
                            # If the piece picked has the same color as self.curr_color
                            # and the piece picked is similar to the piece from the brain
                            if self.curr_color == actual_piece.color and actual_piece.name == piece_from_brain:
                                if self.flipped_view:
                                    possible_moves = self._draw_possible_square_moves(
                                        self.screen, util.flipped_view_coor((y, x)))
                                else:
                                    possible_moves = self._draw_possible_square_moves(
                                        self.screen, (y, x))
                                self._draw_dragging_piece(
                                    self.screen, selected_piece_img, mouse_pos)

            # Detect events in the menu
            for event in pygame.event.get():

                # Quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return -1

                # When holding the mouse down, disable hover update
                if event.type == pygame.MOUSEBUTTONDOWN:
                    hover = False
                    piece_names = ["pawn", "knight",
                                   "bishop", "rook", "king", "queen"]

                    # exclusive for the brain
                    if self.curr_role == "brain" and selected_piece_by_brain == "empty":
                        for i, piece_img_hab in enumerate(pieces_img_hab):
                            if piece_img_hab.on_clicked(mouse_pos):
                                selected_piece_by_brain = piece_names[i]
                    print("[CLIENT] Selected piece by brain: ",
                          selected_piece_by_brain)

                    # Check for clicking resign or offer draw button (only for the brain)
                    if self.curr_role == "brain":
                        if resign.on_clicked(mouse_pos):
                            print("Resign button pressed")
                            move_message_for_server = "resign"
                        if offer_draw.on_clicked(mouse_pos):
                            print("Offer draw button pressed")

                    # Check for back to lobby button
                    if isinstance(back_to_lobby, cg.Button_Text):
                        if back_to_lobby.on_clicked(mouse_pos):
                            print("Back to lobby button pressed")
                            move_message_for_server = "!back_lobby"

                # When lifting the mouse up, enable hover update and record new piece
                if event.type == pygame.MOUSEBUTTONUP:
                    hover = True

                    # Update the board
                    mouse_pos_when_lifted = self._detect_square_on_mouse_hover(
                        mouse_pos)
                    if self.flipped_view and mouse_pos_when_lifted:
                        mouse_pos_when_lifted = util.flipped_view_coor(
                            mouse_pos_when_lifted)

                    # This task is only for the hand
                    if self.curr_role == "hand":
                        if isinstance(possible_moves, list):
                            if mouse_pos_when_lifted in possible_moves:

                                # The move is valid, make the move in self.board
                                if self.flipped_view:
                                    coor_square_on_hover_flipped = util.flipped_view_coor(
                                        coor_square_on_hover)
                                    move_success = self.board.make_move_from_selected_square(
                                        possible_moves, coor_square_on_hover_flipped, mouse_pos_when_lifted, True, promotion_piece)
                                else:
                                    move_success = self.board.make_move_from_selected_square(
                                        possible_moves, coor_square_on_hover, mouse_pos_when_lifted, True, promotion_piece)

                                # For multiplayer chess game
                                if move_success:

                                    #   extract the move
                                    if self.flipped_view:
                                        piece_to_move = coor_square_on_hover_flipped
                                    else:
                                        piece_to_move = coor_square_on_hover
                                    move = mouse_pos_when_lifted

                                    # if the online_result has not been updated and resign button not pressed
                                    if not(online_result) and move_message_for_server != "resign" and move_message_for_server != "!back_lobby":
                                        move_message_for_server = {
                                            "color": self.curr_color, "piece": piece_to_move, "move": move, "role": "hand"
                                        }
                                    elif move_message_for_server != "resign" and move_message_for_server != "!back_lobby":
                                        move_message_for_server = "wait"
                                    else:
                                        pass

                                # Check for checkmate or stalemate
                                opponent_possible_moves = self.board.find_all_possible_moves(
                                    self.board.turn)
                                # No possible moves then checkmate or stalemate
                                if opponent_possible_moves == -100:
                                    checkmate = True
                                if opponent_possible_moves == -50:
                                    stalemate = True

                                # 3-fold repetition
                                if self.board.is_draw_by_3_fold():
                                    draw_by_3_fold = True

                    # Reset the values of the variables
                    possible_moves = None
                    coor_square_on_hover = None
                    selected_piece_img = None

                if event.type == pygame.MOUSEWHEEL:

                    if pgn_screen_rect.collidepoint(mouse_pos):

                        # Scroll down then take the threshold
                        if event.y == -1 and pgn_starting_point < (self.board.num_of_moves - 16) / 2:
                            pgn_starting_point += -(event.y)
                        elif event.y == 1 and pgn_starting_point > 0:
                            pgn_starting_point += -(event.y)

                    # Scroll down is -1
                    # Scroll up is 1

                # Hold down a key for promotion piece (if there is any)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        promotion_piece = "knight"
                    if event.key == pygame.K_q:
                        promotion_piece = "queen"
                    if event.key == pygame.K_b:
                        promotion_piece = "bishop"
                    if event.key == pygame.K_r:
                        promotion_piece = "rook"

            #self._draw_dragging_piece(self.screen, selected_piece_img, mouse_pos)
            pygame.display.update()


class mainGameGUI_blind(mainGameGUI):
    def __init__(self, mode, screen, network_api=None):
        super().__init__(mode, screen, network_api)
        self.voice_listener = voiceChess("en-US")
        self.display_board_duration = 3

    def initialize(self):
        """ 
        Draw the chessboard, load the pieces, create the chessboard object 
        If multiplayer, then request opponent name and player color
        """
        self.board_surface = self.draw_chessboard((25, 25), self.SQUARE_SIZE)
        if self.multiplayer:
            self._get_opponent_name()
            self._get_my_color()

    def event_listener(self):
        """ 
        The main event loop
        """
        checkmate, stalemate, draw_by_3_fold = False, False, False
        game_saved, display_board = False, False
        save_game_text, result_text = None, None
        possible_moves = None
        coor_square_on_hover = None
        pgn_screen_rect = None
        ran_out_of_time, timer_for_display_board = None, None
        move_message_for_server = "wait"
        promotion_piece = "queen"
        pgn_starting_point = 0

        # For multiplayer only
        online_result = None
        back_to_lobby = None

        # Names of both players
        # TODO

        # Display board pieces and turning on mic
        display_board_button = cg.Button_Text("Display board", self.screen)
        turn_mic_on_button = cg.Button_Text("Record move", self.screen)

        # Text for saving game
        game_saved_text = cg.Button_Text("Game has been saved", self.screen)

        # Implement timer
        clock = pygame.time.Clock()
        white_time, black_time = self.TIME_LIMIT, self.TIME_LIMIT
        clock.tick()

        while True:

            # Multiplayer sending and receiving data
            # TODO

            # Time passed (in second)
            sec_elapsed = clock.tick() / 1000

            # Check for whose turn it is to subtract the time (and when the game is not over)
            if not(checkmate) and not(stalemate) and not(draw_by_3_fold) and not(isinstance(ran_out_of_time, int)):
                if self.board.turn == "white":
                    white_time = white_time - sec_elapsed
                else:
                    black_time = black_time - sec_elapsed

                # Check when one of the clocks runs out (not for multiplayer)
                if not(self.multiplayer):
                    if white_time < 0:
                        ran_out_of_time = 1
                    elif black_time < 0:
                        ran_out_of_time = -1

            # Get mouse current position
            mouse_pos = pygame.mouse.get_pos()

            # Draw everything
            self.screen.fill((self.SKIN_COLOR))
            self.screen.blit(self.board_surface, self.BOARD_POS)
            pgn_screen_rect = self._draw_pgn(self.screen, pgn_starting_point)
            display_board_button.draw(
                self.screen, self.RED, self.LARGE_FONT, (200, 600), self.WHITE, None)
            turn_mic_on_button.draw(
                self.screen, self.RED, self.LARGE_FONT, (400, 600), self.WHITE, None)

            if display_board_button.on_clicked(mouse_pos):
                display_board_button.toggle_color(True, False)
            else:
                display_board_button.toggle_color(False, False)

            if turn_mic_on_button.on_clicked(mouse_pos):
                turn_mic_on_button.toggle_color(True, False)
            else:
                turn_mic_on_button.toggle_color(False, False)

            # The game has been saved
            if game_saved:
                game_saved_text.draw(self.screen, self.RED,
                                     self.SMALL_FONT, (670, 550), None, False)

            # If the display button is pressed, then display the piece
            if display_board:
                time_elapsed = time.time()
                if (time_elapsed - timer_for_display_board < self.display_board_duration):
                    # Since the display button is pressed, the time elapsed is not yet 3 seconds
                    self.draw_all_pieces(
                        self.screen, (25, 25), self.SQUARE_SIZE)

                else:
                    # After the button is pressed, reset the variables
                    timer_for_display_board, display_board = None, False

            # Draw timer
            if self.flipped_view:
                white_timer_pos = (575, 125)
                black_timer_pos = (575, 475)
            else:
                white_timer_pos = (575, 475)
                black_timer_pos = (575, 125)

            if self.board.turn == "white":
                black_turn, white_turn = False, True
            else:
                black_turn, white_turn = True, False

            self._display_time(self.screen, black_time,
                               black_timer_pos, black_turn)
            self._display_time(self.screen, white_time,
                               white_timer_pos, white_turn)

            # if not multiplayer game then check this
            if not(self.multiplayer):
                # Checkmate
                if checkmate:
                    result_text = "Checkmate"

                # Stalemate
                if stalemate:
                    result_text = "Stalemate"

                # 3-fold draw
                if draw_by_3_fold:
                    result_text = "Draw by 3-fold repetition"

                # Someone runs out of time
                if isinstance(ran_out_of_time, int):
                    if ran_out_of_time == 1:
                        result_text = "White runs out of time"
                    elif ran_out_of_time == -1:
                        result_text = "Black runs out of time"

                # Draw the result
                if result_text:
                    self._draw_text(self.screen, result_text,
                                    self.RED, (300, 300))

                # Game ends then draw the save pgn button
                if result_text:
                    save_game_text = cg.Button_Text("Save game", self.screen)
                    save_game_text.draw(
                        self.screen, self.DARK_BLACK, self.LARGE_FONT, (670, 600), self.WHITE, False)
                    if save_game_text.on_clicked(mouse_pos):
                        save_game_text.toggle_color(True, False)
                    else:
                        save_game_text.toggle_color(False, False)

            # Detect events in the menu
            for event in pygame.event.get():

                # Quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return -1

                # When holding the mouse down, disable hover update
                if event.type == pygame.MOUSEBUTTONDOWN:

                    # Press the save button
                    if isinstance(save_game_text, cg.Button_Text):
                        if save_game_text.on_clicked(mouse_pos) and not(self.multiplayer) and not(game_saved):

                            # Start the saving process
                            if draw_by_3_fold or stalemate:
                                result = 0
                            elif checkmate:
                                result = 1 if self.board.turn == "black" else -1
                            elif isinstance(ran_out_of_time, int):
                                result = 1 if ran_out_of_time == -1 else -1
                            save_pgn = saveChessPGN(
                                self.board.pgn, result, self.mode, False)
                            save_pgn.save()
                            game_saved = True

                    # Press the display board button to display board in a certain seconds
                    if display_board_button.on_clicked(mouse_pos) and not(timer_for_display_board):
                        display_board = True
                        timer_for_display_board = time.time()

                    # Press the mic to record the move

                # When lifting the mouse up, enable hover update and record new piece
                if event.type == pygame.MOUSEBUTTONUP:

                    # Reset the values of the variables
                    possible_moves = None
                    coor_square_on_hover = None
                    selected_piece_img = None

                if event.type == pygame.MOUSEWHEEL:

                    if pgn_screen_rect.collidepoint(mouse_pos):

                        # Scroll down then take the threshold
                        if event.y == -1 and pgn_starting_point < (self.board.num_of_moves - 16) / 2:
                            pgn_starting_point += -(event.y)
                        elif event.y == 1 and pgn_starting_point > 0:
                            pgn_starting_point += -(event.y)

                    # Scroll down is -1
                    # Scroll up is 1

                # Hold down a key for promotion piece (if there is any)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        promotion_piece = "knight"
                    if event.key == pygame.K_q:
                        promotion_piece = "queen"
                    if event.key == pygame.K_b:
                        promotion_piece = "bishop"
                    if event.key == pygame.K_r:
                        promotion_piece = "rook"
                    if event.key == pygame.K_SPACE:
                        self.flipped_view = not(self.flipped_view)

            #self._draw_dragging_piece(self.screen, selected_piece_img, mouse_pos)
            pygame.display.update()


if __name__ == "__main__":
    pass
