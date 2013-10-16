from __future__ import print_function

import copy
import curses
import operator
import sys
import time

from collections import namedtuple
from functools import reduce
from itertools import product

from kamigraph import graph_solve
from kamicommon import LinkedList

BOARD_WIDTH = 10
BOARD_HEIGHT = 16
BOARD_COORDS = list(product(range(BOARD_WIDTH), range(BOARD_HEIGHT)))


def other_colors3(color):
    if color == 1: return (2, 3)
    if color == 2: return (1, 3)
    if color == 3: return (1, 2)


def other_colors4(color):
    if color == 1: return (2, 3, 4)
    if color == 2: return (1, 3, 4)
    if color == 3: return (1, 2, 4)
    if color == 4: return (1, 2, 3)

OTHER_COLORS_FNS = {3: other_colors3, 4: other_colors4}


class ProblemSetup(object):
    def __init__(self, n_colors, color_chars, color_names, curses_pairs):
        self.n_colors = n_colors
        self.color_map = {c: i+1 for i, c in enumerate(color_chars)}
        self.color_names = {i+1: n for i, n in enumerate(color_names)}
        self.curses_pairs = curses_pairs
        self.other_colors = OTHER_COLORS_FNS[n_colors]

    def init_curses_colors(self):
        for i, (fg, bg) in enumerate(self.curses_pairs):
            curses.init_pair(i+1, fg, bg)


SETUPS = {
    'A': ProblemSetup(3, ['R', 'K', 'B'], ['red', 'black', 'blue'],
                      [(curses.COLOR_WHITE, curses.COLOR_RED),
                       (curses.COLOR_WHITE, curses.COLOR_BLACK),
                       (curses.COLOR_WHITE, curses.COLOR_BLUE)]),
    'B': ProblemSetup(4, ['R', 'K', 'W', 'Y'], ['red', 'black', 'white', 'yellow'],
                      [(curses.COLOR_WHITE, curses.COLOR_RED),
                       (curses.COLOR_WHITE, curses.COLOR_BLACK),
                       (curses.COLOR_BLACK, curses.COLOR_WHITE),
                       (curses.COLOR_BLACK, curses.COLOR_YELLOW)]),
    'C': ProblemSetup(4, ['B', 'R', 'C', 'O'], ['blue', 'red', 'cyan', 'orange'],
                      [(curses.COLOR_WHITE, curses.COLOR_BLUE),
                       (curses.COLOR_WHITE, curses.COLOR_RED),
                       (curses.COLOR_BLACK, curses.COLOR_CYAN),
                       (curses.COLOR_BLACK, curses.COLOR_YELLOW)]),
}


class Board(object):
    def __init__(self, initial_board):
        self.board = [row[:] for row in initial_board]
        self._interesting_points = None

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
        old_color = self.board[y][x]
        if old_color == new_color:
            return self

        other = Board(self.board)

        for x, y in self.flood_fill_from(x, y):
            other._set(x, y, new_color)

        return other

    def flood_fill_from(self, x, y):
        old_color = self.board[y][x]

        q = []
        q.append((x, y))

        visited = set()

        while q:
            x, y = q[0]
            del q[0]

            if (x, y) in visited or self.board[y][x] != old_color:
                continue

            visited.add((x, y))

            if x - 1 >= 0 and (x-1, y) not in visited:
                q.append((x-1, y))
            if x + 1 < BOARD_WIDTH and (x+1, y) not in visited:
                q.append((x+1, y))
            if y - 1 >= 0 and (x, y-1) not in visited:
                q.append((x, y-1))
            if y + 1 < BOARD_HEIGHT and (x, y+1) not in visited:
                q.append((x, y+1))

        return visited

    def is_done(self):
        c = self.board[0][0]

        for x, y in BOARD_COORDS:
            if self.board[y][x] != c:
                return False

        return True

    def interesting_points(self):
        if self._interesting_points:
            return self._interesting_points

        c = None

        skip = set()
        l = []

        for x, y in BOARD_COORDS:
            if (x, y) in skip:
                continue

            new_c = self.board[y][x]
            # if new_c != c:
            c = new_c
            skip.update(self.flood_fill_from(x, y))
            l.append((x, y))

        self._interesting_points = l
        return l

    def field_count(self):
        return len(list(self.interesting_points()))


