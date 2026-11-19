"""Dependency-free decision records shared by online and offline transports."""

from dataclasses import asdict
import hashlib
import json
import math


def diagnostic_json(value):
    if isinstance(value,float) and not math.isfinite(value):
        return str(value)
    if isinstance(value,dict):
        return {k:diagnostic_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [diagnostic_json(v) for v in value]
    return value


def decision_event(position,role,name,decisions,decision):
    return diagnostic_json({"event":"decision","ply_for_player":decisions,
        "agent":name,"role":role,"position_sha256":hashlib.sha256(json.dumps(
            position.to_json(),sort_keys=True).encode()).hexdigest(),
        "move":decision.move.to_json(role),"value":decision.value,
        "statistics":asdict(decision.statistics),"diagnostics":decision.diagnostics})
