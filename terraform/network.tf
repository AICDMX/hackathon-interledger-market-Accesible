# --------------------------------------------------------------------------
# VoxVos Dev Environment — Networking
# --------------------------------------------------------------------------

# -- VPC ----------------------------------------------------------------------

resource "google_compute_network" "vpc" {
  name                    = "voxvox-vpc"
  auto_create_subnetworks = false
  project                 = google_project.voxvox.project_id

  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "voxvox-subnet"
  ip_cidr_range            = "10.0.3.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

# -- Cloud NAT (outbound internet for VM without external IP) -----------------

resource "google_compute_router" "router" {
  name    = "voxvox-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "voxvox-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = false
    filter = "ALL"
  }
}

# -- Firewall Rules -----------------------------------------------------------

resource "google_compute_firewall" "allow_ssh" {
  name    = "voxvox-allow-ssh"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # Direct SSH access + IAP tunnel range
  source_ranges = distinct(concat(var.ssh_allow_cidrs, ["35.235.240.0/20"]))
  target_tags   = ["voxvox-server"]
}

resource "google_compute_firewall" "allow_dev_ports" {
  name    = "voxvox-allow-dev-ports"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  # Open dev ports to same CIDRs as SSH + IAP range
  source_ranges = distinct(concat(var.ssh_allow_cidrs, ["35.235.240.0/20"]))
  target_tags   = ["voxvox-server"]
}

resource "google_compute_firewall" "allow_internal" {
  name    = "voxvox-allow-internal"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.3.0/24"]
}
