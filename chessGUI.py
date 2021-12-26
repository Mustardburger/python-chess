import pygame
import chessboard as cb
import chessPieces as cp
import util
from network_api import Network_API
import gameGUI as gg


class Button_Text():
    def __init__(self, text, screen):
        self.text = text
        self.screen = screen
        self.rect = None
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.LARGE_FONT = pygame.font.Font("OpenSans-Regular.ttf", 30)
        self.font = None
        self.text_color = None

    def draw(self, screen, text_color, font, center_pos, background_color=None, update_display=True):
        """ Draw a button given the necessary parameters """
        button = font.render(self.text, True, text_color)
        button_rect = button.get_rect()
        button_rect.center = center_pos
        self.rect = button_rect
        self.font = font
        self.text_color = text_color

        # If background_color is not None:
        if background_color:
            pygame.draw.rect(screen, background_color, button_rect)

        screen.blit(button, button_rect)

        if update_display:
            pygame.display.update()

    def on_clicked(self, pos):
        """ Check if pos is on the button """
        try:
            return self.rect.collidepoint(pos)
        except:
            return False

    def toggle_color(self, on_hover, update_display=True):
        """ Change the color of the button when the mouse hovers on it """

        center_pos = self.rect.center
        # The mouse is over the button
        if on_hover:
            self.draw(
                self.screen, self.WHITE, self.LARGE_FONT, center_pos, self.RED, update_display
            )

        # The mouse is not over the button
        else:
            self.draw(
                self.screen, self.BLACK, self.LARGE_FONT, center_pos, self.WHITE, update_display
            )

    def clear_text(self, color):
        """ Clear the text with the color"""
        self.screen.fill(color, self.rect)

    def update_text(self, new_text):
        """ Update the text without changing the location of text or text color """
        self.text = new_text


class Button_Img():
    def __init__(self, img_link, screen):
        self.img = pygame.image.load(img_link)
        self.screen = screen
        self.rect = self.img.get_rect()
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)

    def draw(self, center_pos):
        """ Draw the img at the specified location """
        self.rect.center = center_pos
        pygame.draw.rect(self.screen, self.WHITE, self.rect)
        self.screen.blit(self.img, self.rect)

    def toggle_color(self, mouse_pos):
        """ Draw a bounding box around the img if the mouse_pos is on the img """
        if self.on_clicked(mouse_pos):
            pygame.draw.rect(self.screen, self.RED, self.rect, 5)

    def on_clicked(self, mouse_pos):
        """ Check if mouse_pos is on the button """
        try:
            return self.rect.collidepoint(mouse_pos)
        except:
            return False


class mainGUI():
    def __init__(self):
        self.height, self.width = 700, 900
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.SKIN_COLOR = (241, 194, 125)
        self.player_name = self.register_player()

        # Initialize the window
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Chess 1.0")
        self.screen.fill((self.SKIN_COLOR))
        pygame.display.update()

    def register_player(self):
        """ Take input the name of the player in the terminal """
        return input("Please type in your name to start the game: ")

    def _clean_screen(self, color):
        """ Clean the whole screen with the color """
        self.screen.fill(color)
        pygame.display.update()

    def launch(self):
        """
        Launching the main GUI of the game
        """
        intro_menu = introMenu(
            self.screen, (self.BLACK, self.SKIN_COLOR), (self.width, self.height), self.player_name)
        event = intro_menu.launch()

        # Standard offline mode
        if event == 0:
            self._clean_screen(self.SKIN_COLOR)
            chessboard_gui = gg.mainGameGUI_blind("standard", self.screen)
            chessboard_gui.initialize()
            chessboard_gui.event_listener()

        # Chess960 offline mode
        elif event == 1:
            self._clean_screen(self.SKIN_COLOR)
            chessboard_gui = gg.mainGameGUI("960", self.screen)
            chessboard_gui.initialize()
            chessboard_gui.event_listener()

        # Multiplayer mode
        elif event == 2:
            self._clean_screen(self.SKIN_COLOR)

            # When the player presses this button, a new connection is established to the server
            n = Network_API()
            message = n.connect()
            # message = "z"   # For debugging only

            if message == "!fail" or not(message):
                print("Connection failed")
                return -1
            else:
                message = n.send_request(self.player_name)
                if message == "OK":

                    # Start the game loop
                    while True:
                        lobby_gui = multiplayerLobbyGUI(
                            self.screen, (self.BLACK, self.SKIN_COLOR), n, self.player_name)
                        game_type = lobby_gui.launch()

                        if isinstance(game_type, int):

                            # game_type = 0 then Standard game
                            if game_type == 0:
                                game = gg.mainGameGUI(
                                    "standard", self.screen, n)
                                game.initialize()
                                back_to_lobby = game.event_listener()
                            # game_type = 1 then 960
                            if game_type == 1:
                                game = gg.mainGameGUI("960", self.screen, n)
                                game.initialize()
                                back_to_lobby = game.event_listener()
                            # game_type = -1 then player has quitted
                            if game_type == -1:
                                print("Pygame quitted")
                                return -1
                            # game_type = 2 then Hand and Brain
                            if game_type == 2:
                                game = gg.mainGameGUI_hab(
                                    "hab", self.screen, n)
                                game.initialize()
                                back_to_lobby = game.event_listener()

                        if back_to_lobby == -1:
                            print("Pygame quitted")
                            return -1
                        else:
                            continue
        else:
            print("Pygame quitted")
            return -1


