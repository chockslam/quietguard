"""Cheap White-centric material, escape and containment evaluation.

Terminal scores belong to search, never to this heuristic. Both colours use the
same consistent perspective. Phase is derived from material, not a turn counter
that could make cached scores stale. Expensive exact threats are checked by search.
"""

from tablut_agents.model import EMPTY, BLACK, CAMPS, THRONE_NEIGHBORS
from tablut_agents.rules import NEIGHBORS
from .board import RAY_MASKS, CAMP_MASK, EDGE

popcount = getattr(int, "bit_count", lambda value: bin(value).count("1"))
EXITS = tuple(i for i in range(81) if (1 << i) & EDGE and i not in CAMPS)
EXIT_DISTANCE = tuple(min(abs(s//9-t//9)+abs(s%9-t%9) for t in EXITS) for s in range(81))
RINGS = tuple(tuple(sum(1 << t for t in range(81)
                        if abs(s//9-t//9)+abs(s%9-t%9) == distance)
                    for distance in (2,3)) for s in range(81))
FORMATION = sum(1 << i for i in (11,15,19,25,55,61,65,69))


def evaluate(board):
    if board.king is None:
        return -9000
    king = board.king
    white, black = popcount(board.whites), popcount(board.blacks)
    value = 400 + 130*white - 90*black
    blockers = board.occupied | CAMP_MASK
    mobility, escapes, own_blocks = 0,0,0
    for d,ray in enumerate(RAY_MASKS[king]):
        if not ray:
            continue
        blocked = ray & blockers
        if not blocked:
            escapes += 1
            distance = (king//9 if d==0 else 8-king//9 if d==1 else king%9 if d==2 else 8-king%9)
        else:
            stop = blocked.bit_length()-1 if d in (0,2) else (blocked & -blocked).bit_length()-1
            distance = abs(king-stop)//9-1 if d in (0,1) else abs(king-stop)-1
            own_blocks += bool((1 << stop) & board.whites)
        mobility += distance
    value += 5*mobility + 28*(6-EXIT_DISTANCE[king]) - 12*own_blocks
    if escapes:
        value += 280*escapes + (600 if escapes>1 else 0)
    adjacent = sum(board.cells[n] == BLACK for n in NEIGHBORS[king])
    special = king == 40 or king in THRONE_NEIGHBORS
    required = 4 if king==40 else 3 if special else 2
    # Hostile camps matter particularly to an off-throne king.
    value -= (35 if special else 90)*adjacent
    if not special:
        value -= 45*sum(n in CAMPS for n in NEIGHBORS[king])
    if adjacent >= required-1:
        value -= 180 if special else 250
    value -= 12*popcount(board.blacks & RINGS[king][0])
    value -= 5*popcount(board.blacks & RINGS[king][1])
    if white>4:
        value -= 12*popcount(board.blacks & FORMATION)
    else:
        value -= 10*adjacent  # Containment matters more after escorts disappear.
    value += 15*sum(bool(board.whites & (1 << n)) for n in NEIGHBORS[king])
    value -= 30 if king == 40 else 0
    return max(-9000,min(9000,value))
