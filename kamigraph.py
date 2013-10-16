from __future__ import print_function

import time

from kamicommon import LinkedList

class Graph(object):
    def __init__(self):
        self._counter = 0
        self._connections = set()
        self._node_data = {}

        self._connected_nodes = None
        self._num_connected_nodes = None
        self._node_connections = None

    def copy(self):
        g = Graph()
        g._counter = self._counter
        g._connections = set(self._connections)
        g._node_data = dict(self._node_data)

        return g

    def freeze(self):
        self._connected_nodes = self.connected_nodes()
        self._num_connected_nodes = self.num_connected_nodes()

        self._node_connections = {}
        for n1, n2 in self._connections:
            self._node_connections.setdefault(n1, []).append(n2)
            self._node_connections.setdefault(n2, []).append(n1)


    def num_connected_nodes(self):
        if self._num_connected_nodes is not None: return self._num_connected_nodes

        return len(self.connected_nodes())

    def connected_nodes(self):
        if self._connected_nodes is not None: return self._connected_nodes

        ns = set()

        for n1, n2 in self._connections:
            ns.add(n1)
            ns.add(n2)

        return ns

    def add_node(self):
        self._counter += 1
        self._node_data[self._counter] = {}
        return self._counter

    def node_data(self, node):
        return self._node_data[node]

    def set_node_data(self, node, data):
        self._node_data[node] = data

    def connect(self, n1, n2):
        if n1 < n2:
            self._connections.add((n1, n2))
        else:
            self._connections.add((n2, n1))

    def is_connected(self, n1, n2):
        if n1 < n2:
            return (n1, n2) in self._connections
        else:
            return (n2, n1) in self._connections

    def connections(self, node):
        if self._node_connections: return self._node_connections[node]

        l = []

        for n1, n2 in self._connections:
            if node == n1:
                l.append(n2)
            elif node == n2:
                l.append(n1)

        return l

    def rename_node(self, old, new):
        new_conns = set()

        for n1, n2 in self._connections:
            if n1 == old:
                if n2 != new: new_conns.add((min(new, n2), max(new, n2)))
            elif n2 == old:
                if n1 != new: new_conns.add((min(new, n1), max(new, n1)))
            else:
                new_conns.add((n1, n2))

        self._connections = new_conns

    def draw(self):
        print('   ' + '  '.join(map(str, range(1, self._counter + 1))))

        for n1 in range(1, self._counter + 1):
            print('{}{}'.format(n1,
                                ''.join('  X' if self.is_connected(n1, n2) else '   '
                                        for n2 in range(1, n1 + 1))))

        print('')

        for n in range(1, self._counter + 1):
            print('{}: {}'.format(n, self._node_data[n]))

        print('')


def graph_by_collapsing_node(graph, node, set_color):
    conns = graph.connections(node)
    g2 = graph.copy()

    size = graph.node_data(node)['size']
    origin = graph.node_data(node)['origin']

    for conn in conns:
        nd = graph.node_data(conn)
        if nd['color'] == set_color:
            size += nd['size']
            g2.rename_node(conn, node)

    g2.set_node_data(node, {'size': size, 'origin': origin, 'color': set_color})

    return g2


GRAPHS_GENERATED = 0
START_TIME = None


def gen_options(other_colors, graph):
    global GRAPHS_GENERATED
    l = []

    for node in graph.connected_nodes():
        nd = graph.node_data(node)
        base_color = nd['color']

        for color in other_colors(base_color):
            new_graph = graph_by_collapsing_node(graph, node, color)

            GRAPHS_GENERATED += 1
            if GRAPHS_GENERATED % 10000 == 0:
                print('{} graphs generated ({} graphs/s)'.format(GRAPHS_GENERATED, GRAPHS_GENERATED / (time.time() - START_TIME)))

            l.append((nd['origin'], color, new_graph))

    return l


def option_sort_key(option):
    return option[2].num_connected_nodes()


def is_graph_done(graph):
    return graph.num_connected_nodes() == 0


def get_solution_path(other_colors, graph, step, max_step):
    if step == max_step:
        return False

    if is_graph_done(graph):
        return None

    options = gen_options(other_colors, graph)
    options.sort(key=option_sort_key)

    for coord, color, option in options:
        path = get_solution_path(other_colors, option, step + 1, max_step)

        if path != False:
            return LinkedList((coord, color), path)

    return False


def graph_solve(problem_setup, board, start_depth):
    global GRAPHS_GENERATED, START_TIME
    graph = graph_from_board(board, draw=False)
    # graph.draw()

    limit = start_depth
    path = False

    START_TIME = start_time = time.time()

    while path is False:
        limit += 1
        print('Solving with step limit {}...'.format(limit - 1))
        path = get_solution_path(problem_setup.other_colors, graph, 0, limit)

        if limit == 10:
            print('I guess there\'s no solution...')
            return

    end_time = time.time()
    dur = end_time - start_time

    for (x, y), color in path:
        print('Color {},{} {}'.format(x+1, y+1, problem_setup.color_names[color]))

    print('')
    print('{} graphs generated in {} seconds ({} graphs/s)'.format(GRAPHS_GENERATED, dur, GRAPHS_GENERATED/dur))


def is_adjacent(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2:
        return abs(y1 - y2) <= 1
    elif y1 == y2:
        return abs(x1 - x2) <= 1

    return False


def graph_from_board(board, draw=False):
    graph = Graph()

    pts = board.interesting_points()
    node_at_coord = {}

    for px, py in pts:
        node = graph.add_node()
        area = board.flood_fill_from(px, py)

        graph.set_node_data(node, {'size': len(area),
                                   'color': board.get(px, py),
                                   'origin': (px, py)})

        for x, y in area:
            node_at_coord[(x,y)] = node

    for c1, n1 in node_at_coord.items():
        for c2, n2 in node_at_coord.items():
            if n1 != n2 and is_adjacent(c1, c2):
                graph.connect(n1, n2)

    if draw:
        for row in range(16):
            print(' '.join('{:2}'.format(node_at_coord[(col, row)]) for col in range(10)))
            # print(''.join(str(graph.node_data(node_at_coord[(col, row)])['color']) for col in range(10)))
        print('')

    return graph
