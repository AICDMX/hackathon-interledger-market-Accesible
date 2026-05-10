# --------------------------------------------------------------------------
# VoxVos Dev Environment — Outputs
# --------------------------------------------------------------------------

locals {
  vm_ip = coalesce(try(google_compute_instance.server.network_interface[0].access_config[0].nat_ip, null), "PENDING")
}

output "external_ip" {
  description = "External IP of the dev VM"
  value       = local.vm_ip
}

output "ssh_command" {
  description = "SSH into the dev VM directly with generated key"
  value       = "ssh -i ${path.module}/voxvox-ssh-key ${var.dev_username}@${local.vm_ip}"
}

output "ssh_command_iap" {
  description = "SSH into the dev VM via IAP tunnel (primary)"
  value       = "gcloud compute ssh voxvox-server --zone=${var.zone} --project=${var.project_id} --tunnel-through-iap"
}

output "tunnel_command" {
  description = "Forward Django dev server to localhost:8000 (via IAP)"
  value       = "gcloud compute ssh voxvox-server --zone=${var.zone} --project=${var.project_id} --tunnel-through-iap -- -NL 8000:localhost:8000"
}

output "tunnel_command_direct" {
  description = "Forward Django dev server to localhost:8000 (direct SSH)"
  value       = "ssh -i ${path.module}/voxvox-ssh-key -NL 8000:localhost:8000 ${var.dev_username}@${local.vm_ip}"
}

output "startup_log_command" {
  description = "Command to check startup script progress"
  value       = "gcloud compute ssh voxvox-server --zone=${var.zone} --project=${var.project_id} --tunnel-through-iap -- sudo tail -f /var/log/voxvox-startup.log"
}

output "ssh_private_key" {
  description = "Private SSH key (save to a file, chmod 600)"
  value       = tls_private_key.ssh.private_key_openssh
  sensitive   = true
}

output "tfstate_bucket" {
  description = "GCS bucket for Terraform remote state"
  value       = google_storage_bucket.tfstate.name
}

output "dev_info" {
  description = "Development environment paths and useful info"
  value       = <<-EOT
    IAP SSH:       make ssh       (gcloud auto-detected)
    Direct SSH:    ssh -i voxvox-ssh-key ${var.dev_username}@${local.vm_ip}
    Project repo:  ~/marketplace
    Django:        make dev-run   (runserver on :8000)
    Docker:        make up        (docker compose up)
    Claude:        make claude    (Claude Code in tmux)
    Codex:         make codex     (Codex CLI in tmux)
    Web UI:        make tunnel    (then open http://localhost:8000)
  EOT
}
