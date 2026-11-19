"""Official GameAshtonTablut semantics at pinned UniBo commit 96983984e42c.

Movement/capture/draw behavior is derived from the official Java implementation,
including keeping the captured king on its square and the cache-size boundary.
Rulebook improvements must be separate rule profiles, not changes to this one.
"""

from __future__ import annotations
from dataclasses import dataclass
from .model import (EMPTY, WHITE, BLACK, KING, THRONE, CAMPS, OUTER_CAMPS,
                    THRONE_INDEX, THRONE_NEIGHBORS, OPPONENT, Move, Position,
                    DATACLASS_OPTIONS)

DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def ray(source, dr, dc):
    r, c = divmod(source, 9)
    result = []
    r, c = r + dr, c + dc
    while 0 <= r < 9 and 0 <= c < 9:
        result.append(r * 9 + c)
        r, c = r + dr, c + dc
    return tuple(result)


RAYS = tuple(tuple(ray(i, *d) for d in DIRECTIONS) for i in range(81))
NEIGHBORS = tuple(tuple(r[0] for r in RAYS[i] if r) for i in range(81))


@dataclass(frozen=True, **DATACLASS_OPTIONS)
class History:
    states: tuple = ()
    repeated_allowed: int = 0
    cache_size: int = -1

    def advance(self, position, captured):
        states = () if captured else self.states
        if sum(key == position.key for key in states) > self.repeated_allowed:
            position = Position(position.board, "DRAW")
        # Java removes one entry BEFORE adding, and only when size > cache_size.
        if self.cache_size >= 0 and len(states) > self.cache_size:
            states = states[1:]
        return position, History(states + (position.key,), self.repeated_allowed,
                                 self.cache_size)


@dataclass(frozen=True, **DATACLASS_OPTIONS)
class Transition:
    position: Position
    captured: tuple[int, ...]
    history: History | None


class AshtonRules:
    def legal_moves(self, position):
        if position.terminal:
            return []
        board = position.board
        own = (WHITE, KING) if position.turn == "WHITE" else (BLACK,)
        moves = []
        for source, pawn in enumerate(board):
            if pawn not in own:
                continue
            starts_in_camp = source in CAMPS
            for line in RAYS[source]:
                for distance, target in enumerate(line, 1):
                    if board[target] != EMPTY:
                        break
                    if target in CAMPS:
                        if not starts_in_camp:
                            break
                        if distance > 5:
                            continue
                    moves.append(Move(source, target))
        return moves

    def apply(self, position, move, history=None, *, validate=True):
        if validate and move not in self.legal_moves(position):
            raise ValueError("Illegal move: " + str(move))
        return self.apply_legal(position, move, history)

    def apply_legal(self, position, move, history=None):
        """Search fast path: caller has already generated a legal action."""
        if position.terminal:
            raise ValueError("Cannot move after the game ends")
        board = list(position.board)
        board[move.target] = board[move.source]
        board[move.source] = THRONE if move.source == THRONE_INDEX else EMPTY
        turn = OPPONENT[position.turn]
        captured = []
        if position.turn == "WHITE":
            for line in RAYS[move.target]:
                if len(line) < 2:
                    continue
                adjacent, support = line[:2]
                hostile_camp = support in CAMPS and support not in OUTER_CAMPS
                if board[adjacent] == BLACK and (board[support] in (WHITE, KING, THRONE)
                                                or hostile_camp):
                    board[adjacent] = EMPTY
                    captured.append(adjacent)
            r, c = divmod(move.target, 9)
            if board[move.target] == KING and (r in (0, 8) or c in (0, 8)):
                turn = "WHITEWIN"
        else:
            # Java checks normal pawns before checking king capture.
            for line in RAYS[move.target]:
                if len(line) < 2:
                    continue
                adjacent, support = line[:2]
                if board[adjacent] == WHITE and (board[support] in (BLACK, THRONE)
                                               or support in CAMPS or support == 40):
                    board[adjacent] = EMPTY
                    captured.append(adjacent)
            for line in RAYS[move.target]:
                if len(line) < 2 or board[line[0]] != KING:
                    continue
                king, support = line[:2]
                if king == 40:
                    is_captured = all(board[n] == BLACK for n in NEIGHBORS[king])
                elif king in THRONE_NEIGHBORS:
                    is_captured = all(board[n] == BLACK for n in NEIGHBORS[king] if n != 40)
                else:
                    is_captured = board[support] == BLACK or support in CAMPS
                if is_captured:
                    turn = "BLACKWIN"
        result = Position(tuple(board), turn)
        if history is not None:
            result, history = history.advance(result, bool(captured))
        return Transition(result, tuple(captured), history)


class SearchBoard:
    """Reversible view: retain immutable snapshots instead of deep-copying objects."""
    def __init__(self, position, history=None, rules=None):
        self.position, self.history = position, history
        self.rules = rules or AshtonRules()
        self._stack = []

    def push(self, move):
        result = self.rules.apply(self.position, move, self.history)
        self._stack.append((self.position, self.history))
        self.position, self.history = result.position, result.history
        return result

    def pop(self):
        self.position, self.history = self._stack.pop()