class introMenu():
    def __init__(self, screen, colors, size, name):
        self.screen = screen
        self.BLACK, self.SKIN_COLOR = colors
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.WIDTH, self.HEIGHT = size
        self.LARGE_FONT = pygame.font.Font("OpenSans-Regular.ttf", 30)
        self.SMALL_FONT = pygame.font.Font("OpenSans-Regular.ttf", 20)
        self.button_rects = []
        self.player_name = name
        self.text = "Hello " + self.player_name + ", welcome to Chess 1.0!"

    def draw(self):
        """Draw the main menu of the game"""

        intro = Button_Text(self.text, self.screen)
        standard = Button_Text(
            "Click here to play: Standard offline mode", self.screen)
        chess960 = Button_Text(
            "Click here to play: Chess960 offline mode", self.screen)
        multiplayer = Button_Text(
            "Click here to play: Multiplayer game", self.screen)

        self.button_rects = [standard, chess960, multiplayer]

        # Draw the texts (or buttons)
        intro.draw(self.screen, self.BLACK, self.LARGE_FONT,
                   (self.WIDTH / 2, 200), None)
        standard.draw(self.screen, self.BLACK, self.LARGE_FONT,
                      (self.WIDTH / 2, 300), self.WHITE)
        chess960.draw(self.screen, self.BLACK, self.LARGE_FONT,
                      (self.WIDTH / 2, 370), self.WHITE)
        multiplayer.draw(self.screen, self.BLACK, self.LARGE_FONT,
                         (self.WIDTH / 2, 440), self.WHITE)

    def launch(self):
        """ Launch the main menu """

        self.draw()

        # The waiting loop
        while True:

            # Change texture of button when mouse hovers over it
            pos = pygame.mouse.get_pos()

            for button in self.button_rects:
                if button.on_clicked(pos):
                    button.toggle_color(True)
                else:
                    button.toggle_color(False)

            # Detect events in the menu
            for event in pygame.event.get():

                # Quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return -1

                # Clicking action
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.button_rects):
                        if button.on_clicked(pos):
                            return i


class standardGameSetting():
    # TODO
    def __init__(self):
        pass


