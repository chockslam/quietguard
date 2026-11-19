"""Experimental Sentinel with an exact guard against forced quiet-move losses.

The original player, evaluation, full search and rules stay unchanged. This
variant checks whether at least one legal move avoids an immediate winning
reply before using stand pat. It is a two-ply safety check, not a general
zugzwang solver or a replacement for deeper search.
"""

from .agent import Sentinel, MATE, INF
from .evaluation import evaluate


class SentinelQuietGuard(Sentinel):
    def __init__(self, seed=1, *, resolve_cutoff_threats=True, **kwargs):
        super().__init__(seed, **kwargs)
        self.resolve_cutoff_threats = resolve_cutoff_threats
        self._reset_guard_counts()

    def _reset_guard_counts(self):
        self.guard_probes = 0
        self.guard_forced_losses = 0
        self.guard_defensive_leaves = 0

    def choose(self, position, limits):
        self._reset_guard_counts()
        decision = super().choose(position, limits)
        decision.diagnostics.update(
            profile="sentinel-quiet-guard" if self.resolve_cutoff_threats else "sentinel-forced-move-guard",
            quiet_guard_probes=self.guard_probes,
            quiet_guard_forced_losses=self.guard_forced_losses,
            quiet_guard_defensive_leaves=self.guard_defensive_leaves,
            resolve_cutoff_threats=self.resolve_cutoff_threats)
        return decision

    def _safe_actions(self, ply, *, collect_all=False, evaluate_children=False):
        """Find safe actual moves, including repetition draws, with reversible undo.

        Probe one piece at a time using the existing move generator: ordinary
        positions often need just the first move, not a full root list. When
        threatened, collect every safe defense. No node/clock cutoff is allowed
        to turn an incomplete scan into a forced-loss declaration.
        """
        board, side = self.board, self.board.side
        pieces = board.blacks if side else board.whites | (
            0 if board.king is None else 1 << board.king)
        safe, checked = [], 0
        while pieces:
            bit = pieces & -pieces
            pieces ^= bit
            for move in board.moves(source_mask=bit):
                self._visit()
                self.guard_probes += 1
                checked += 1
                record = self._push(move)
                try:
                    danger = not board.outcome and bool(board.winning_moves(check=self._check))
                    if not danger:
                        score = None
                        if board.outcome:
                            score = -self._terminal(ply+1)
                        elif evaluate_children:
                            score = evaluate(board)*(1 if side == 0 else -1)
                        safe.append((move, score))
                finally:
                    self._pop(record)
                if safe and not collect_all:
                    return safe, checked
        return safe, checked

    def _quiescence(self, alpha, beta, ply, remaining):
        self._check()
        self.qnodes += 1
        board = self.board
        if board.outcome:
            self.stats.leaves += 1
            return self._terminal(ply)
        if board.winning_moves(check=self._check):
            return MATE-ply-1
        stand = evaluate(board)*(1 if board.side == 0 else -1)
        threatened = bool(board.winning_moves(1-board.side, check=self._check))
        safe, checked = self._safe_actions(
            ply, collect_all=threatened and (remaining > 0 or self.resolve_cutoff_threats),
            evaluate_children=threatened and remaining <= 0 and self.resolve_cutoff_threats)
        if not checked:
            # Official Ashton does not declare a winner on move exhaustion.
            self.stats.leaves += 1
            return stand
        if not safe:
            self.guard_forced_losses += 1
            self.stats.leaves += 1
            return -MATE+ply+2
        if remaining <= 0:
            self.stats.leaves += 1
            if threatened and self.resolve_cutoff_threats:
                # One bounded defensive ply: keeping the board unchanged is
                # unavailable. Further non-immediate tactics remain heuristic.
                self.guard_defensive_leaves += 1
                return max(score for _, score in safe)
            known = [score for _, score in safe if score is not None]
            return max([stand, *known])
        if threatened:
            value = -INF
            moves = [move for move, _ in safe]
        else:
            known = [score for _, score in safe if score is not None]
            value = max([stand, *known])
            if value >= beta:
                return value
            alpha = max(alpha, value)
            moves = board.moves()
        for move in self._order(moves, ply=ply):
            capture = board.capture_hint(move)
            king_move = move//81 == board.king
            if not threatened and not capture and not king_move:
                continue
            self._visit()
            record = self._push(move)
            try:
                forcing = (threatened or capture or board.outcome or
                           board.winning_moves(1-board.side, check=self._check))
                if not forcing:
                    continue
                score = -self._quiescence(-beta, -alpha, ply+1, remaining-1)
            finally:
                self._pop(record)
            value = max(value, score)
            alpha = max(alpha, value)
            if alpha >= beta:
                self.stats.cutoffs += 1
                break
        return value
