from chessdotcom import get_leaderboards, get_player_stats, get_player_games_by_month
import pprint
import re

printer = pprint.PrettyPrinter()

def get_player_rating(username):
    data = get_player_stats(username).json
    printer.pprint(data)

def get_player_games(username, year = 2021, month = 4):
    games = get_player_games_by_month(username, year, month).json
    pgn = list(games.values())[0][0]["pgn"]

    # Extract the players' names and ratings
    things_in_pgn = pgn.split("\n")
    print(len(things_in_pgn))
    for thing in things_in_pgn:
        check = re.findall("White", thing)
        if check:
            score = re.search(r"\"([A-Za-z0-9_]+)\"", thing)
            score = score.group(1)
            print(score)
            print("-------------------------")

    # Extract the game PGN
    pgn_moves = things_in_pgn[-2]
    time_moves = re.findall("\{.*?\}", pgn_moves)
    for time_move in time_moves:
        pgn_moves = pgn_moves.replace(time_move, "")
    pgn_moves_preprocessed = pgn_moves.split("  ")
    print(pgn_moves_preprocessed)


get_player_games("mustardburger")

