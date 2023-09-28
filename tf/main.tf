resource "random_id" "bucket_prefix" {
  byte_length = 8
}

resource "google_storage_bucket" "tfstate" {
  project       = var.project_id
  name          = "${random_id.bucket_prefix.hex}-bucket-tfstate"
  force_destroy = false
  location      = "US"
  storage_class = "STANDARD"
  versioning {
    enabled = true
  }
}



resource "google_project_service" "service-container" {
  project = var.project_id
  service = "container.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}


resource "google_project_service" "service-artifactregistry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}

resource "google_project_service" "service-dns" {
  project = var.project_id
  service = "dns.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}

resource "google_project_service" "service-firebase" {
  project = var.project_id
  service = "firebase.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}


resource "google_project_service" "service-oslogin" {
  project = var.project_id
  service = "oslogin.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}



resource "google_artifact_registry_repository" "my-repository" {
  location      = "us-east1"
  project       = var.project_id
  repository_id = "my-repository"
  description   = "Evan's docker repository"
  format        = "DOCKER"
}


resource "google_service_account" "service_account" {
  project      = var.project_id
  account_id   = "service-account-id"
  display_name = "Service Account"
}

resource "google_service_account" "circleci_service_account" {
  project      = var.project_id
  account_id   = "circleci-service-account"
  display_name = "CircleCIService Account"
}



# add a service account that can write to google artifact registry
resource "google_project_iam_member" "circleci_service_account_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.circleci_service_account.email}"
}
# Also give that service account cluster admin access
resource "google_project_iam_member" "circleci_service_account_cluster_admin" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.circleci_service_account.email}"
}
