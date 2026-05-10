# --------------------------------------------------------------------------
# VoxVos Dev Environment — Terraform Variables
# --------------------------------------------------------------------------

# -- GCP Project ---------------------------------------------------------------

variable "project_name" {
  description = "Display name for the GCP project"
  type        = string
  default     = "voxvox"
}

variable "project_id" {
  description = "Globally unique GCP project ID"
  type        = string
}

variable "org_id" {
  description = "GCP organization ID"
  type        = string
  default     = "564163886903"
}

variable "billing_account" {
  description = "GCP billing account ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "southamerica-east1"
}

variable "zone" {
  description = "GCP zone for compute resources"
  type        = string
  default     = "southamerica-east1-a"
}

# -- Compute -------------------------------------------------------------------

variable "machine_type" {
  description = "GCE machine type"
  type        = string
  default     = "e2-standard-4"
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 40
}

# -- AI Tools ------------------------------------------------------------------

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude Code"
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for Codex CLI"
  type        = string
  default     = ""
  sensitive   = true
}

# -- Cloudflare Tunnel ---------------------------------------------------------

variable "cloudflare_tunnel_token" {
  description = "Cloudflare Tunnel connector token (from Zero Trust dashboard)"
  type        = string
  default     = ""
  sensitive   = true
}

# -- Git -----------------------------------------------------------------------

variable "repo_url" {
  description = "Git repo URL for the marketplace project"
  type        = string
  default     = "https://github.com/AICDMX/hackathon-interledger-market-Accesible.git"
}

variable "git_branch" {
  description = "Git branch to clone"
  type        = string
  default     = "main"
}

# -- Dev User ------------------------------------------------------------------

variable "dev_username" {
  description = "Linux username for the development user"
  type        = string
  default     = "dev"
}

# -- SSH Access ----------------------------------------------------------------

variable "ssh_allow_cidrs" {
  description = "CIDRs allowed to SSH directly (default: anywhere)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
