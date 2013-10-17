from __future__ import print_function

import heapq

from kamicommon import LinkedList

class MinHeap(object):
    def __init__(self):
        self._counter = 0
        self._data = []

    def push(self, priority, obj):
        heapq.heappush(self._data, (priority, self._counter, obj))
        self._counter += 1

    def pop(self):
        prio, counter, obj = heapq.heappop(self._data)
        return obj

    def is_empty(self):
        return len(self._data) == 0


class GraphSearchProblem(object):
    def start(self):
        '''start :: Node'''

    def successors(self, node):
        '''successors :: Node -> [(Cost, Edge, Node)]'''

    def is_target(self, node):
        '''is_target :: Node -> Bool'''

    def target_heuristic(self, node):
        '''target_heuristic :: Node -> Number'''
        return 0


### --------- Iterative Deepening Depth First Search

def cost_getter(t):
    return t[0]


def _get_solution_path(problem, node, step, max_step):
    if step == max_step:
        return False

    if problem.is_target(node):
        return None

    options = problem.successors(node)
    options.sort(key=cost_getter)

    for cost, edge, successor_node in options:
        path = _get_solution_path(problem, successor_node, step + 1, max_step)

        if path != False:
            return LinkedList(edge, path)

    return False


def iterative_deepening_dfs(problem, start_depth):
    limit = start_depth
    path = False

    while path is False:
        limit += 1
        print('Solving with step limit {}...'.format(limit - 1))
        path = _get_solution_path(problem, problem.start(), 0, limit)

        if limit == 10:
            print('I guess there\'s no solution...')
            return None

    return list(path)


### --------- A* Search

def a_star_search(problem, max_path_length):
    q = MinHeap()

    q.push(0, (0, None, problem.start()))

    while not q.is_empty():
        acc_cost, prev_edge, node = q.pop()

        if prev_edge and len(prev_edge) > max_path_length:
            continue

        if problem.is_target(node):
            return list(prev_edge)

        for local_cost, edge, successor_node in problem.successors(node):
            new_cost = local_cost + acc_cost + problem.target_heuristic(node)

            q.push(new_cost, (new_cost, LinkedList(edge, prev_edge), successor_node))

    return None
