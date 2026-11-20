# Benchmarks and opponent credits

QuietGuard was evaluated against Python recreations built from pinned revisions of historical Tablut players. The recreation names identify the profiles used in the tests. The GitHub links credit the upstream projects and point to the source revisions used as references.

[Development cup and release selection](selection.md) · [Architecture and implementation](architecture.md)

## Results

All time limits are per move. W–D–L means wins, draws, and losses from Sentinel’s or QuietGuard’s perspective. Each row reports its own match conditions.

| Test | Setup | Sentinel W–D–L | QuietGuard W–D–L |
| --- | --- | ---: | ---: |
| Historical opponent screen, 20 s | 39 default opponent profiles, one standard-start game in each role per opponent | 75–1–2 | — |
| Matched screen, 6 s | B2P, Daniele, Tavoletta, and Weakmind, three starts, both roles | 13–4–7 | 15–2–6, plus 1 unscored |
| Matched White study, 60 s | B2P, Daniele, and Weakmind, three starts, nine games as White per version | 5–1–3 | 5–4–0 |
| Alternate profiles, 60 s | Eight profiles, one standard-start game in each role per profile | — | 13–1–0, plus 2 unscored |
| Daniele replay, 60 s | One Black game from a prescribed four-ply opening | — | 1–0–0 |

The six-second screen left one QuietGuard game unfinished at the whole-game cap. The two unscored games in the alternate-profile panel ended when the `weakmind-final` recreation reached its memory limit. The matched 60-second comparison covers White only. Its three opponents and three openings give a concrete comparison of the cutoff change on that set of positions.