BOARDS_GENERATED = 0
START_TIME = None


def gen_options(other_colors, board):
    global BOARDS_GENERATED
    l = []

    for x, y in board.interesting_points():
        base_color = board.get(x, y)

        for color in other_colors(base_color):
            BOARDS_GENERATED += 1
            if BOARDS_GENERATED % 10000 == 0:
                print('{} boards generated ({} boards/s)'.format(BOARDS_GENERATED, BOARDS_GENERATED / (time.time() - START_TIME)))

            l.append(((x, y), color, board.replaced_color(x, y, color)))

    return l


def option_sort_key(option):
    return option[2].field_count()


def get_solution_path(other_colors, board, step, max_step):
    if step == max_step:
        return False

    if board.is_done():
        return None

    options = list(gen_options(other_colors, board))
    options.sort(key=option_sort_key)

    for coord, color, option in options:
        path = get_solution_path(other_colors, option, step + 1, max_step)

        if path != False:
            return LinkedList((coord, color), path)

    return False


def solve(problem_setup, board, start_depth):
    global BOARDS_GENERATED, START_TIME
    limit = start_depth
    path = False

    START_TIME = start_time = time.time()

    while path is False:
        limit += 1
        print('Solving with step limit {}...'.format(limit - 1))
        path = get_solution_path(problem_setup.other_colors, board, 0, limit)

        if limit == 10:
            print('I guess there\'s no solution...')
            return

    end_time = time.time()

    for (x, y), color in path:
        print('Color {},{} {}'.format(x+1, y+1, problem_setup.color_names[color]))

    print('')
    print('{} boards generated in {:10.5} seconds'.format(BOARDS_GENERATED, (end_time - start_time)))


def main(screen, problem_setup, board):
    screen.clear()

    curses.start_color()
    problem_setup.init_curses_colors()

    cursor_x, cursor_y = 0, 0

    running = True

    while running:
        screen.clear()
        board.draw(screen, (cursor_x, cursor_y))

        k = screen.getch()

        if chr(k) == 'q':
            running = False
        elif chr(k) in ('1', '2', '3', '4'):
            board = board.replaced_color(cursor_x, cursor_y, int(chr(k)))
        elif k in (curses.KEY_UP, ','):
            cursor_y = max(0, cursor_y - 1)
        elif k in (curses.KEY_DOWN, 'o'):
            cursor_y = min(BOARD_HEIGHT - 1, cursor_y + 1)
        elif k in (curses.KEY_LEFT, 'a'):
            cursor_x = max(0, cursor_x - 1)
        elif k in (curses.KEY_RIGHT, 'e'):
            cursor_x = min(BOARD_WIDTH - 1, cursor_x + 1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} [solve/graph-solve] level [solver-start-depth]'.format(sys.argv[0]))

        sys.exit(1)

    board_name = sys.argv[2 if sys.argv[1] == 'solve' else 1]
    run_solver = sys.argv[1] == 'solve'
    run_graph_solver = sys.argv[1] == 'graph-solve'

    with open('levels/{}.txt'.format(board_name)) as board_file:
        board_text = board_file.read().split()

    problem_setup = SETUPS[board_name[0]]
    board = Board([[problem_setup.color_map[c] for c in row] for row in board_text])

    if len(board.board) != BOARD_HEIGHT:
        raise Exception('Board has incorrect height: {} != {}'.format(BOARD_HEIGHT, len(board.board)))
    if any(len(row) != BOARD_WIDTH for row in board.board):
        raise Exception('Board has incorrect width on some row')

    if run_solver:
        start_depth = int(sys.argv[3]) if len(sys.argv) >= 4 else 0
        solve(problem_setup, board, start_depth)
    elif run_graph_solver:
        start_depth = int(sys.argv[3]) if len(sys.argv) >= 4 else 0
        graph_solve(problem_setup, board, start_depth)
    elif not curses.wrapper(main, problem_setup, board):
        sys.exit(1)