class multiplayerLobbyGUI():
    def __init__(self, screen, colors, n, curr_name):
        # Have several game options to choose from:
        # Standard game
        # Chess960 game
        # Hand and brain
        # Blindfold
        self.n = n
        self.screen = screen
        self.BLACK, self.SKIN_COLOR = colors
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.LARGE_FONT = pygame.font.Font("OpenSans-Regular.ttf", 30)
        self.SMALL_FONT = pygame.font.Font("OpenSans-Regular.ttf", 25)
        self.button_rects = []
        self.curr_name = curr_name

    def draw(self):
        """ Draw the lobby """

        onl_players = Button_Text("Current online players", self.screen)
        gamemode = Button_Text("Choose gamemode", self.screen)
        standard = Button_Text("Standard", self.screen)
        chess960 = Button_Text("Chess 960", self.screen)
        hand_and_brain = Button_Text("Hand and brain", self.screen)
        blind = Button_Text("Blind chess", self.screen)
        self.button_rects = [standard, chess960, hand_and_brain, blind]

        onl_players.draw(self.screen, self.BLACK, self.LARGE_FONT, (200, 50))
        gamemode.draw(self.screen, self.BLACK, self.LARGE_FONT, (675, 50))
        standard.draw(self.screen, self.BLACK,
                      self.LARGE_FONT, (675, 125), self.WHITE)
        chess960.draw(self.screen, self.BLACK,
                      self.LARGE_FONT, (675, 175), self.WHITE)
        hand_and_brain.draw(self.screen, self.BLACK,
                            self.LARGE_FONT, (675, 225), self.WHITE)
        blind.draw(self.screen, self.BLACK,
                   self.LARGE_FONT, (675, 275), self.WHITE)

        # Draw a frame
        online_players_rect = pygame.Rect(50, 100, 400, 450)
        pygame.draw.rect(self.screen, self.BLACK, online_players_rect, 5)

        # Update the view
        pygame.display.update()

    def draw_players(self, players_dict):
        """ Draw the players currently in the lobby """
        self.screen.fill(self.SKIN_COLOR, (55, 105, 390, 440))
        for i, player_id in enumerate(players_dict.keys()):
            player_name = players_dict[player_id]
            if player_name == self.curr_name:
                add = " (You)"
            else:
                add = ""
            img = self.SMALL_FONT.render(
                str(i+1) + ". " + player_name + add, True, self.BLACK)
            img_x = 65
            img_y = 125 + 30 * i
            self.screen.blit(img, (img_x, img_y))

    def launch(self):
        """ Launch the multiplayer lobby """
        self.draw()
        command_list = ["!standard", "!960", "!hab", "!blind"]
        prev_mode = 1000
        current_command = None
        message_received = None

        # Draw waiting for opponent text
        waiting_text = Button_Text("Waiting for opponent", self.screen)
        waiting_text.draw(self.screen, self.BLACK, self.SMALL_FONT, (650, 400))
        waiting_text.clear_text(self.SKIN_COLOR)

        # The waiting loop
        while True:

            # Change texture of button when mouse hovers over it
            pos = pygame.mouse.get_pos()
            for button_rect in self.button_rects:
                if button_rect.on_clicked(pos):
                    button_rect.toggle_color(True)
                else:
                    button_rect.toggle_color(False)

            # Get a list of players
            try:
                online_players = self.n.send_request("!get_player")
                if online_players:
                    self.draw_players(online_players)
            except:
                pass

            # Send continuous commands to the server
            try:
                if current_command:
                    message_received = self.n.send_request(current_command)
                    #print("[CLIENT] Message received: ", message_received)

                    # Chose the mode but no opponent
                    if message_received == "!OK" or message_received == "!wait":
                        waiting_text.update_text(
                            "Waiting for opponent")
                        waiting_text.clear_text(self.SKIN_COLOR)
                        waiting_text.draw(
                            self.screen, self.RED, self.SMALL_FONT, (650, 400))

                    # There is an opponent then display the opponent's name and start a new game
                    elif isinstance(message_received, str) and current_command != "!hab":
                        waiting_text.update_text(
                            "Opponent is: " + str(message_received))
                        waiting_text.clear_text(self.SKIN_COLOR)
                        waiting_text.draw(
                            self.screen, self.RED, self.SMALL_FONT, (650, 400))

                        # Returns 0 for Standard mode, 1 for 960, 3 for blind
                        return prev_mode

                    elif isinstance(message_received, str) and current_command == "!hab":
                        #print("[CLIENT] Message received " + message_received)
                        waiting_text.update_text("Yo WTF")
                        waiting_text.clear_text(self.SKIN_COLOR)
                        waiting_text.draw(
                            self.screen, self.RED, self.SMALL_FONT, (650, 400))
                        if "hand" in message_received or "brain" in message_received:
                            return prev_mode

            except Exception as e:
                print("[CLIENT] (5) Error: ")
                print(e)

            # Detect events in the menu
            for event in pygame.event.get():

                # Quitting the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return -1

                # A button is clicked
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, button_rect in enumerate(self.button_rects):
                        if button_rect.on_clicked(pos):

                            # Highlight the button
                            if prev_mode == i or prev_mode == 1000:
                                prev_mode = i
                                current_command = command_list[i]
                                pygame.draw.rect(
                                    self.screen, self.GREEN, button_rect.rect, 4)

            pygame.display.update()


if __name__ == "__main__":
    a = mainGUI()
    a.launch()