The November panels ran in a native Windows offline arena. Completed traces were replayed against the official Java rules. The VM compatibility checks used the separate TCP referee and exercised the actual launcher, including full short-budget games and a 60-second turn for each role. The referee used for the research was pinned to the official repository. [Referee source revision](https://github.com/AGalassi/TablutCompetition/tree/96983984e42c6b846ff5f6fb473754da3da21292)

## Opponent credits

### Opponents in the focused QuietGuard tests

| Opponent family | Profiles in the studies above | Upstream repository at the referenced revision |
| --- | --- | --- |
| B2P | `b2p` | [AlessandroPomponio/B2P-Penicilin-Tablut-AI at `c8a5664c86a5`](https://github.com/AlessandroPomponio/B2P-Penicilin-Tablut-AI/tree/c8a5664c86a51154afd5c193c567d98441a2146d) |
| Daniele | `daniele` | [MatteoCastiglio/Daniele at `fc13f5963700`](https://github.com/MatteoCastiglio/Daniele/tree/fc13f5963700b763f02e93485ad0bdab3c61a386) |
| EleMisi | `elemisi-rays-fixed` | [EleMisi/TablutAI at `1b500d36336e`](https://github.com/EleMisi/TablutAI/tree/1b500d36336eec62c5f9ad0bdc9b0f3c10588314) |
| Mbappé | `mbappe-timer-fixed` | [LorenzoCassano/TablutChallenge22-23 at `a2f3458764e8`](https://github.com/LorenzoCassano/TablutChallenge22-23/tree/a2f3458764e8a55c793dc1329ab82087a0c24ce9) |
| NotXia | `notxia-cython-semantics` | [NotXia/tablut-player at `2f7bbb95eab1`](https://github.com/NotXia/tablut-player/tree/2f7bbb95eab1cab87b8acd264416c4db8d23ea70) |
| O’Sarracino | `osarracino-collision` | [federico-terzi/osarracino at `ae34855a1881`](https://github.com/federico-terzi/osarracino/tree/ae34855a1881282f35f556c4dde95d281ad0db0c) |
| Tavoletta | `tavoletta`, `tavoletta-mcts-reset` | [Gionnino9000/Gionnino9000 at `7d4bf1c16d44`](https://github.com/Gionnino9000/Gionnino9000/tree/7d4bf1c16d44a2053dd72941f83a77b7daadff18) |
| Weakmind | `weakmind`, `weakmind-final`, `weakmind-hard`, `weakmind-mcts` | [Zeegomo/weakmind at `5b9461704076`](https://github.com/Zeegomo/weakmind/tree/5b94617040761c6b32071caa87b2d371c59a6fe6) |

### Additional opponents in the Sentinel screen

The earlier 39-opponent screen also included the eight families above, using each family’s default recreation.

| Recreation | Upstream repository at the referenced revision |
| --- | --- |
| `almarima` | [alessandrostockman/almarima-tablut at `0e80c1133c9a`](https://github.com/alessandrostockman/almarima-tablut/tree/0e80c1133c9ae1966e7e2349022fc3ea29343f0e) |
| `almazeneca` | [HerbieNaL/Tablut_AlmaZeneca at `903a5c4c6f6b`](https://github.com/HerbieNaL/Tablut_AlmaZeneca/tree/903a5c4c6f6b825786d0d9779d6787080e30b1d0) |
| `aminmk` | [aminmk99/TablutPython at `c60713dc3dd2`](https://github.com/aminmk99/TablutPython/tree/c60713dc3dd262bc8b75e551f51831787a2de4dd) |
| `andrea` | [AndreaTerenz/PyTablut at `d2f10bb8cf79`](https://github.com/AndreaTerenz/PyTablut/tree/d2f10bb8cf7911154753b6e0bd906536bea722a9) |
| `bardreamaster` | [Bardreamaster/pytablut at `844220598e39`](https://github.com/Bardreamaster/pytablut/tree/844220598e39b1ccdcfd693c8c18b5d1c4bafadf) |
| `brainmates` | [gmurro/Tablut at `7d870839fb60`](https://github.com/gmurro/Tablut/tree/7d870839fb60a3c25530c42e0049ff82fe8e0d25) |
| `bug` | [DaniDF/BugTablutChallenge at `b513932578ed`](https://github.com/DaniDF/BugTablutChallenge/tree/b513932578ed4aadd62320c6266ddf27861ecafc) |
| `colish` | [riccardo-cozzi/ColishTablut at `9dccd488cbc1`](https://github.com/riccardo-cozzi/ColishTablut/tree/9dccd488cbc125f5f816fff1149bdf23a3a8cfab) |
| `cristina` | [nickromandini/TablutPlayer at `b47ca78bb062`](https://github.com/nickromandini/TablutPlayer/tree/b47ca78bb06233ac5852cec9b39f4286a6b77f6b) |
| `demetrios` | [demetrios-koziris/comp-424-tablut-ai-project at `56d0109b0f88`](https://github.com/demetrios-koziris/comp-424-tablut-ai-project/tree/56d0109b0f8834209e22c98752cfe63a705c7d15) |
| `fashad` | [Fashad-Ahmed/Tablut-challenge at `3cbe75cbb634`](https://github.com/Fashad-Ahmed/Tablut-challenge/tree/3cbe75cbb634de014082c1d0deff9cb893cf7b64) |
| `fpm` | [contimatteo/Tablut-PMF at `9886583d2027`](https://github.com/contimatteo/Tablut-PMF/tree/9886583d2027beb2c0941c753f78bfb42ba8ae36) |
| `frittomisto` | [virtualms/Tablut2020_FrittoMisto at `ed384e517ea4`](https://github.com/virtualms/Tablut2020_FrittoMisto/tree/ed384e517ea48c17d84d07de801f7e1373e647d1) |
| `giuseppe` | [alebov/IbimbidiGiuseppeConte at `6abaf7b26dfa`](https://github.com/alebov/IbimbidiGiuseppeConte/tree/6abaf7b26dfaee623366dffec6a7294034699ded) |
| `ibratanov` | [ibratanov/tablut.ai at `536c65cd3f04`](https://github.com/ibratanov/tablut.ai/tree/536c65cd3f049bc5dab984d417f4050d9cc46602) |
| `kyndill` | [splicer3/Kyndill at `3a907cf9b9ca`](https://github.com/splicer3/Kyndill/tree/3a907cf9b9ca711cf32700e85781ff765bd5ac41) |
| `lodale` | [davideligabue/TablutChallenge at `ad1c9c916dcf`](https://github.com/davideligabue/TablutChallenge/tree/ad1c9c916dcfac2a763208bc06a0780767688989) |
| `matteofasulo` | [MatteoFasulo/Tablut at `a56a1c269318`](https://github.com/MatteoFasulo/Tablut/tree/a56a1c2693187402df4b3378e2bfb7cbab1cfda3) |
| `mazzo` | [mazzo98/Tablut at `fee91fe9c965`](https://github.com/mazzo98/Tablut/tree/fee91fe9c965f5d5573be10972844d75b775533b) |
| `mrmeeseeks` | [AlessandroMusarella/Tablut at `f5c25168b5e6`](https://github.com/AlessandroMusarella/Tablut/tree/f5c25168b5e6df41f71cd56888b41860aba93c76) |
| `nemo` | [mcampestri/NemoTablut at `79fafaaac748`](https://github.com/mcampestri/NemoTablut/tree/79fafaaac748494b8fde8e4a2c381a36ce6c9ac1) |
| `picklericks` | [lorenzo-bonetti/TablutAI at `d2ca294f0ce9`](https://github.com/lorenzo-bonetti/TablutAI/tree/d2ca294f0ce9c044349df2f669b5c872a4b359f3) |
| `tabloidi` | [FedeSpu/TablutCompetition at `50c90c62a505`](https://github.com/FedeSpu/TablutCompetition/tree/50c90c62a505d5451801d43112dea6aa443b5377) |
| `tablutzero` | [tonislees/TablutZero at `0850331a624a`](https://github.com/tonislees/TablutZero/tree/0850331a624afe6261d1f513e43e76dc8aad0e19) |
| `tabroot` | [LorenzoPiazza/Tabroot at `ab51832999be`](https://github.com/LorenzoPiazza/Tabroot/tree/ab51832999be92b31cd3168c2ade0c7ced58394b) |
| `tabularasa` | [MoAITeam/TabulaRasa at `3788e365a4bb`](https://github.com/MoAITeam/TabulaRasa/tree/3788e365a4bb750d62e4ac4ae905d0757d57b60b) |
| `teammy` | [TeammyTurner/TablutAI at `bcc0bd14302d`](https://github.com/TeammyTurner/TablutAI/tree/bcc0bd14302d486043496bf841dff78486de4569) |
| `thor` | [carlo98/tablut-THOR at `b990d49c6673`](https://github.com/carlo98/tablut-THOR/tree/b990d49c66735c40afbfa7d26aeec7694a80a729) |
| `unibot` | [chrifio01/tablut_UniBOt at `96b833eb0ddd`](https://github.com/chrifio01/tablut_UniBOt/tree/96b833eb0dddd3419013bed3ab8686cc8fa26c8e) |
| `wadaboa` | [Wadaboa/Tablut at `e4e60bf3c744`](https://github.com/Wadaboa/Tablut/tree/e4e60bf3c7444cf2f8cf1f7fef22c961fd0d5304) |
| `yiniang` | [imRaazy/YinIAngWarriorsTablut at `bd1131c625e9`](https://github.com/imRaazy/YinIAngWarriorsTablut/tree/bd1131c625e9eb801a8ca5c22c3c172ea3036cfb) |

The Teammy recreation also drew on the project’s MCTS companion. [TeammyTurner/tablut-mcts at `9d82cec6bbea`](https://github.com/TeammyTurner/tablut-mcts/tree/9d82cec6bbea2ae176c5f35658c100d2f272aedf)
