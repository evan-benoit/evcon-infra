resource "google_certificate_manager_certificate" "default" {
  name        = "trophypace-cert2"
  description = "The default SSL cert"
  scope       = "DEFAULT"
  location    = "global"
  managed {
    domains = [
      google_certificate_manager_dns_authorization.instance.domain,
      google_certificate_manager_dns_authorization.instance2.domain,
      ]
    dns_authorizations = [
      google_certificate_manager_dns_authorization.instance.id,
      google_certificate_manager_dns_authorization.instance2.id,
      ]
  }
}


resource "google_certificate_manager_dns_authorization" "instance" {
  name        = "dns-auth"
  description = "The default dnss"
  domain      = "trophypace.com"
}

resource "google_certificate_manager_dns_authorization" "instance2" {
  name        = "dns-auth2"
  description = "The default dnss"
  domain      = "www.trophypace.com"
}


resource "google_compute_address" "ip_address" {
  name = "trophypace2"
}