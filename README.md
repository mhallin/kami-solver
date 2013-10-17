# Kami Solver

Simple and half-working solver for excellent game
[Kami](https://itunes.apple.com/us/app/kami/id710724007?mt=8).

It's written in Python and runs like this:

    python kami.py graph-solve [level] [moves]

So if you want to solve level A5 in five steps, you would run:

    python kami.py graph-solve A5 5

If you want to solve the larger levels, [PyPy](http://pypy.org) is recommended.

## Implementation

* The levels are stored as ASCII art in the levels folder.
* `graph-solve` uses A* in a graph representation of the board. The heuristic
  is very simple and could use some tuning. It currently runs out of memory
  on the larger and longer levels (such as B8 and B9).
