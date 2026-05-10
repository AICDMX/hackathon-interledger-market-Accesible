# --------------------------------------------------------------------------
# VoxVos Dev Environment — Main Configuration
# --------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"

  backend "gcs" {}

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# -- GCP Project --------------------------------------------------------------

resource "google_project" "voxvox" {
  name            = var.project_name
  project_id      = var.project_id
  org_id          = var.org_id
  billing_account = var.billing_account

  deletion_policy = "DELETE"
}

# -- Enable APIs ---------------------------------------------------------------

resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com",
  ])

  project            = google_project.voxvox.project_id
  service            = each.value
  disable_on_destroy = false

  depends_on = [google_project.voxvox]
}

# -- Service Account -----------------------------------------------------------

resource "google_service_account" "vm" {
  account_id   = "voxvox-vm-sa"
  display_name = "VoxVos Dev VM Service Account"
  project      = google_project.voxvox.project_id

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "vm_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])

  project = google_project.voxvox.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.vm.email}"
}

# -- GCS Bucket for Terraform State (bootstrap) --------------------------------

resource "google_storage_bucket" "tfstate" {
  name          = "${var.project_id}-terraform-state"
  project       = google_project.voxvox.project_id
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.apis]
}
