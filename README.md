# QuietGuard

QuietGuard plays the Ashton variant of Tablut for the **UniBo Tablut Challenge 2026/27**. It builds on Sentinel, a Python search engine, and improves how the engine scores positions where a player has to move under an immediate threat. The competition VM contains release [`69abb874a754`](RELEASE.json).

[Architecture and search concepts](docs/architecture.md) · [Development and release selection](docs/selection.md) · [Benchmarks and opponent credits](docs/benchmarks.md)

## Tournament launch

Run the command for the assigned role inside the prepared VM. Replace `SERVER_IP` with the referee’s address and `60` with the supplied time limit in seconds when it differs. The launcher uses Bash and the Python standard library. It was verified with Python 3.9.2 in the guest.

```sh
/home/tablut/tablut/runmyplayer.sh WHITE 60 SERVER_IP
/home/tablut/tablut/runmyplayer.sh BLACK 60 SERVER_IP
```

## How it plays

1. **Simulate moves locally.** The referee sends the current board over TCP. The player generates legal moves and uses a reversible Python board to explore hypothetical moves, captures, king escapes, and repetition draws. It sends the chosen move back to the referee.
2. **Check immediate tactics at the root.** Play an immediate win if available. Otherwise, search only the moves that avoid an immediate losing reply whenever such moves exist. A legal fallback covers interruptions before the first search round completes.
3. **Search progressively deeper.** Iterative deepening runs negamax with alpha–beta pruning. The move from the previous round, transposition-table moves, and earlier cutoffs help order the search. Principal variation search probes later moves with a narrow window. From depth three, the root search tries an aspiration window around the previous score and retries with a full window if needed.
4. **Score the positions at the cutoff.** The evaluation considers material, king mobility, escape routes, and pressure around the king. Quiescence selectively follows captures, forcing king moves, and defenses so the search can score their consequences.

## Why QuietGuard was added

A board can look safe at the search cutoff while the player to move is already lost. For example, Black can have all of the king’s escape routes blocked, yet every legal Black move opens an escape for White on the next turn. A static score of the current board can miss that forced loss.

QuietGuard checks whether at least one legal move survives the opponent’s immediate reply. If every legal move concedes a win, it returns a forced-loss score in two plies. When the player is already under threat and the quiescence budget runs out, it evaluates the boards reached by safe defenses and takes the best score. This brings the same immediate-reply check used at the root into the tactical cutoff.

## Development and testing

An offline cup among 39 historical opponent recreations helped identify a focused set of opponents for developing Sentinel. The project then tested Sentinel against all 39, used its losses to investigate the search cutoff, and compared several candidate changes before selecting QuietGuard. A later matched 60-second White panel recorded **5 wins, 1 draw, and 3 losses** for Sentinel and **5 wins and 4 draws** for QuietGuard across the same nine fixtures. [Development and release selection](docs/selection.md)

The exported VM was imported and booted in VirtualBox. It completed games against the official Java referee with QuietGuard in both roles, plus a self-play check. Separate 60-second launch checks returned a legal move for each role.

## Source layout

| File | Responsibility |
| --- | --- |
| [`runmyplayer.sh`](runmyplayer.sh) and [`myplayer.py`](myplayer.py) | Launcher, time limits, and referee communication |
| [`agent.py`](research/recreations/src/sentinel/agent.py) and [`evaluation.py`](research/recreations/src/sentinel/evaluation.py) | Search, move ordering, and positional evaluation |
| [`quiet_guard.py`](research/recreations/src/sentinel/quiet_guard.py) | Quiescence and the legal-move safety check |
| [`board.py`](research/recreations/src/sentinel/board.py) and [`rules.py`](research/recreations/src/tablut_agents/rules.py) | Reversible search board and Python implementation of the official rules |
| [`RELEASE.json`](RELEASE.json) | Runtime file checksums for the VM release |

## References and credits

- The official TablutCompetition project supplies the referee and the reference implementation for the Ashton rules. The upstream BSD 3-Clause notice credits Andrea Galassi. [Official TablutCompetition project](https://github.com/AGalassi/TablutCompetition) · [Upstream license notice](LICENSE)
- Russell and Norvig describe move ordering, iterative deepening, and quiescence in the game-search chapter of *Artificial Intelligence: A Modern Approach*. [AIMA, 4th Global Edition, Chapter 6](https://lib.ysu.am/disciplines_bk/efdd4d1d4c2087fe1cbe03d9ced67f34.pdf#page=201)
- Marsland describes aspiration windows and re-search in *A Review of Game-Tree Pruning*. [Section 2.4](https://webdocs.cs.ualberta.ca/~tony/OldPapers/icca.Mar1986.pp3-18.pdf)
- The authors and contributors behind the historical players supplied the upstream projects used to build the benchmark opponents. [Opponent credits and pinned GitHub revisions](docs/benchmarks.md#opponent-credits)
