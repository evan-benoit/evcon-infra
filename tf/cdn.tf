
# --- Cloud Storage bucket for static site ---
resource "google_storage_bucket" "site" {
  name                        = "${var.project_id}-trophypace-site"
  location                    = "US"
  uniform_bucket_level_access  = true
  force_destroy                = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }

  iam_configuration {
    public_access_prevention = "inherited"
  }
}


# --- Backend bucket for Cloud CDN ---
resource "google_compute_backend_bucket" "cdn_backend" {
  name        = "trophypace-backend"
  bucket_name = google_storage_bucket.site.name
  enable_cdn  = true
}

# --- URL Map for routing ---
resource "google_compute_url_map" "cdn_map" {
  name            = "${var.project_id}-trophypace-map"
  default_service = google_compute_backend_bucket.cdn_backend.id
}

# --- Target HTTP proxy (no SSL) ---
resource "google_compute_target_http_proxy" "cdn_proxy" {
  name    = "trophypace-proxy-http"
  url_map = google_compute_url_map.cdn_map.id
}

# --- Global static IP for the load balancer ---
resource "google_compute_global_address" "cdn_ip" {
  name = "trophypace-ip"
}

# --- Global forwarding rule (port 80 / HTTP) ---
resource "google_compute_global_forwarding_rule" "cdn_rule" {
  name        = "trophypace-http-rule"
  target      = google_compute_target_http_proxy.cdn_proxy.id
  port_range  = "80"
  ip_protocol = "TCP"
  ip_address  = google_compute_global_address.cdn_ip.address
}

# --- Project lookup (for service account binding) ---
data "google_project" "current" {}

# --- IAM binding for LB access ---
resource "google_storage_bucket_iam_member" "lb_access" {
  bucket = google_storage_bucket.site.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"

  # ensure this happens AFTER the LB/backend bucket exists
  depends_on = [
    google_compute_backend_bucket.cdn_backend,
    google_compute_global_forwarding_rule.cdn_rule
  ]
}

output "cdn_ip" {
  description = "Public IP address for the load balancer — open this in a browser"
  value       = google_compute_global_address.cdn_ip.address
}