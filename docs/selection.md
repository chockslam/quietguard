# How the release was selected

The project progressed from a legal-move client to Sentinel and then to QuietGuard. The historical opponent cup helped identify comparison players. Controlled matches and saved positions then helped identify and test changes to our own search. [Architecture and implementation](architecture.md) · [Benchmark records and opponent credits](benchmarks.md)

## 1. Build a usable test field

The early client exercised the official JSON/TCP protocol against the provided random bot and adapted historical student programs. Those runs surfaced integration issues such as launch failures, timeouts, and illegal moves. Even after deadline handling was repaired for a five-opponent panel, the initial local player scored **0 wins, 1 draw, and 9 losses** at both five and sixty seconds per move.

For broader comparisons, the project built Python recreations of **39 default opponent profiles and 41 alternatives** using pinned GitHub sources. All 39 defaults eventually completed a clean game in each role against the official Java server. The offline arena made it practical to run matched games and save positions, moves, timings, and endings. Official Java replays checked the resulting game states.

## 2. Run the historical opponent cup

The October 13 development cup put the 39 default recreations into **eight groups**. A pairing played both colours, with 20 seconds per move. Each group’s top two advanced to the **16-player knockout bracket**. Tied knockout pairings received an extra colour-swapped pair, then a recorded seeded draw if the scores remained tied.

The cup recorded **190 games**, with 189 normal endings and one EleMisi timeout forfeit. Weakmind and MrMeeseeks drew all four games in the final. The seeded tie-break selected **Weakmind** as the cup winner. Tavoletta and Nemo reached the semifinals. The result identified interesting comparison players, and a common-opponent league provided a more controlled follow-up.

The four-player league paired Weakmind, Tavoletta, MrMeeseeks, and PickleRicks in both colours. Weakmind and Tavoletta tied on points. A separate panel brought in Daniele and Bardreamaster against common opposition. Weakmind, Tavoletta, MrMeeseeks, and Daniele were then used for the first focused Sentinel comparisons. This was a local development tournament among the recreated players.

## 3. Test Sentinel and investigate the losses

The optimized Sentinel scored **6–1–1** against the four focused opponents at 20 seconds per move. Its expanded benchmark retained those eight games and added 70, for **78 games** against all 39 defaults. Sentinel scored **75–1–2** overall. As White, it lost to B2P and Tavoletta and drew against Daniele. Five follow-up games as White against Tavoletta all ended in losses.

Saved positions gave us a way to test one specific cutoff problem. In a B2P fixture, White had three legal king moves and each let Black capture the king immediately. In a Tavoletta fixture, both legal defender moves did the same. The original tactical cutoff returned ordinary heuristic scores on those boards. Enumerating the replies established a forced loss in two plies. That led to the safety check described in the [quiescence implementation](architecture.md#quiescence-and-the-quietguard-change).

## 4. Compare candidate changes

Candidate changes were tested on fixed positions and in timed games. Fixed-depth comparisons checked whether an optimization changed the moves or scores. Timed games checked what the change meant with a limited budget.

| Candidate | What was tested | Decision |
| --- | --- | --- |
| Forced-move guard | Check for a safe legal move before using a static cutoff score. In the 36-game six-second screen it scored 24–3–9, compared with Sentinel’s 29–4–3. | Keep Sentinel for that release. |
| Mobility guard | Add an evaluation penalty for a live position with zero legal moves. It scored 26–1–9 in the same screen. | Keep the original evaluation. |
| Tactical candidate ordering optimization | Classify tactical candidates before sorting. It matched the sampled fixed-depth decisions and reduced median runtime by about 11% in those tests. Its six-second game results fell from 11–1–0 to 10–0–2. | Keep the existing search order code. |
| Quiet-soldier extension | Follow a quiet soldier move that opens a forced king escape. It solved a known tactical fixture, and both versions lost the clean 20-second White pilot against default Tavoletta. | Keep the fixture as a known limitation of the shipped quiescence search. |
| QuietGuard with defensive evaluation | Check for a safe legal move and score the actual defenses when quiescence ends under a threat. In the later six-second screen it gained two points over 23 normally completed matched pairs, with all gains as White. | Retain this candidate for release consideration. |

The later six-second screen had one unscored Black game against Daniele that reached the whole-game cap. The declared gate required a fully scored panel, so its planned follow-ups stopped there. A separate replay at 60 seconds per move from the same opening ended in a QuietGuard win as Black. [Recorded benchmark scope](benchmarks.md#results)

## 5. Select and verify QuietGuard

The release decision selected `SentinelQuietGuard(resolve_cutoff_threats=True)` for its specific correction to tactical cutoff scoring. The later matched 60-second White study supported retaining that build. Across nine games per version, QuietGuard scored **5–4–0** versus Sentinel’s **5–1–3**. B2P accounted for the net point gain, and one original win against Weakmind became a draw. The matched study covered White. Separate Black games and alternate-profile tests supplied additional evidence under their own conditions.

The shipped release is [`69abb874a754`](../RELEASE.json). Validation replayed move sets and state transitions against the official Java rules, verified the runtime files inside the imported VirtualBox appliance, and exercised the live launch path for both roles. The tactical guard covers immediate winning replies. Longer threats, king containment, and escort preservation still depend on the search and evaluation.

## Research records

| Stage | Record in the research archive |
| --- | --- |
| Historical cup and controlled follow-up | `cup-39-full/report.md` and `focused-study/report.md` |
| Sentinel against 39 opponents | `sentinel-all39-20s/games.csv` |
| Early guard regressions | `SENTINEL_REGRESSION.md` |
| November matched and full-budget studies | `quiet-guard-20261117/RESULTS.md`, `quiet-guard-white-60s-20261117/RESULTS.md`, and `quiet-guard-variants-20261117/REPORT.md` |
| VirtualBox release verification | `verification/fresh-original/virtualbox-check.json` |
