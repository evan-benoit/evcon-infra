#GCS bucket to store the source code
resource "google_storage_bucket" "function_bucket" {
    name     = "${var.project_id}-function"
    location = var.region
}

# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "source_getLeagueSeason" {
    type        = "zip"
    source_dir  = "../src/populateLeagueSeason"
    output_path = "./tmp/populateLeagueSeason.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "zip_getLeagueSeason" {
    source       = data.archive_file.source_getLeagueSeason.output_path
    content_type = "application/zip"

    # Append to the MD5 checksum of the files's content
    # to force the zip to be updated as soon as a change occurs
    name         = "src-${data.archive_file.source_getLeagueSeason.output_md5}.zip"
    bucket       = google_storage_bucket.function_bucket.name
}

# Create the Cloud function triggered by a `Finalize` event on the bucket
resource "google_cloudfunctions_function" "populateTodaysLeagues" {
    name                  = "populateTodaysLeagues"
    runtime               = "python39"
    trigger_http          = true

    # Get the source code of the cloud function as a Zip compression
    source_archive_bucket = google_storage_bucket.function_bucket.name
    source_archive_object = google_storage_bucket_object.zip_getLeagueSeason.name

    # Must match the function name in the cloud function `main.py` source code
    entry_point           = "populateTodaysLeagues"
}


resource "google_service_account" "cloudfunction_service_account" {
  account_id           = "cloudfunction-service-account"
  display_name         = "Cloud Function service account"
  description          = "Service Account for running cloud functions"
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.populateTodaysLeagues.project
  region         = google_cloudfunctions_function.populateTodaysLeagues.region
  cloud_function = google_cloudfunctions_function.populateTodaysLeagues.name

  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.cloudfunction_service_account.email}"
}


resource "google_cloud_scheduler_job" "populateTodaysLeagues_job" {
  name             = "populateTodaysLeagues_job"
  description      = "Run populateTodaysLeagues hourly"
  schedule         = "0 * * * *"
  time_zone        = "GMT"
  attempt_deadline = "320s"

  retry_config {
    min_backoff_duration = "120s"
    max_retry_duration = "3600s"
    max_doublings = 4
  }

  http_target {
    http_method = "POST"
    uri         = "https://us-east1-evcon-app.cloudfunctions.net/populateTodaysLeagues"
    oidc_token {
        service_account_email = "${google_service_account.cloudfunction_service_account.email}"
        audience = "https://us-east1-evcon-app.cloudfunctions.net/populateTodaysLeagues"
    }
  }

}