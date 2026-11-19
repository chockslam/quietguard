"""Internal board representation. JSON dictionaries stay at the wire boundary."""

from __future__ import annotations
from dataclasses import dataclass
import sys
from typing import NamedTuple

# Debian 11 in the official VM supplies Python 3.9. Newer hosts keep slots.
DATACLASS_OPTIONS = {"slots": True} if sys.version_info >= (3, 10) else {}

EMPTY, WHITE, BLACK, KING, THRONE = range(5)
PAWN_NAMES = ("EMPTY", "WHITE", "BLACK", "KING", "THRONE")
PAWN_CODES = {name: code for code, name in enumerate(PAWN_NAMES)}
TERMINAL = frozenset(("WHITEWIN", "BLACKWIN", "DRAW"))
OPPONENT = {"WHITE": "BLACK", "BLACK": "WHITE"}
CAMPS = frozenset((3, 4, 5, 13, 27, 35, 36, 37, 43, 44, 45, 53, 67, 75, 76, 77))
OUTER_CAMPS = frozenset((4, 36, 44, 76))
THRONE_INDEX = 40
THRONE_NEIGHBORS = frozenset((31, 39, 41, 49))


def square(index: int) -> str:
    return chr(97 + index % 9) + str(index // 9 + 1)


def index(square_name: str) -> int:
    if (len(square_name) != 2 or square_name[0].lower() not in "abcdefghi"
            or square_name[1] not in "123456789"):
        raise ValueError("Invalid square: " + square_name)
    return (int(square_name[1]) - 1) * 9 + ord(square_name[0].lower()) - 97


class Move(NamedTuple):
    source: int
    target: int

    def to_json(self, role: str) -> dict:
        return {"from": square(self.source), "to": square(self.target), "turn": role}

    @classmethod
    def from_json(cls, action: dict):
        return cls(index(action["from"]), index(action["to"]))


@dataclass(frozen=True, **DATACLASS_OPTIONS)
class Position:
    board: tuple[int, ...]
    turn: str

    def __post_init__(self):
        if len(self.board) != 81 or any(p not in range(5) for p in self.board):
            raise ValueError("Expected 81 valid squares")
        if self.turn not in OPPONENT and self.turn not in TERMINAL:
            raise ValueError("Unknown turn")

    @property
    def terminal(self):
        return self.turn in TERMINAL

    @property
    def key(self):
        return self.board, self.turn

    @property
    def king(self):
        try:
            return self.board.index(KING)
        except ValueError:
            return None

    def to_json(self):
        return {"board": [[PAWN_NAMES[p] for p in self.board[r:r + 9]]
                          for r in range(0, 81, 9)], "turn": self.turn}

    @classmethod
    def from_json(cls, state):
        rows = state["board"]
        if len(rows) != 9 or any(len(row) != 9 for row in rows):
            raise ValueError("Expected 9 by 9 board")
        return cls(tuple(PAWN_CODES[p] for row in rows for p in row), state["turn"])


def initial_position():
    board = [EMPTY] * 81
    for i in CAMPS:
        board[i] = BLACK
    for i in (22, 31, 38, 39, 41, 42, 49, 58):
        board[i] = WHITE
    board[40] = KING
    return Position(tuple(board), "WHITE")


def position_with(turn="WHITE", king="e5", **pieces):
    """Small explicit positions for rule and decision fixtures."""
    board = [EMPTY] * 81
    board[40] = THRONE
    if king is not None:
        board[index(king)] = KING
    for name, pawn in pieces.items():
        board[index(name)] = PAWN_CODES[pawn] if isinstance(pawn, str) else pawn
    return Position(tuple(board), turn)
