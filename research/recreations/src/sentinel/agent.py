"""Sentinel's one-core iterative alpha-beta/PVS search for official Ashton.

No student search implementation is executed or imported. The public Agent API
is shared with TCP and offline clients; only the transport differs.
"""

from collections import OrderedDict
from dataclasses import dataclass
import time

from tablut_agents.api import Decision, Limits, SearchStopped, Statistics
from tablut_agents.model import WHITE, BLACK, KING, initial_position
from .board import Board, encode, decode, SIDE_NAME, EDGE, KING_NEIGHBOUR_MASK
from .evaluation import evaluate, popcount, EXIT_DISTANCE

MATE = 100000
INF = 1000000
EXACT, LOWER, UPPER = 0,1,2


@dataclass(frozen=True)
class Entry:
    depth: int
    score: int
    flag: int
    move: int
    context_hash: int
    context: frozenset


class Sentinel:
    def __init__(self, seed=1, *, table_size=32768, quiescence_depth=2, pvs=True):
        self.seed = seed  # Deterministic ordering; a seed alone does not vary play.
        self.table_size, self.quiescence_depth, self.pvs = table_size,quiescence_depth,pvs
        self.table = OrderedDict()
        self.played = set()
        self.last_observed = None
        self.last_material = None
        self.history_scores = {}
        self.killers = {}

    def observe(self, position):
        if self.last_observed == position.key:
            return
        material = position.board.count(WHITE)+position.board.count(BLACK)
        if self.last_material is not None and material<self.last_material:
            self.played.clear()
        # The official draw cache starts empty; the initial board is not stored.
        if not (self.last_observed is None and position == initial_position()):
            self.played.add(Board(position).key)
        self.last_observed, self.last_material = position.key,material

    def _check(self):
        if self.limits.nodes is not None and self.stats.nodes >= self.limits.nodes:
            self.stats.stop_reason = "node_limit"
            raise SearchStopped
        if time.monotonic() >= self.deadline:
            self.stats.stop_reason = "deadline"
            raise SearchStopped

    def _visit(self):
        self._check()
        self.stats.nodes += 1

    def _push(self, move):
        undo,captured = self.board.push(move)
        old_seen, old_hash = self.seen,self.context_hash
        if captured:
            self.seen = set()
            self.context_hash = 0
        key = self.board.key
        repeated = key in self.seen
        if repeated and not self.board.outcome:
            self.board.outcome = 2
        added = key not in self.seen
        if added:
            self.seen.add(key)
            self.context_hash ^= hash(key)
        return undo,captured,old_seen,old_hash,key,added

    def _pop(self, record):
        undo,captured,old_seen,old_hash,key,added = record
        if added:
            self.seen.remove(key)
        self.seen,self.context_hash = old_seen,old_hash
        self.board.pop(undo,captured)

    def _terminal(self, ply):
        if self.board.outcome == 2:
            return 0
        white_value = MATE-ply if self.board.outcome == 1 else -MATE+ply
        return white_value if self.board.side == 0 else -white_value

    def _order(self, moves, preferred=None, ply=0):
        board,side = self.board,self.board.side
        killers = self.killers.get(ply,())
        def score(move):
            if move == preferred:
                return 10000000
            source,target = divmod(move,81)
            value = 20000*board.capture_hint(move)
            if source == board.king:
                value += 500000 if (1 << target) & EDGE else 30*(EXIT_DISTANCE[source]-EXIT_DISTANCE[target])
            elif side == 1 and board.king is not None:
                if (1 << target) & KING_NEIGHBOUR_MASK[board.king]:
                    value += 15000
            if move in killers:
                value += 10000 if move == killers[0] else 7000
            return value + self.history_scores.get((side,move),0)
        return sorted(moves,key=score,reverse=True)

    def _store(self, key, depth, value, alpha, beta, best, ply):
        # Mate distances are relative to the stored position, not a prior root.
        score = value+ply if value>MATE-1000 else value-ply if value<-MATE+1000 else value
        flag = UPPER if value<=alpha else LOWER if value>=beta else EXACT
        old = self.table.get(key)
        if old is None or depth>=old.depth or old.context != self.seen:
            self.table[key] = Entry(depth,score,flag,best,self.context_hash,frozenset(self.seen))
            self.table.move_to_end(key)
            if len(self.table)>self.table_size:
                self.table.popitem(last=False)

    def _search(self, depth, alpha, beta, ply):
        self._visit()
        board = self.board
        if board.outcome:
            self.stats.leaves += 1
            return self._terminal(ply)
        if depth<=0:
            return self._quiescence(alpha,beta,ply,self.quiescence_depth)
        key,original_alpha,original_beta = board.key,alpha,beta
        entry = self.table.get(key)
        preferred = entry.move if entry else None
        if entry and entry.depth>=depth and entry.context_hash==self.context_hash and entry.context==self.seen:
            self.tt_hits += 1
            score = entry.score-ply if entry.score>MATE-1000 else entry.score+ply if entry.score<-MATE+1000 else entry.score
            if entry.flag==EXACT:
                return score
            if entry.flag==LOWER:
                alpha = max(alpha,score)
            else:
                beta = min(beta,score)
            if alpha>=beta:
                return score
        moves = self._order(board.moves(),preferred,ply)
        if not moves:
            # Official Ashton does not assign a board winner on move exhaustion.
            self.stats.leaves += 1
            return evaluate(board)*(1 if board.side==0 else -1)
        value,best = -INF,moves[0]
        side = board.side
        for i,move in enumerate(moves):
            self._check()
            quiet = board.capture_hint(move)==0
            record = self._push(move)
            try:
                if self.pvs and i and alpha>-INF:
                    score = -self._search(depth-1,-alpha-1,-alpha,ply+1)
                    if alpha<score<beta:
                        self.researches += 1
                        score = -self._search(depth-1,-beta,-alpha,ply+1)
                else:
                    score = -self._search(depth-1,-beta,-alpha,ply+1)
            finally:
                self._pop(record)
            if score>value:
                value,best = score,move
            alpha = max(alpha,value)
            if alpha>=beta:
                self.stats.cutoffs += 1
                if quiet:
                    previous = self.killers.get(ply,())
                    self.killers[ply] = (move,)+tuple(m for m in previous if m!=move)[:1]
                    self.history_scores[side,move] = min(5000,self.history_scores.get((side,move),0)+depth*depth)
                break
        self._store(key,depth,value,original_alpha,original_beta,best,ply)
        return value

    def _quiescence(self, alpha, beta, ply, remaining):
        self._check()
        self.qnodes += 1
        board = self.board
        if board.outcome:
            self.stats.leaves += 1
            return self._terminal(ply)
        wins = board.winning_moves(check=self._check)
        if wins:
            return MATE-ply-1
        stand = evaluate(board)*(1 if board.side==0 else -1)
        if remaining<=0:
            self.stats.leaves += 1
            return stand
        threatened = bool(board.winning_moves(1-board.side,check=self._check))
        if not threatened:
            if stand>=beta:
                return stand
            alpha = max(alpha,stand)
        value = -INF if threatened else stand
        moves = self._order(board.moves(),ply=ply)
        searched = False
        for move in moves:
            capture = board.capture_hint(move)
            king_move = move//81==board.king
            if not threatened and not capture and not king_move:
                continue
            self._visit()
            record = self._push(move)
            try:
                # Quiet king moves are forcing only if they create an escape.
                forcing = threatened or capture or board.outcome or board.winning_moves(1-board.side,check=self._check)
                if not forcing:
                    continue
                searched = True
                score = -self._quiescence(-beta,-alpha,ply+1,remaining-1)
            finally:
                self._pop(record)
            value = max(value,score)
            alpha = max(alpha,value)
            if alpha>=beta:
                self.stats.cutoffs += 1
                break
        if threatened and not searched:
            return stand
        return value

    def _root(self, roots, depth, alpha, beta, preferred):
        values,best,value = [],preferred,-INF
        for i,move in enumerate(self._order(roots,preferred)):
            self._check()
            record = self._push(move)
            try:
                if self.pvs and i and alpha>-INF:
                    score = -self._search(depth-1,-alpha-1,-alpha,1)
                    if alpha<score<beta:
                        self.researches += 1
                        score = -self._search(depth-1,-beta,-alpha,1)
                else:
                    score = -self._search(depth-1,-beta,-alpha,1)
            finally:
                self._pop(record)
            values.append((move,score))
            if score>value:
                best,value = move,score
            alpha = max(alpha,value)
            if alpha>=beta:
                break
        return best,value,values

    def choose(self, position, limits):
        self.observe(position)
        started = time.monotonic()
        self.limits,self.stats,self.board = limits,Statistics(),Board(position)
        if position.terminal:
            raise ValueError("Cannot choose after game end")
        roots = self.board.moves()
        if not roots:
            raise ValueError("No legal move available")
        reserve = min(1.0,max(0.10,limits.seconds*0.12))
        self.deadline = started+max(0.0,limits.seconds-reserve)
        self.seen = set(self.played)
        self.context_hash = 0
        for key in self.seen:
            self.context_hash ^= hash(key)
        self.tt_hits,self.qnodes,self.researches = 0,0,0
        self.killers.clear()
        self.history_scores = {k:v//2 for k,v in self.history_scores.items() if v>1}
        best,value,records = self._order(roots)[0],None,[]
        safe,unsafe,checked = [],[],0
        iterations = []
        try:
            # Exact root safety precedes any heuristic ranking.
            wins = self.board.winning_moves(check=self._check)
            if wins:
                best,value = wins[0],MATE-1
                self.stats.completed_depth = 1
                self.stats.completed_roots = len(wins)
                self.stats.stop_reason = "immediate_win"
            else:
                root_scores = []
                for move in self._order(roots):
                    self._visit()
                    record = self._push(move)
                    try:
                        danger = not self.board.outcome and bool(self.board.winning_moves(check=self._check))
                        white_value = evaluate(self.board)
                        score = white_value if position.turn=="WHITE" else -white_value
                        if self.board.outcome:
                            score = -self._terminal(1)
                    finally:
                        self._pop(record)
                    checked += 1
                    (unsafe if danger else safe).append(move)
                    root_scores.append((move,score))
                    eligible = [(m,v) for m,v in root_scores if m in safe]
                    if eligible:
                        best,value = max(eligible,key=lambda item:item[1])
                roots = safe or roots
                if best not in roots:
                    best = roots[0]
                maximum = limits.depth or 64
                for depth in range(1,maximum+1):
                    self.stats.attempted_depth = depth
                    alpha,beta = (-INF,INF) if depth<3 or value is None else (value-150,value+150)
                    move,score,values = self._root(roots,depth,alpha,beta,best)
                    if score<=alpha or score>=beta:
                        move,score,values = self._root(roots,depth,-INF,INF,move)
                    best,value,records = move,score,values
                    self.stats.completed_depth,self.stats.completed_roots = depth,len(values)
                    iterations.append(dict(depth=depth,nodes=self.stats.nodes,score=value))
                    if abs(value)>MATE-1000:
                        self.stats.stop_reason = "forced_terminal"
                        break
                    if limits.depth is not None and depth>=limits.depth:
                        self.stats.stop_reason = "depth_limit"
                        break
        except SearchStopped:
            pass
        self.stats.elapsed_seconds = time.monotonic()-started
        return Decision(decode(best),value,self.stats,[(decode(m),v) for m,v in records],dict(
            profile="sentinel-ashton",source="custom",root_choices_checked=checked,
            unsafe_roots=len(unsafe),safe_roots=len(safe),root_safety_complete=checked==len(self.board.moves()),
            tt_hits=self.tt_hits,tt_entries=len(self.table),qnodes=self.qnodes,pvs_researches=self.researches,
            repetition_states=len(self.played),iterations=iterations,completed_iteration_adoption=True,
            seed_changes_play=False))
