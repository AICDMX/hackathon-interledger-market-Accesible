# VoxVox Remote Dev Server

## Quick Start

```bash
cd terraform
make ssh            # shell on the server
make claude         # Claude Code in tmux
make codex          # Codex CLI in tmux
```

That's it. The Makefile handles SSH, keys, and connections automatically.

## Connection Details

| Field    | Value                        |
|----------|------------------------------|
| Host     | `$(make -s ip)` / Terraform `external_ip` |
| User     | `dev`                        |
| Key      | `terraform/voxvox-ssh-key`   |
| Port     | `22` (default)               |

Manual SSH (if not using the Makefile):

```bash
ssh -i terraform/voxvox-ssh-key dev@$(cd terraform && make -s ip)
```

## What's on the Server

- **OS:** Ubuntu 22.04 LTS
- **Project:** `~/marketplace` — the hackathon-interledger-market-Accesible repo
- **Python:** managed with `uv` (virtualenv in marketplace-py)
- **Docker:** running via docker compose in `~/marketplace-deploy`
- **Django:** dev server on port 8000
- **Claude Code** and **Codex CLI** installed globally via npm
- **tmux** for persistent sessions

## Makefile Commands

Run these from the `terraform/` directory.

### Connect

| Command          | What it does                              |
|------------------|-------------------------------------------|
| `make ssh`       | Open a shell as the `dev` user            |
| `make tmux`      | Attach to tmux session chooser            |
| `make tunnel`    | Forward server port 8000 to localhost:8000|
| `make logs`      | Tail the VM startup log                   |
| `make status`    | Show VM status and running containers     |
| `make ip`        | Print the server IP                       |

### AI Tools

| Command              | What it does                                  |
|----------------------|-----------------------------------------------|
| `make claude`        | Launch Claude Code in tmux                    |
| `make claude N=2`    | Launch a second Claude session                |
| `make codex`         | Launch Codex CLI in tmux                      |
| `make codex N=2`     | Launch a second Codex session                 |

### Development (run on the server after `make ssh`)

| Command              | What it does                                  |
|----------------------|-----------------------------------------------|
| `make dev-run`       | Django runserver on :8000                     |
| `make dev-migrate`   | Run database migrations                       |
| `make dev-test`      | Run tests                                     |
| `make dev-shell`     | Django shell                                  |
| `make up`            | Docker compose up                             |
| `make down`          | Docker compose down                           |
| `make demo`          | Load demo users and jobs                      |

## How It Works

The Makefile auto-detects your environment:

- **gcloud installed** → connects via Google IAP tunnel (admin/owner workflow)
- **no gcloud** → connects via direct SSH with the local generated key

No configuration needed after Terraform has generated the local key and external IP file. The private key itself is intentionally gitignored and must be distributed separately.

To force a specific mode:

```bash
make ssh USE_IAP=0    # force direct SSH
make ssh USE_IAP=1    # force IAP tunnel
```

## For LLMs / Agents

To execute commands on the remote server programmatically:

```bash
# Run a single command
ssh -i terraform/voxvox-ssh-key dev@$(cd terraform && make -s ip) "cd ~/marketplace && git status"

# Run Claude Code non-interactively
ssh -i terraform/voxvox-ssh-key dev@$(cd terraform && make -s ip) "cd ~/marketplace && claude --dangerously-skip-permissions -p 'your prompt here'"

# Check what's running
ssh -i terraform/voxvox-ssh-key dev@$(cd terraform && make -s ip) "docker ps && tmux ls"
```

Claude Code and Codex CLI authentication depends on the server environment; verify access before launching long-running agent work.

## File Layout on Server

```
/home/dev/
├── marketplace/              # git repo (your code)
│   ├── marketplace-py/       # Django project
│   └── ...
├── marketplace-deploy/       # docker compose setup
│   └── docker-compose.yml
├── vm-files/
│   └── update-tools.sh       # daily tool updater
├── Makefile                  # on-server dev commands
└── .voxvox-env               # local environment file (sourced by .bashrc)
```
