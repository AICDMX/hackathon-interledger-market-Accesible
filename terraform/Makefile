.PHONY: help init plan apply destroy ssh tmux tunnel logs status output fmt validate clean claude codex update-tools update-claude update-codex revert-claude revert-codex update-log push-makefile push-compose push-update-script push-all start stop ip

# --- Auto-detect transport ----------------------------------------------------
# If gcloud is installed → IAP tunnel (owner/admin workflow)
# If gcloud is missing  → direct SSH with key (shared package workflow)
# Override: make ssh USE_IAP=1  or  make ssh USE_IAP=0
# ------------------------------------------------------------------------------

HAS_GCLOUD := $(shell command -v gcloud >/dev/null 2>&1 && echo 1 || echo 0)
USE_IAP    ?= $(HAS_GCLOUD)

# Shared settings
DEV_USER   ?= dev
SSH_KEY    ?= $(CURDIR)/voxvox-ssh-key
VM_IP      ?= $(or $(shell cat $(CURDIR)/.vm-ip 2>/dev/null),$(shell terraform output -raw external_ip 2>/dev/null))
VM_NAME    := voxvox-server
_UPDATE_SCRIPT = /home/$(DEV_USER)/vm-files/update-tools.sh

# gcloud settings (only evaluated when USE_IAP=1)
ifeq ($(USE_IAP),1)
  ZONE    := $(shell grep '^zone ' terraform.tfvars 2>/dev/null | sed 's/.*= *"\(.*\)"/\1/')
  PROJECT := $(shell grep '^project_id ' terraform.tfvars 2>/dev/null | sed 's/.*= *"\(.*\)"/\1/')
  ZONE    := $(or $(ZONE),southamerica-east1-a)
  PROJECT := $(or $(PROJECT),voxvox-dev)
  export CLOUDSDK_PYTHON_SITEPACKAGES := 1
endif

# --- Transport abstraction ----------------------------------------------------

ifeq ($(USE_IAP),1)
  _SSH      = gcloud compute ssh $(VM_NAME) --zone=$(ZONE) --project=$(PROJECT) --tunnel-through-iap --
  _SSH_CMD  = gcloud compute ssh $(VM_NAME) --zone=$(ZONE) --project=$(PROJECT) --tunnel-through-iap --command=
  _SCP      = gcloud compute scp --zone=$(ZONE) --project=$(PROJECT) --tunnel-through-iap
  _SCP_DST  = $(VM_NAME):
else
  _SSH      = ssh -i $(SSH_KEY) -t $(DEV_USER)@$(VM_IP)
  _SSH_CMD  = ssh -i $(SSH_KEY) $(DEV_USER)@$(VM_IP)
  _SCP      = scp -i $(SSH_KEY)
  _SCP_DST  = $(DEV_USER)@$(VM_IP):
endif

# --- Help ---------------------------------------------------------------------

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  mode: $$([ '$(USE_IAP)' = '1' ] && echo 'IAP tunnel (gcloud detected)' || echo 'direct SSH → $(VM_IP)')"

# --- Terraform lifecycle ---

init: ## Initialize Terraform with GCS backend
	terraform init -backend-config="bucket=$(PROJECT)-terraform-state" -backend-config="prefix=terraform/state"

plan: ## Preview infrastructure changes
	terraform plan

apply: ## Create or update the dev VM
	terraform apply

destroy: ## Tear down all dev infrastructure
	terraform destroy

output: ## Show Terraform outputs
	terraform output

# --- Terraform utilities ---

fmt: ## Format .tf files
	terraform fmt -recursive

validate: ## Validate Terraform configuration
	terraform validate

# --- Remote VM access ---

ssh: ## SSH into the dev VM
ifeq ($(USE_IAP),1)
	-$(_SSH) -tt "exec sudo -iu $(DEV_USER) bash"
else
	-$(_SSH) bash
endif

tmux: ## Attach to tmux session chooser on the VM
ifeq ($(USE_IAP),1)
	-$(_SSH) -tt "exec sudo -iu $(DEV_USER) bash -c 'tmux attach \\; choose-tree || tmux new-session \\; choose-tree'"
else
	-$(_SSH) "tmux attach \\; choose-tree || tmux new-session \\; choose-tree"
endif

tunnel: ## Forward Django dev server to localhost:8000
	@echo "Forwarding localhost:8000 -> Django dev server"
	@echo "Press Ctrl+C to stop"
ifeq ($(USE_IAP),1)
	-gcloud compute ssh $(VM_NAME) --zone=$(ZONE) --project=$(PROJECT) --tunnel-through-iap -- -NL 8000:localhost:8000
else
	-ssh -i $(SSH_KEY) -NL 8000:localhost:8000 $(DEV_USER)@$(VM_IP)
endif

logs: ## Tail the startup script log on the VM
	$(_SSH_CMD) 'sudo tail -f /var/log/voxvox-startup.log'

status: ## Check VM status and running containers
	@echo "--- VM instance ---"
ifeq ($(USE_IAP),1)
	gcloud compute instances describe $(VM_NAME) --zone=$(ZONE) --project=$(PROJECT) \
		--format='table(name, status, networkInterfaces[0].accessConfigs[0].natIP, machineType.basename())' 2>/dev/null || echo "  VM not found (run 'make apply' first)"
