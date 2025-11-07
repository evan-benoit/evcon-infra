# Cloud Storage bucket
resource "google_storage_bucket" "site" {
  name                        = "${var.project_id}-site"
  location                    = "us-east1"
  uniform_bucket_level_access = true
  storage_class               = "STANDARD"
  // delete bucket and contents on destroy.
  force_destroy = true
  // Assign specialty files
  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }
}

resource "null_resource" "upload_image" {
  provisioner "local-exec" {
    command = "gcloud storage cp gs://gcp-external-http-lb-with-bucket/three-cats.jpg gs://${google_storage_bucket.site.name}/never-fetch/ --recursive"
  }
}

# make bucket public
resource "google_storage_bucket_iam_member" "default" {
  bucket = google_storage_bucket.site.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# reserve IP address
resource "google_compute_global_address" "default" {
  name = "example-ip"
}

# backend bucket with CDN policy with default ttl settings
resource "google_compute_backend_bucket" "default" {
  name        = "backend-bucket"
  description = "Contains beautiful images"
  bucket_name = google_storage_bucket.site.name
  enable_cdn  = true
  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    client_ttl        = 3600
    default_ttl       = 3600
    max_ttl           = 86400
    negative_caching  = true
    serve_while_stale = 86400
  }
}

# url map
resource "google_compute_url_map" "default" {
  name            = "http-lb"
  default_service = google_compute_backend_bucket.default.id
}

# http proxy
resource "google_compute_target_http_proxy" "default" {
  name    = "http-lb-proxy"
  url_map = google_compute_url_map.default.id
}

# forwarding rule
resource "google_compute_global_forwarding_rule" "default" {
  name                  = "http-lb-forwarding-rule"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
  port_range            = "80"
  target                = google_compute_target_http_proxy.default.id
  ip_address            = google_compute_global_address.default.id
}

output "lb_ip" {
  description = "Public IP address for the load balancer"
  value       = google_compute_global_address.default.address
}