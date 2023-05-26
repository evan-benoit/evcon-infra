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
resource "google_cloudfunctions_function" "populateLeagueSeason" {
    name                  = "populateLeagueSeason"
    runtime               = "python39"
    trigger_http          = true

    # Get the source code of the cloud function as a Zip compression
    source_archive_bucket = google_storage_bucket.function_bucket.name
    source_archive_object = google_storage_bucket_object.zip_getLeagueSeason.name

    # Must match the function name in the cloud function `main.py` source code
    entry_point           = "populateLeagueSeason"
}