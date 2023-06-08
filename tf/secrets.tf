resource "google_project_service" "service-secretmanager" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = true
}


# Create a secret for local-admin-password
resource "google_secret_manager_secret" "football-api-key" {
  
  secret_id = "football-api-key"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_iam_binding" "football-api-key-binding" {
  project = google_secret_manager_secret.football-api-key.project
  secret_id = google_secret_manager_secret.football-api-key.secret_id
  role = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:${google_service_account.cloudfunction_service_account.email}",
    "user:evan.m.benoit@gmail.com"
  ]
}