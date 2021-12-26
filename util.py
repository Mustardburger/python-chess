def cartesian_to_sequential(coor, width, height):
    """ 
    Change from (x, y) position coordinate to the sequential index of the same square
    """
    y, x = coor
    return (height - y - 1) * width + x


def sequential_to_cartesian(num, width, height):
    """ 
    Change from the sequential index to the (x, y) position coordinate of the same square
    """
    x = num % width
    y = height - int(num / 8) - 1
    return (y, x)


def unravel(nested_list):
    """
    Unravel a list of lists into a flat list
    """
    return [item for sublist in nested_list for item in sublist]


def find_in_between_squares(start_pos, end_pos, start=True):
    """
    Return the squares between the start_pos square and the end_pos square, the start square inclusive
    If 2 squares are not on the same line, return None
    """
    li = []
    start_y, start_x = start_pos
    end_y, end_x = end_pos

    # Same row
    if start_y == end_y:
        a = end_x - start_x
        inc = a / abs(a)
        for i in range(abs(a)):
            li.append((start_y, int(start_x + i*inc)))

    # Same file
    elif start_x == end_x:
        a = end_y - start_y
        inc = a / abs(a)
        for i in range(abs(a)):
            li.append((int(start_y + i*inc), start_x))

    # Same diag
    else:
        end_ind, start_ind = cartesian_to_sequential(
            end_pos, 8, 8), cartesian_to_sequential(start_pos, 8, 8)
        a = (end_ind - start_ind) / 7
        b = (end_ind - start_ind) / 9
        if int(a) == a and (start_x - start_y == end_x - end_y):
            d = abs(a)
            c = abs(end_ind - start_ind) / a
        elif int(b) == b and (start_x + start_y == end_x + end_y):
            d = abs(b)
            c = abs(end_ind - start_ind) / b
        else:
            return None

        for i in range(int(d)):
            ind = start_ind + i*c
            y, x = sequential_to_cartesian(ind, 8, 8)
            li.append((int(y), int(x)))

    if not(start):
        li.remove(start_pos)

    return li


def from_sec_to_minsec(sec):
    """ Turn seconds into minutes and seconds """
    sec = int(sec) + 1
    curr_sec = sec % 60
    curr_min = sec // 60

    return (curr_min, curr_sec)


def find_pawn_attack(coor, color):
    """ Find the attack squares of a pawn"""

    attack_squares = []
    y, x = coor
    if color == "white":
        dy = -1
    else:
        dy = 1

    if x - 1 > -1:
        attack_squares.append((y + dy, x - 1))
    if x + 1 < 8:
        attack_squares.append((y + dy, x + 1))

    return attack_squares


def from_value_to_key(dict_obj, val_to_find):
    """ Find a key of a dict given a value """
    new_dict = {
        val: key for key, val in dict_obj.items()
    }
    return new_dict[val_to_find]


def flipped_view_coor(coor):
    """ When flipping the board from White's to Black's view, update the coor """
    coor_y, coor_x = coor
    return (7 - coor_y, 7 - coor_x)


def from_pgn_to_square_coor(pgn):
    """ Given the pgn of a square (for example d4), extract its actual square coor (d4 -> (4,3))"""
    # Pre-process
    ref = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    pgn = pgn.lower()

    if len(pgn) != 2:
        print("PGN of square not in correct format")
        return -1

    # Check for row and col
    col, row = pgn[0], pgn[1]
    coor_y = 8 - int(row)
    coor_x = ref.index(col)

    # return
    return (coor_y, coor_x)


if __name__ == "__main__":
    #print(find_in_between_squares((0,2), (7,4), False))
    #print(find_pawn_attack((3, 4), "black"))
    #a = {1: "z", 2: "y", 3: "x"}
    #print(from_value_to_key(a, "x"))
    print(from_pgn_to_square_coor("a7"))
