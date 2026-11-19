"""Mutable specialization of tablut_agents.rules.AshtonRules for search.

The immutable reference remains authoritative. This kernel avoids allocating and
validating an 81-square Position at every node, and is checked against it.
King capture deliberately keeps the king on the board, as official Java does.
"""

from tablut_agents.model import (EMPTY, WHITE, BLACK, KING, THRONE, CAMPS,
                                OUTER_CAMPS, THRONE_NEIGHBORS, Move, Position)
from tablut_agents.rules import RAYS, NEIGHBORS

WHITE_SIDE, BLACK_SIDE = 0, 1
SIDE_NAME = ("WHITE", "BLACK")
EDGE = sum(1 << i for i in range(81) if i // 9 in (0, 8) or i % 9 in (0, 8))
CAMP_MASK = sum(1 << i for i in CAMPS)
THRONE_BIT = 1 << 40
RAY_MASKS = tuple(tuple(sum(1 << t for t in ray) for ray in rays) for rays in RAYS)
BEFORE = tuple(tuple({t: sum(1 << q for q in ray[:n]) for n,t in enumerate(ray)}
                     for ray in rays) for rays in RAYS)
FAR_CAMPS = tuple(sum(1 << t for t in CAMPS
                     if abs(t // 9 - s // 9) + abs(t % 9 - s % 9) > 5)
                 for s in range(81))
KING_NEIGHBOUR_MASK = tuple(sum(1 << t for t in near) for near in NEIGHBORS)
CAPTURE_SIDES = tuple(tuple((target,line[1]) for target in NEIGHBORS[king]
                           for line in RAYS[target] if len(line)>1 and line[0]==king)
                     for king in range(81))


def encode(move):
    return move.source * 81 + move.target


def decode(move):
    return Move(*divmod(move, 81))


class Board:
    def __init__(self, position):
        self.cells = list(position.board)
        self.whites = sum(1 << i for i,p in enumerate(self.cells) if p == WHITE)
        self.blacks = sum(1 << i for i,p in enumerate(self.cells) if p == BLACK)
        self.king = position.king
        self.side = WHITE_SIDE if position.turn == "WHITE" else BLACK_SIDE
        self.outcome = {"WHITEWIN":1, "BLACKWIN":-1, "DRAW":2}.get(position.turn, 0)

    @property
    def key(self):
        # Full keys retain equality checks; no hash collision changes a position.
        return self.whites, self.blacks, self.king, self.side, self.cells[40] == THRONE, self.outcome

    @property
    def occupied(self):
        king = 0 if self.king is None else 1 << self.king
        return self.whites | self.blacks | king | (THRONE_BIT if self.cells[40] == THRONE else 0)

    def position(self):
        turn = {1:"WHITEWIN", -1:"BLACKWIN", 2:"DRAW"}.get(self.outcome, SIDE_NAME[self.side])
        return Position(tuple(self.cells), turn)

    def moves(self, side=None, source_mask=None, target_mask=None):
        if self.outcome:
            return []
        side = self.side if side is None else side
        pieces = self.blacks if side else self.whites | (0 if self.king is None else 1 << self.king)
        if source_mask is not None:
            pieces &= source_mask
        occupied = self.occupied
        result = []
        while pieces:
            bit = pieces & -pieces
            source = bit.bit_length() - 1
            pieces ^= bit
            starts_camp = source in CAMPS
            blockers = occupied if starts_camp else occupied | CAMP_MASK
            for d, ray in enumerate(RAY_MASKS[source]):
                blocked = ray & blockers
                if blocked:
                    nearest = blocked.bit_length()-1 if d in (0,2) else (blocked & -blocked).bit_length()-1
                    targets = BEFORE[source][d][nearest]
                else:
                    targets = ray
                if starts_camp:
                    targets &= ~FAR_CAMPS[source]
                if target_mask is not None:
                    targets &= target_mask
                while targets:
                    target = targets.bit_length()-1 if d in (0,2) else (targets & -targets).bit_length()-1
                    targets ^= 1 << target
                    result.append(source*81+target)
        return result

    def push(self, move, side=None):
        source, target = divmod(move,81)
        cells = self.cells
        pawn, old_target = cells[source], cells[target]
        undo = (source,target,pawn,old_target,self.whites,self.blacks,self.king,self.side,self.outcome)
        side = self.side if side is None else side
        cells[target] = pawn
        cells[source] = THRONE if source == 40 else EMPTY
        bits = (1 << source) | (1 << target)
        if pawn == WHITE:
            self.whites ^= bits
        elif pawn == BLACK:
            self.blacks ^= bits
        else:
            self.king = target
        self.side, self.outcome = 1-side, 0
        captured = []
        if side == WHITE_SIDE:
            for line in RAYS[target]:
                if len(line) < 2:
                    continue
                adjacent, support = line[:2]
                if cells[adjacent] == BLACK and (cells[support] in (WHITE,KING,THRONE)
                                                 or support in CAMPS and support not in OUTER_CAMPS):
                    cells[adjacent] = EMPTY
                    self.blacks ^= 1 << adjacent
                    captured.append((adjacent,BLACK))
            if pawn == KING and (1 << target) & EDGE:
                self.outcome = 1
        else:
            for line in RAYS[target]:
                if len(line) < 2:
                    continue
                adjacent, support = line[:2]
                if cells[adjacent] == WHITE and (cells[support] in (BLACK,THRONE)
                                                 or support in CAMPS or support == 40):
                    cells[adjacent] = EMPTY
                    self.whites ^= 1 << adjacent
                    captured.append((adjacent,WHITE))
            for line in RAYS[target]:
                if len(line) < 2 or cells[line[0]] != KING:
                    continue
                king, support = line[:2]
                if king == 40:
                    caught = all(cells[n] == BLACK for n in NEIGHBORS[king])
                elif king in THRONE_NEIGHBORS:
                    caught = all(cells[n] == BLACK for n in NEIGHBORS[king] if n != 40)
                else:
                    caught = cells[support] == BLACK or support in CAMPS
                if caught:
                    self.outcome = -1
        return undo, captured

    def pop(self, undo, captured):
        source,target,pawn,old_target,self.whites,self.blacks,self.king,self.side,self.outcome = undo
        self.cells[source] = pawn
        self.cells[target] = old_target
        for square,piece in captured:
            self.cells[square] = piece

    def winning_moves(self, side=None, check=None):
        """Exact immediate king escape/capture candidates, under Ashton rules."""
        side = self.side if side is None else side
        if self.king is None or self.outcome:
            return []
        sources = (1 << self.king) if side == WHITE_SIDE else None
        targets = EDGE
        if side == BLACK_SIDE:
            king = self.king
            if king==40 or king in THRONE_NEIGHBORS:
                required = 4 if king==40 else 3
                if sum(self.cells[n]==BLACK for n in NEIGHBORS[king]) < required-1:
                    return []
                targets = KING_NEIGHBOUR_MASK[king]
            else:
                targets = sum(1 << target for target,support in CAPTURE_SIDES[king]
                              if self.cells[support]==BLACK or support in CAMPS)
        if not targets:
            return []
        result = []
        for move in self.moves(side,sources,targets):
            source,target = divmod(move,81)
            if side == WHITE_SIDE and source != self.king or not (1 << target) & targets:
                continue
            if check:
                check()
            undo,captured = self.push(move,side)
            won = self.outcome == (1 if side == WHITE_SIDE else -1)
            self.pop(undo,captured)
            if won:
                result.append(move)
        return result

    def capture_hint(self, move):
        source,target = divmod(move,81)
        enemy = WHITE if self.side else BLACK
        own = (BLACK,THRONE) if self.side else (WHITE,KING,THRONE)
        count = 0
        for line in RAYS[target]:
            if len(line)<2:
                continue
            victim,support = line[:2]
            if self.cells[victim] != enemy or support == source:
                continue
            hostile = support in CAMPS and (self.side or support not in OUTER_CAMPS)
            count += self.cells[support] in own or hostile or self.side and support == 40
        return count
