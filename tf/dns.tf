# to create a DNS zone
resource "google_dns_managed_zone" "default" {
  name          = "zone-trophypace"
  dns_name      = "trophypace.com."
  description   = "TrophyPace"
  force_destroy = "true"
}

# to register web-server's ip address in DNS
resource "google_dns_record_set" "default" {
  name         = google_dns_managed_zone.default.dns_name
  managed_zone = google_dns_managed_zone.default.name
  type         = "A"
  ttl          = 300
  rrdatas = [
    "34.23.73.154"
  ]
}

resource "google_dns_record_set" "cname" {
  name         = "www.${google_dns_managed_zone.default.dns_name}"
  managed_zone = google_dns_managed_zone.default.name
  type         = "CNAME"
  ttl          = 300
  rrdatas      = ["trophypace.com."]
}