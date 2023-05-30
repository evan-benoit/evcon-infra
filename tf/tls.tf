resource "google_compute_managed_ssl_certificate" "lb_default" {
  name     = "evcon-ssl-cert"

  managed {
    domains = [google_dns_managed_zone.default.dns_name]
  }
}