else
	@echo "  IP: $(VM_IP)"
endif
	@echo ""
	@echo "--- Docker containers ---"
	@$(_SSH_CMD) 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"' 2>/dev/null || echo "  Could not reach VM"

# --- AI coding tools (use N=1, N=2, etc. for multiple sessions) ---

N :=
_CLAUDE_SESSION = claude$(if $(N),-$(N))
_CODEX_SESSION  = codex$(if $(N),-$(N))

claude: ## Launch Claude Code (N=1 for extra session)
ifeq ($(USE_IAP),1)
	-$(_SSH) -tt "exec sudo -iu $(DEV_USER) bash -lc 'tmux new-session -As \"$(_CLAUDE_SESSION)\" -c /home/$(DEV_USER)/marketplace \"claude --dangerously-skip-permissions\"'"
else
	-$(_SSH) "tmux new-session -As \"$(_CLAUDE_SESSION)\" -c /home/$(DEV_USER)/marketplace 'claude --dangerously-skip-permissions'"
endif

codex: ## Launch Codex CLI (N=1 for extra session)
ifeq ($(USE_IAP),1)
	-$(_SSH) -tt "exec sudo -iu $(DEV_USER) bash -lc 'tmux new-session -As \"$(_CODEX_SESSION)\" -c /home/$(DEV_USER)/marketplace \"codex --dangerously-bypass-approvals-and-sandbox\"'"
else
	-$(_SSH) "tmux new-session -As \"$(_CODEX_SESSION)\" -c /home/$(DEV_USER)/marketplace 'codex --dangerously-bypass-approvals-and-sandbox'"
endif

# --- Tool updates (Claude Code + Codex CLI) ---

VER :=

update-tools: ## Update both Claude Code and Codex CLI on the VM
	$(_SSH_CMD) 'sudo $(_UPDATE_SCRIPT) all'

update-claude: ## Update only Claude Code on the VM
	$(_SSH_CMD) 'sudo $(_UPDATE_SCRIPT) claude'

update-codex: ## Update only Codex CLI on the VM
	$(_SSH_CMD) 'sudo $(_UPDATE_SCRIPT) codex'

revert-claude: ## Revert Claude to a specific version (VER=x.y.z)
	@[ -n "$(VER)" ] || { echo "Usage: make revert-claude VER=x.y.z"; exit 1; }
	$(_SSH_CMD) 'sudo $(_UPDATE_SCRIPT) claude --revert $(VER)'

revert-codex: ## Revert Codex to a specific version (VER=x.y.z)
	@[ -n "$(VER)" ] || { echo "Usage: make revert-codex VER=x.y.z"; exit 1; }
	$(_SSH_CMD) 'sudo $(_UPDATE_SCRIPT) codex --revert $(VER)'

update-log: ## Show tool update history from the VM
	$(_SSH_CMD) 'sudo $(_UPDATE_SCRIPT) all --log'

# --- Push files to VM ---

push-makefile: ## Push templates/vm-Makefile to the VM
	$(_SCP) templates/vm-Makefile $(_SCP_DST)/tmp/vm-Makefile
	$(_SSH_CMD) 'sudo mv /tmp/vm-Makefile /home/$(DEV_USER)/Makefile && sudo chown $(DEV_USER):$(DEV_USER) /home/$(DEV_USER)/Makefile'

push-compose: ## Push docker-compose.yml to the VM and recreate
	$(_SCP) templates/docker-compose.yml $(_SCP_DST)/tmp/docker-compose.yml
	$(_SSH_CMD) 'sudo mv /tmp/docker-compose.yml /home/$(DEV_USER)/marketplace-deploy/docker-compose.yml && sudo chown $(DEV_USER):$(DEV_USER) /home/$(DEV_USER)/marketplace-deploy/docker-compose.yml && sudo -u $(DEV_USER) bash -c "cd /home/$(DEV_USER)/marketplace-deploy && docker compose up -d --force-recreate web"'

push-update-script: ## Push update-tools.sh to the VM
	$(_SCP) vm-files/update-tools.sh $(_SCP_DST)/tmp/update-tools.sh
	$(_SSH_CMD) 'sudo mkdir -p /home/$(DEV_USER)/vm-files && sudo mv /tmp/update-tools.sh /home/$(DEV_USER)/vm-files/update-tools.sh && sudo chmod +x /home/$(DEV_USER)/vm-files/update-tools.sh && sudo chown -R $(DEV_USER):$(DEV_USER) /home/$(DEV_USER)/vm-files'

push-all: push-makefile push-compose push-update-script ## Push all files to VM

# --- Lifecycle helpers ---

ip: ## Show the VM's external IP
	@echo "$(VM_IP)"

start: ## Start a stopped VM
	gcloud compute instances start $(VM_NAME) --zone=$(ZONE) --project=$(PROJECT)

stop: ## Stop the VM (saves cost, keeps disk)
	gcloud compute instances stop $(VM_NAME) --zone=$(ZONE) --project=$(PROJECT)

# --- Cleanup ---

clean: ## Remove local Terraform state and cache
	rm -rf .terraform .terraform.lock.hcl
	@echo "Run 'make init' to re-initialize"
