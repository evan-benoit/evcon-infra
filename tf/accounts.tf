# Create the service account
resource "google_service_account" "cicd" {
  account_id   = "github-cicd"
  display_name = "GitHub CI/CD Service Account"
  project      = var.project_id
}

# Grant Artifact Registry push access
resource "google_project_iam_member" "cicd_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

# Grant GKE deployment admin
resource "google_project_iam_member" "cicd_gke_admin" {
  project = var.project_id
  role    = "roles/container.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

# (Optional, but common) Allow impersonation if you need Workload Identity
resource "google_project_iam_member" "cicd_iam_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}