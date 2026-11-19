"""Persistent JSON-lines arena protocol without the full student registry."""

import json
import time
from .model import Position
from .reporting import decision_event


def serve(agent,role,name,limits,requests,replies,diagnostics):
    def reply(message):
        print(json.dumps(message,allow_nan=False),file=replies,flush=True)
    reply({"event":"ready","role":role,"agent":name})
    position,decisions = None,0
    for line in requests:
        command = json.loads(line)
        if command["event"] == "observe":
            position = Position.from_json(command["position"])
            observe = getattr(agent,"observe",None)
            if observe is not None:
                observe(position)
            reply({"event":"observed"})
            if position.terminal:
                print(json.dumps({"event":"result","outcome":position.turn,
                                  "decisions":decisions}),file=diagnostics,flush=True)
                return
        elif command["event"] == "choose":
            if position is None or position.terminal or position.turn!=role:
                raise ValueError("Choose requested outside this player's turn")
            started = time.monotonic()
            decision = agent.choose(position,limits)
            decisions += 1
            event = decision_event(position,role,name,decisions,decision)
            event["choose_wall_seconds"] = time.monotonic()-started
            print(json.dumps(event,allow_nan=False),file=diagnostics,flush=True)
            reply(event)
        elif command["event"] == "stop":
            reply({"event":"stopped"})
            return
        else:
            raise ValueError("Unknown arena request")
