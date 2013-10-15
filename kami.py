import copy
import curses
import operator
import sys

from functools import reduce
from itertools import product

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

BOARD_WIDTH = 10
BOARD_HEIGHT = 16
BOARD_COORDS = list(product(range(BOARD_WIDTH), range(BOARD_HEIGHT)))

COLOR_INT_MAP = {'R': 1, 'K': 2, 'B': 3}
INT_COLOR_MAP = {1: 'red', 2: 'black', 3: 'blue'}
COLOR_MAP = {1: curses.COLOR_RED, 2: curses.COLOR_BLACK, 3: curses.COLOR_BLUE}

BOARDS = {
    'A1': ['R' * 10 ] * 8 + ['K' * 10] * 8,
    'A2': ['B' * 10] * 3 + ['BBRRRRRRBB'] * 10 + ['B' * 10] * 3,
    'A3': (['B' * 10] * 3
         + ['BBRRRRRRBB'] * 3
         + ['BBKKKKKKBB'] * 4
         + ['BBRRRRRRBB'] * 3
         + ['B' * 10] * 3),
    'A9': (['K' * 10]
         + ['KBBKBBBBBK']
         + ['KBBKBKKKBK']
         + ['KKKKBKRKBK']
         + ['KBBKBKKKBK']
         + ['KKKKBBBBBK']
         + ['K' * 10] * 2
         + ['KRRRRRRRRK']
         + ['KRKKKKKKRK']
         + ['KRKRRRRKRK']
         + ['KRKRBBRKRK']
         + ['KRKRRRRKRK']
         + ['KRKKKKKKRK']
         + ['KRRRRRRRRK']
         + ['K' * 10])
}


class Board(object):
    def __init__(self, initial_board):
        if len(initial_board) != BOARD_HEIGHT:
            raise Exception('Board has incorrect height: {} != {}'.format(BOARD_HEIGHT, len(initial_board)))
        if any(len(row) != BOARD_WIDTH for row in initial_board):
            raise Exception('Board has incorrect width on some row')

        self.board = copy.deepcopy(initial_board)

    def get(self, x, y):
        return self.board[y][x]

    def _set(self, x, y, color):
        self.board[y][x] = color

    def draw(self, screen, cursor):
        for x, y in BOARD_COORDS:
            rev = cursor == (x, y)
            color = curses.color_pair(self.get(x, y))

            attrs = color | (curses.A_REVERSE if rev else 0)

            screen.addstr(y, x, str(self.get(x, y)), attrs)

        screen.addstr(BOARD_HEIGHT + 1, 0, 'Done: {}'.format(self.is_done()))
        screen.addstr(BOARD_HEIGHT + 2, 0, 'Interesting Points: {}'.format(list(self.interesting_points())))
        screen.refresh()

    def replaced_color(self, x, y, new_color):
        old_color = self.get(x, y)
        if old_color == new_color:
            return self

        other = Board(self.board)

        for x, y in self.flood_fill_from(x, y):
            other._set(x, y, new_color)

        return other

    def flood_fill_from(self, x, y):
        old_color = self.get(x, y)

        q = Queue()
        q.put((x, y))

        visited = set()

        while not q.empty():
            x, y = q.get()
            if (x, y) in visited or self.get(x, y) != old_color:
                continue

            visited.add((x, y))

            if x - 1 >= 0:
                q.put((x-1, y))
            if x + 1 < BOARD_WIDTH:
                q.put((x+1, y))
            if y - 1 >= 0:
                q.put((x, y-1))
            if y + 1 < BOARD_HEIGHT:
                q.put((x, y+1))

        return visited

    def is_done(self):
        return list(self.interesting_points()) == [(0, 0)]

    def interesting_points(self):
        c = None

        skip = set()

        for x, y in BOARD_COORDS:
            if (x, y) in skip:
                continue

            new_c = self.get(x, y)
            if new_c != c:
                c = new_c
                skip.update(self.flood_fill_from(x, y))
                yield (x, y)

    def field_count(self):
        return len(list(self.interesting_points()))


class LinkedList(object):
    def __init__(self, head, tail):
        self.head, self.tail = head, tail

    def __iter__(self):
        n = self
        while n:
            yield n.head
            n = n.tail


def other_colors(color):
    if color == 1: return (2, 3)
    if color == 2: return (1, 3)
    if color == 3: return (1, 2)


def gen_options(board):
    for x, y in board.interesting_points():
        base_color = board.get(x, y)

        for color in other_colors(base_color):
            yield (x, y), color, board.replaced_color(x, y, color)


def get_solution_path(board, step, max_step):
    if step == max_step:
        return False

    if board.is_done():
        return None

    options = list(gen_options(board))
    options.sort(key=lambda t: t[2].field_count())

    for coord, color, option in options:
        path = get_solution_path(option, step + 1, max_step)

        if path != False:
            return LinkedList((coord, color), path)

    return False


def solve(board):
    limit = 1
    path = False

    while path is False:
        limit += 1
        print('Solving with step limit {}...'.format(limit - 1))
        path = get_solution_path(board, 0, limit)

        if limit == 10:
            print('I guess there\'s no solution...')
            return

    for (x, y), color in path:
        print('Color {},{} {}'.format(x, y, INT_COLOR_MAP[color]))


def main(screen, board):
    screen.clear()

    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)

    cursor_x, cursor_y = 0, 0


    running = True

    while running:
        screen.clear()
        board.draw(screen, (cursor_x, cursor_y))

        k = screen.getch()

        if chr(k) == 'q':
            running = False
        elif chr(k) in ('1', '2', '3'):
            board = board.replaced_color(cursor_x, cursor_y, int(chr(k)))
        elif k in (curses.KEY_UP, ','):
            cursor_y = max(0, cursor_y - 1)
        elif k in (curses.KEY_DOWN, 'o'):
            cursor_y = min(BOARD_WIDTH - 1, cursor_y + 1)
        elif k in (curses.KEY_LEFT, 'a'):
            cursor_x = max(0, cursor_x - 1)
        elif k in (curses.KEY_RIGHT, 'e'):
            cursor_x = min(BOARD_HEIGHT - 1, cursor_x + 1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} [solve] level'.format(sys.argv[0]))

        sys.exit(1)

    board_name = sys.argv[2 if sys.argv[1] == 'solve' else 1]
    run_solver = sys.argv[1] == 'solve'

    if board_name not in BOARDS:
        print('Unknown board: {}'.format(board_name))
        print()
        print('Available boards:')
        for k in BOARDS.keys():
            print('  {}'.format(k))

        sys.exit(1)

    board = Board([[COLOR_INT_MAP[c] for c in row] for row in BOARDS[board_name]])

    if run_solver:
        solve(board)
    elif not curses.wrapper(main, board):
        sys.exit(1)
