"""Small interfaces shared by reproductions, diagnostics and match clients.

Limits are explicit experiment inputs. A diagnostic depth/node limit is never
silently substituted for a submitted bot's configured search horizon.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import random
import math
import time
from typing import Protocol
from .model import Move, Position


@dataclass(frozen=True)
class Limits:
    seconds: float = 60.0
    depth: int | None = None
    nodes: int | None = None
    simulations: int | None = None

    def __post_init__(self):
        if not math.isfinite(self.seconds) or self.seconds < 0:
            raise ValueError("seconds must be finite and nonnegative")
        for value in (self.depth, self.nodes, self.simulations):
            if value is not None and value < 1:
                raise ValueError("diagnostic limits must be positive")


@dataclass
class Statistics:
    nodes: int = 0
    leaves: int = 0
    cutoffs: int = 0
    simulations: int = 0
    completed_depth: int = 0
    attempted_depth: int = 0
    completed_roots: int = 0
    elapsed_seconds: float = 0.0
    stop_reason: str = "finished"


@dataclass
class Decision:
    move: Move
    value: float | None
    statistics: Statistics
    # Ordered records distinguish evaluated roots from legal fallbacks.
    root_values: list[tuple[Move, float]] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)


class Agent(Protocol):
    def choose(self, position: Position, limits: Limits) -> Decision: ...


class SearchStopped(Exception):
    """Cooperative replacement for killing a source search thread."""


class Budget:
    def __init__(self, limits, statistics, reserve=0.0, clock=time.monotonic):
        self.limits, self.statistics, self.clock = limits, statistics, clock
        self.start = clock()
        self.deadline = self.start + max(0.0, limits.seconds - reserve)

    def expired(self):
        if self.limits.nodes is not None and self.statistics.nodes >= self.limits.nodes:
            self.statistics.stop_reason = "node_limit"
            return True
        if self.clock() > self.deadline:
            self.statistics.stop_reason = "deadline"
            return True
        return False

    def visit(self):
        if self.expired():
            raise SearchStopped
        self.statistics.nodes += 1

    def finish(self):
        self.statistics.elapsed_seconds = self.clock() - self.start


class JavaRandom:
    """java.util.Random nextInt and Collections.shuffle, for controlled checks."""
    def __init__(self, seed):
        self.state = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def bits(self, n):
        self.state = (self.state * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        return self.state >> (48 - n)

    def randrange(self, bound):
        if bound <= 0:
            raise ValueError("Empty random choice")
        if bound & (bound - 1) == 0:
            return (bound * self.bits(31)) >> 31
        while True:
            bits = self.bits(31)
            value = bits % bound
            if bits - value + bound - 1 < (1 << 31):
                return value

    def choice(self, values):
        return values[self.randrange(len(values))]

    def random(self):
        return ((self.bits(26) << 27) + self.bits(27)) / float(1 << 53)

    def shuffle(self, values):
        for i in range(len(values), 1, -1):
            j = self.randrange(i)
            values[i - 1], values[j] = values[j], values[i - 1]


class RandomAgent:
    def __init__(self, seed=1, rules=None):
        from .rules import AshtonRules
        self.random, self.rules = random.Random(seed), rules or AshtonRules()

    def choose(self, position, limits):
        moves = self.rules.legal_moves(position)
        if not moves:
            raise ValueError("No legal move")
        return Decision(self.random.choice(moves), None, Statistics())


class NumpyRandomState:
    """Legacy NumPy RandomState's MT19937 integer choice, without a dependency.

The source calls np.random.choice on move arrays. This adapter retains its
masked rejection sampler instead of substituting Python's differently seeded
MT19937. Seed is an unsigned 32-bit value, as for np.random.seed.
    """
    def __init__(self, seed):
        self.state = [seed & 0xFFFFFFFF]
        for i in range(1, 624):
            previous = self.state[-1]
            self.state.append((1812433253 * (previous ^ (previous >> 30)) + i) & 0xFFFFFFFF)
        self.index = 624
        self.gaussian = None

    def uint32(self):
        if self.index >= 624:
            for i in range(624):
                y = (self.state[i] & 0x80000000) | (self.state[(i + 1) % 624] & 0x7FFFFFFF)
                self.state[i] = self.state[(i + 397) % 624] ^ (y >> 1) ^ (0x9908B0DF if y & 1 else 0)
            self.index = 0
        y = self.state[self.index]
        self.index += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        return y & 0xFFFFFFFF

    def randrange(self, bound):
        if bound <= 0:
            raise ValueError("Empty random choice")
        maximum = bound - 1
        if maximum == 0:
            return 0
        mask = (1 << maximum.bit_length()) - 1
        while True:
            value = self.uint32() & mask
            if value <= maximum:
                return value

    def choice(self, values):
        return values[self.randrange(len(values))]

    def random(self):
        return ((self.uint32() >> 5)*67108864.0+(self.uint32() >> 6))/9007199254740992.0

    def normal(self):
        """Legacy NumPy RandomState polar Gaussian, including cached partner."""
        if self.gaussian is not None:
            result,self.gaussian=self.gaussian,None
            return result
        while True:
            x1,x2=2*self.random()-1,2*self.random()-1
            r2=x1*x1+x2*x2
            if 0 < r2 < 1: break
        factor=math.sqrt(-2*math.log(r2)/r2)
        self.gaussian=factor*x1
        return factor*x2
