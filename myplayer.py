#!/usr/bin/env python3
"""QuietGuard: the dependency-free UniBo Ashton competition entry point.

The validated transport is retained. Online and offline play use the same agent.
The submission manifest packages only that agent and the shared rules/API.
"""

import argparse
import json
from pathlib import Path
import socket
import struct
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent / "research/recreations/src"))
from sentinel.quiet_guard import SentinelQuietGuard as Sentinel
from tablut_agents.api import Limits
from tablut_agents.model import Position
from tablut_agents.rules import AshtonRules
from tablut_agents.offline_protocol import serve


PORTS = {"WHITE": 5800, "BLACK": 5801}
PLAYER_NAME = "QuietGuard"
TERMINAL_TURNS = {"WHITEWIN", "BLACKWIN", "DRAW"}
PAWNS = {"EMPTY", "WHITE", "BLACK", "KING", "THRONE"}
CAMPS = frozenset("a4 a5 a6 b5 d1 e1 f1 e2 i4 i5 i6 h5 d9 e9 f9 e8".split())
MAX_MESSAGE_BYTES = 1024 * 1024


def box(row, column):
    """Convert board[row][column] coordinates to a server square, e.g. e5."""
    return chr(ord("a") + column) + str(row + 1)


def legal_moves(board, role):
    """List legal actions using GameAshtonTablut.checkMove's movement rules.

    Walk in each orthogonal direction until blocked. A pawn starting outside a
    camp cannot enter or cross a camp. One starting inside can cross camps, but
    a camp destination more than five squares away is forbidden by the engine.
    THRONE is not EMPTY, so nobody can enter or cross an empty throne.
    """
    position = Position.from_json({"board": board, "turn": role})
    return [move.to_json(role) for move in AshtonRules().legal_moves(position)]


def recv_exact(connection, size):
    """TCP reads can be partial; keep reading until the whole frame arrives."""
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Server disconnected before the game result arrived.")
        data.extend(chunk)
    return bytes(data)


def read_json(connection):
    size = struct.unpack(">i", recv_exact(connection, 4))[0]
    if not 0 < size <= MAX_MESSAGE_BYTES:
        raise ValueError("Invalid message length from server.")
    return json.loads(recv_exact(connection, size).decode("utf-8"))


def send_json(connection, value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    connection.sendall(struct.pack(">i", len(payload)) + payload)


def validate_state(state):
    """Reject malformed states rather than choosing a move from guessed data."""
    if (not isinstance(state, dict) or not isinstance(state.get("turn"), str)
            or state["turn"] not in PORTS.keys() | TERMINAL_TURNS):
        raise ValueError("Invalid turn in server state.")
    board = state.get("board")
    if not isinstance(board, list) or len(board) != 9:
        raise ValueError("Expected a 9 by 9 board.")
    for row in board:
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError("Expected a 9 by 9 board.")
        if any(not isinstance(pawn, str) or pawn not in PAWNS for pawn in row):
            raise ValueError("Unknown pawn in server state.")


def play(role, timeout, server_ip):
    agent = Sentinel()
    with socket.create_connection((server_ip, PORTS[role]), timeout=timeout) as connection:
        send_json(connection, PLAYER_NAME)
        print(PLAYER_NAME + " connected as " + role, flush=True)
        while True:
            # Waiting for the opponent must not use our own move time limit.
            connection.settimeout(None)
            state = read_json(connection)
            received_at = time.monotonic()
            validate_state(state)
            turn = state["turn"]
            position = Position.from_json(state)
            agent.observe(position)
            if turn in TERMINAL_TURNS:
                print("Game finished: " + turn, flush=True)
                return
            if turn != role:
                continue

            # Charge parsing and searching to the same received-state budget.
            deadline = received_at + timeout - min(0.25, timeout * 0.1)
            moves = legal_moves(state["board"], role)
            if not moves:
                raise RuntimeError("No legal move available; refusing to send an illegal move.")
            allowance = max(0.0, timeout - (time.monotonic() - received_at))
            decision = agent.choose(position, Limits(allowance))
            move = decision.move.to_json(role)
            if move not in moves:
                raise RuntimeError("Sentinel returned an illegal move; refusing to send it.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Move selection exceeded the time budget.")
            connection.settimeout(remaining)
            send_json(connection, move)
            print("Move {}-{}; depth {}; nodes {}; {:.3f}s".format(
                move["from"], move["to"], decision.statistics.completed_depth,
                decision.statistics.nodes, decision.statistics.elapsed_seconds), flush=True)


def positive_seconds(value):
    try:
        seconds = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Timeout must be a positive integer.")
    if seconds < 1:
        raise argparse.ArgumentTypeError("Timeout must be a positive integer.")
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", type=str.upper, choices=PORTS)
    parser.add_argument("timeout", type=positive_seconds, help="move limit in seconds")
    parser.add_argument("server_ip", nargs="?")
    parser.add_argument("--offline", action="store_true", help="Use the arena JSON-lines protocol on stdin/stdout")
    args = parser.parse_args()
    if not args.offline and not args.server_ip:
        parser.error("server_ip is required in online mode")
    try:
        if args.offline:
            serve(Sentinel(),args.role,"sentinel-quiet-guard",Limits(args.timeout),sys.stdin,sys.stdout,sys.stderr)
        else:
            play(args.role, args.timeout, args.server_ip)
    except (OSError, ValueError, RuntimeError) as error:
        print(PLAYER_NAME + ": " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
