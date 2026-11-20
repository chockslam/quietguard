# QuietGuard

QuietGuard is a Python player for the UniBo Tablut Challenge 2026/27. This repository contains the player packaged in the prepared VirtualBox appliance. [RELEASE.json](RELEASE.json) records the runtime files and their checksums for release `69abb874a754`.

## Tournament launch

Inside the prepared VM, run the command for the assigned role.

```sh
/home/tablut/tablut/runmyplayer.sh WHITE 60 SERVER_IP
/home/tablut/tablut/runmyplayer.sh BLACK 60 SERVER_IP
```

Use the referee’s server IP and time limit in seconds. The player uses Bash and Python’s standard library.

## Upstream attribution

The official [TablutCompetition project](https://github.com/AGalassi/TablutCompetition) supplies the referee and the reference implementation for the Ashton rules used by QuietGuard. The [LICENSE](LICENSE) file preserves Andrea Galassi’s upstream BSD 3-Clause copyright notice and license terms.
