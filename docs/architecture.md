# Architecture and search concepts

QuietGuard runs as one persistent Python player process. It receives official positions from the referee, explores temporary positions locally, and returns a single move on its turn. The shipped class is `SentinelQuietGuard`, which uses Sentinel’s ordinary search and overrides its quiescence search. [Tournament class selection](../myplayer.py#L16) · [QuietGuard class](../research/recreations/src/sentinel/quiet_guard.py#L13)

```text
runmyplayer.sh
  myplayer.py main()
    play() over referee TCP, or serve() for the offline arena
      Position and the agent's observe()
      SentinelQuietGuard.choose()
        Sentinel.choose() orders the root and sets the search budget
          _root() searches one depth of iterative deepening
            _search() explores the reversible Board
              _quiescence() probes safety and follows forcing moves
                evaluate() scores a single board when needed
      play() checks and sends Decision.move to the referee
      serve() emits an offline decision event
```

## Transport and time limits

[`runmyplayer.sh`](../runmyplayer.sh) locates and runs `myplayer.py` from the launcher’s directory. [`main()`](../myplayer.py#L137) reads the role, timeout in seconds, and referee address. It normalizes the role to uppercase and selects either the tournament TCP client or the development-only `--offline` interface.

[`play()`](../myplayer.py#L87) registers as `QuietGuard` and exchanges UTF-8 JSON with a four-byte big-endian length prefix. `recv_exact()` assembles partial TCP reads. The client validates incoming board messages, gives every observed position to the agent for repetition tracking, and calls `choose()` when it is the assigned player’s turn. Before sending the result, it checks the chosen move against the reference legal-move generator. [Framing and validation](../myplayer.py#L37) · [Response validation](../myplayer.py#L107)

The client measures the move budget from receipt of the position and passes the remaining allowance into `Limits`. `choose()` reserves time for cleanup and reply. The recursive search checks its deadline and can unwind with `SearchStopped`, restoring trial moves through `finally`. The answer is the best move from the deepest completed round, with a legal fallback available before the first round completes. [Search limits and stopping checks](../research/recreations/src/sentinel/agent.py#L53) · [Budget setup and fallback](../research/recreations/src/sentinel/agent.py#L249) · [Result adoption](../research/recreations/src/sentinel/agent.py#L300)

## Board and rules

- **Immutable position.** `Position` stores 81 cells and a turn. `Move` stores source and target indices and converts them to the referee’s coordinates. Camps and throne information live with the shared model. [Shared model and coordinates](../research/recreations/src/tablut_agents/model.py#L11)
- **Reference rules.** `AshtonRules` generates legal moves and applies moves, captures, and outcomes. `History` models the official repetition behavior. The TCP client uses this implementation for the final legality check. [Reference rules and history](../research/recreations/src/tablut_agents/rules.py#L32)
- **Search board.** `Board` stores mutable cells, piece bitboards, the king location, the side to move, and the outcome. Precomputed rays and masks speed up move generation. Moves are encoded as `source * 81 + target`. `push()` makes a trial move and records what changed, then `pop()` restores it. [Board representation](../research/recreations/src/sentinel/board.py#L12) · [Make and undo](../research/recreations/src/sentinel/board.py#L92)
- **Exact tactical checks.** `winning_moves()` limits the candidates to moves that could let the king escape or complete a king capture, then verifies them with the board rules. The search layer records real and hypothetical repetitions and clears its repetition set after a capture. [Immediate win detection](../research/recreations/src/sentinel/board.py#L152) · [Search repetition tracking](../research/recreations/src/sentinel/agent.py#L42)

The official Java implementation is the reference for Ashton movement, captures, and repetition behavior. The Python board exists so the agent can evaluate many trial moves locally during one referee turn. [Pinned TablutCompetition rules reference](https://github.com/AGalassi/TablutCompetition/tree/96983984e42c6b846ff5f6fb473754da3da21292)

## Concepts and their implementation

A ply is one move by either side. `depth` tracks ordinary plies remaining, `ply` tracks distance from the root, and `remaining` is the separate quiescence budget. `_root()` makes the first move, so a depth-three round calls `_search(2, ...)` for the opponent’s reply.

| Concept | How QuietGuard uses it | Code |
| --- | --- | --- |
| Root safety | Keep a legal fallback. Take an immediate win when available. Otherwise, test each candidate for an immediate winning reply and restrict the root search to safe moves when at least one exists. | [`choose()`](../research/recreations/src/sentinel/agent.py#L267) |
| Iterative deepening | Search from the root at depths 1, 2, 3, and so on. Start each round with the previous best move. Adopt a result once the round has completed. | [Depth loop](../research/recreations/src/sentinel/agent.py#L300) |
| Negamax and alpha–beta | Make a move, search the child from the other side’s perspective, and negate the returned score. Update `alpha` as scores improve and stop exploring siblings when `alpha >= beta`. The child receives the sign-flipped window `(-beta, -alpha)`. | [Recursive move loop](../research/recreations/src/sentinel/agent.py#L152) |
| Principal variation search | Give the first move the current window. With a finite `alpha`, probe later moves with `(-alpha-1, -alpha)` from the child’s perspective. Re-search a move with the wider window when its probe score falls strictly between `alpha` and `beta`. | [Interior PVS](../research/recreations/src/sentinel/agent.py#L156) · [Root PVS](../research/recreations/src/sentinel/agent.py#L226) |
| Aspiration windows | Start depths 1 and 2 with a full root window. From depth 3, use the previous score ±150 and retry that depth with a full window if the score touches or crosses either bound. | [Root window and retry](../research/recreations/src/sentinel/agent.py#L300) |
| Move ordering | Promote the preferred move from the previous depth or table entry. Rank the rest using capture hints, king movement, and past cutoffs. Store up to two quiet cutoff moves per ply as killer moves. Give those quiet cutoff moves a separate side-and-move history bonus. | [`_order()`](../research/recreations/src/sentinel/agent.py#L94) · [Cutoff updates](../research/recreations/src/sentinel/agent.py#L166) |
| Transposition table | Cache an interior position’s best move, searched depth, score or bound, and repetition context. Use a cached move for ordering. Use its score when the stored depth is sufficient and its repetition context matches. Exact entries can return immediately. Bounds narrow the window and can cause a cutoff. | [Entry storage](../research/recreations/src/sentinel/agent.py#L112) · [Lookup](../research/recreations/src/sentinel/agent.py#L131) |
| Static evaluation | Score material, king mobility, distance to an exit, open routes, guards, and nearby Black pressure. The raw score is from White’s perspective. The search converts it to the side to move and handles wins, losses, and draws with terminal scores. | [`evaluate()`](../research/recreations/src/sentinel/evaluation.py#L21) · [Terminal scoring](../research/recreations/src/sentinel/agent.py#L88) |

The lookup key records the board and side to move. The history check matters because two identical boards can lead to different repetition draws based on earlier positions. The default table holds up to 32,768 entries. Mate scores are adjusted on write and read so that the distance to a win or loss stays meaningful across different roots. [Table defaults and entry fields](../research/recreations/src/sentinel/agent.py#L21) · [Mate normalization](../research/recreations/src/sentinel/agent.py#L112)

Negamax, alpha–beta, iterative deepening, move ordering, transposition tables, PVS, and aspiration are established search techniques. The board features, move-ordering weights, and the safety check at the quiescence cutoff are choices in this player’s implementation. [AIMA, Chapter 6](https://lib.ysu.am/disciplines_bk/efdd4d1d4c2087fe1cbe03d9ced67f34.pdf#page=201) · [Marsland, *A Review of Game-Tree Pruning*](https://webdocs.cs.ualberta.ca/~tony/OldPapers/icca.Mar1986.pp3-18.pdf)

## Quiescence and the QuietGuard change

When `_search()` reaches zero ordinary depth on a live board, it calls `_quiescence()` with a separate budget of two tactical plies by default. Quiescence extends selected lines, such as captures and forcing king moves, to reduce misleading scores at an unstable cutoff. The original Sentinel checks for a win in one and, at an exhausted quiescence budget, can return the current-board evaluation. [Quiescence handoff](../research/recreations/src/sentinel/agent.py#L123) · [Original cutoff](../research/recreations/src/sentinel/agent.py#L179)

QuietGuard checks whether the side to move can survive playing an actual move. `_safe_actions()` makes a legal move, checks for a winning reply, and restores the board. It can stop at the first safe choice in an ordinary position. In a threatened position the shipped profile collects safe defenses. [Safety probe](../research/recreations/src/sentinel/quiet_guard.py#L35)

| Situation | QuietGuard’s response |
| --- | --- |
| Every legal move gives the opponent an immediate win | Return `-MATE + ply + 2` for the side to move. The two plies are its move and the winning reply. |
| A threat exists and tactical depth remains | Recursively search the safe defenses. |
| A threat exists and the tactical budget is exhausted | Evaluate the position after each safe defense, using the terminal score if the defense ends the game, and take the best score. This is the additional bounded defensive ply enabled by `resolve_cutoff_threats=True`. |
| An ordinary position has a safe legal move | Use the static score as a baseline and follow selected tactical moves while the budget allows. |

For a position with zero legal moves, this quiescence implementation returns the static score. For a recorded game outcome, it returns the terminal score. [QuietGuard scoring and recursion](../research/recreations/src/sentinel/quiet_guard.py#L70)

## Other files in the release

| File | Role |
| --- | --- |
| [`api.py`](../research/recreations/src/tablut_agents/api.py) | Search inputs and outputs, including `Limits`, `Statistics`, `Decision`, and `SearchStopped` |
| [`offline_protocol.py`](../research/recreations/src/tablut_agents/offline_protocol.py) | Persistent JSON-lines interface for the research arena. It accepts `observe`, `choose`, and `stop` and calls the same agent. |
| [`reporting.py`](../research/recreations/src/tablut_agents/reporting.py) | Serializes decisions and diagnostics for the offline arena |
| [`sentinel/__init__.py`](../research/recreations/src/sentinel/__init__.py) and [`tablut_agents/__init__.py`](../research/recreations/src/tablut_agents/__init__.py) | Package entry points and public imports |
| [`RELEASE.json`](../RELEASE.json) and [`LICENSE`](../LICENSE) | Appliance release ID and file hashes, and the upstream license notice |
