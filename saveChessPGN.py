from datetime import date, datetime
import time
import os

BASE_DIRECTORY = "PGN_past_games\\"


class saveChessPGN():
    def __init__(self, pgn, result, game_mode=None, multiplayer=False, players=None):
        self.pgn = pgn
        self.current_time = time.strftime('%H.%M')
        self.current_date = datetime.today().strftime('%Y-%m-%d')
        self.game_mode = game_mode
        self.is_multiplayer = multiplayer
        if self.is_multiplayer:
            self.dir = BASE_DIRECTORY + "Online_games\\"
        else:
            self.dir = BASE_DIRECTORY + "Offline_games\\"
        self.players = players
        self.result = self._change_result_format(result)

    def _create_txt_file(self, name):
        """ Create a new txt file """
        complete_name = os.path.join(self.dir, name + ".txt")
        with open(complete_name, "w") as f:
            pass
        return complete_name

    def _change_result_format(self, result):
        """ Change the format of the input result to the form 1-0, 0-1, or 1/2-1/2 """
        if result == 1:
            return "1-0"
        elif result == -1:
            return "0-1"
        elif result == 0:
            return "1/2-1/2"
        else:
            print("Error: Result not correct format")
            return -1

    def _create_content_list(self):
        """ Create a list of data (without pgn) """
        data_list = [
            "[" + "Date " + self.current_date + "]",
            "[" + "Time " + self.current_time + "]",
            "[" + "Multiplayer " + str(self.is_multiplayer) + "]",
            "[" + "Mode " + self.game_mode + "]",
        ]
        if self.players and isinstance(self.players, dict):
            black_player = self.players["black"]
            white_player = self.players["white"]
            data_list.append("[" + "White " + white_player + "]")
            data_list.append("[" + "Black " + black_player + "]")

        data_list.append("[" + "Result " + self.result + "]")
        return data_list

    def save(self):
        """ Save the PGN to the correct directory """
        # Create the file
        name_file = "[" + self.current_date + " " + self.current_time + "]"
        complete_name_file = self._create_txt_file(name_file)
        data_list = self._create_content_list()

        # Start writing in the file
        with open(complete_name_file, "w") as f:
            # Write all the data that is not the pgn
            f.write("\n".join(data_list))
            f.write("\n")
            f.write("\n")

            # Print the PGN
            num_of_moves = len(self.pgn)
            for i in range(num_of_moves):
                part_of_pgn = self.pgn[i*10:(i+1)*10]
                f.write("  ".join(part_of_pgn) + "\n")


if __name__ == "__main__":
    test_pgn = [
        '1. d4', '1... d5', '2. Nf3', '2... Nf6', '3. g3', '3... Bf5', '4. Bg2', '4... e6', '5. O-O', '5... Bd6', '6. b3', '6... O-O', '7. Bb2', '7... Nbd7', '8. Ne5', '8... c5', '9. e3', '9... Qc7', '10. f4', '10... cxd4', '11. exd4', '11... Qxc2', '12. Qxc2', '12... Bxc2', '13. Rc1', '13... Rac8', '14. Na3', '14... Bg6', '15. Nb5', '15... Bb8', '16. Ba3', '16... Rfd8', '17. Be7', '17... Re8', '18. Bd6', '18... Rxc1+', '19. Rxc1', '19... Nxe5', '20. dxe5', '20... Ne4', '21. Bxb8', '21... Rxb8', '22. Nxa7', '22... h6', '23. Rc7', '23... Bh5', '24. Nb5', '24... Be2', '25. Nd6', '25... Nxd6', '26. exd6', '26... Rd8', '27. Rxb7', '27... Rxd6', '28. Bf1', '28... Bd1', '29. Bd3', '29... d4', '30. Rb8+'
    ]
    a = saveChessPGN(test_pgn, 1, "Standard", False)
    a.save()
