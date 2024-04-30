
resource "google_storage_bucket" "evcon-summaries" {
    name     = "evcon-summaries"
    location = "us-east1"
    storage_class = "STANDARD"
    force_destroy = true

    lifecycle_rule {
        condition {
        age = 10
        }
        action {
        type = "Delete"
        }
    }
}