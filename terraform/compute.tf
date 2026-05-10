# --------------------------------------------------------------------------
# VoxVos Dev Environment — Compute (GCE Instance)
# --------------------------------------------------------------------------

# -- SSH key pair (auto-generated) -------------------------------------------

resource "tls_private_key" "ssh" {
  algorithm = "ED25519"
}

resource "local_file" "ssh_private_key" {
  content         = tls_private_key.ssh.private_key_openssh
  filename        = "${path.module}/voxvox-ssh-key"
  file_permission = "0600"
}

resource "local_file" "ssh_public_key" {
  content  = tls_private_key.ssh.public_key_openssh
  filename = "${path.module}/voxvox-ssh-key.pub"
}

# -- GCE Instance -------------------------------------------------------------

resource "google_compute_instance" "server" {
  name         = "voxvox-server"
  machine_type = var.machine_type
  zone         = var.zone
  project      = google_project.voxvox.project_id

  tags = ["voxvox-server"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.boot_disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {
      # Ephemeral external IP for direct SSH access
    }
  }

  service_account {
    email  = google_service_account.vm.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    "vm-makefile"     = file("${path.module}/templates/vm-Makefile")
    "update-tools-sh" = file("${path.module}/vm-files/update-tools.sh")
    "docker-compose"  = file("${path.module}/templates/docker-compose.yml")
    "ssh-keys"        = "${var.dev_username}:${tls_private_key.ssh.public_key_openssh}"
  }

  metadata_startup_script = templatefile("${path.module}/templates/startup.sh.tpl", {
    dev_username            = var.dev_username
    repo_url                = var.repo_url
    git_branch              = var.git_branch
    anthropic_api_key       = var.anthropic_api_key
    openai_api_key          = var.openai_api_key
    cloudflare_tunnel_token = var.cloudflare_tunnel_token
  })

  allow_stopping_for_update = true

  lifecycle {
    ignore_changes = [metadata, metadata_startup_script]
  }

  depends_on = [
    google_project_iam_member.vm_roles,
  ]
}
