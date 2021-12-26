# Check if all the packages are installed and can be imported
# if not, raise an error
# TODO

import os
import time
import pyaudio
import playsound
import speech_recognition as sr
from gtts import gTTS
import util

CHESSBOARD_SQUARES = [
    col + str(row) for col in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] for row in range(1, 9)
]
CHESSBOARD_PIECES = set(
    ["pawn", "knight", "rook", "bishop", "king", "queen"])
CASTLE = "castle"


class voiceChess():
    def __init__(self, language):

        # Check if all the packages are installed and can be imported
        # if not, raise an error
        # TODO
        self.recognizer = sr.Recognizer()
        self.language = language

        # Some autotune, including finding the working microphone and deleting background noise
        # TODO

    def _convert_move_predictions_to_move(self, move_predictions):
        """ Given a dictionary of predictions from the recognizer, extract the relevant move, if any 
        Returns a dict with the piece to move and the square to move to
        """
        if not(isinstance(move_predictions, dict)):
            return {}

        transcripts = move_predictions["alternative"]
        for transcript_dict in transcripts:
            piece_to_move, square_to_move = None, None
            transcript = transcript_dict["transcript"].lower()
            if CASTLE in transcript:
                # A castle move
                # TODO
                return {
                    "piece": "king", "move": "castle"
                }

            else:
                for piece in CHESSBOARD_PIECES:
                    if piece in transcript:
                        piece_to_move = piece
                        break

                # If there is no piece available then continue on the next transcript
                if not(piece_to_move):
                    continue
                else:
                    for square in CHESSBOARD_SQUARES:
                        if square in transcript:
                            square_to_move = util.from_pgn_to_square_coor(
                                square)
                            break
                    if square_to_move:
                        return {
                            "piece": piece_to_move, "move": square_to_move
                        }
        return {}

    def listen(self):
        """ Listen to the speech and extract the moves """
        move = None
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Ready to get microphone input")
            audio = self.recognizer.listen(source)
            move_predictions = ""

            try:
                move_predictions = self.recognizer.recognize_google(
                    audio, show_all=True)
                # print(move_predictions)
                move = self._convert_move_predictions_to_move(move_predictions)
                # print(move)
            except Exception as e:
                print("There's an error: " + str(e))

        if not(move):
            print("Cannot detect move")


if __name__ == "__main__":
    a = voiceChess("en-US")
    a.listen()

    # For debugging
    # transcripts = {'alternative': [{'transcript': '94', 'confidence': 0.97182459}, {'transcript': 'nicety for'}, {
    #    'transcript': 'nice D4'}, {'transcript': 'nice tea for'}, {'transcript': 'nice T4'}], 'final': True}
    # print(a._convert_move_predictions_to_move(transcripts))
