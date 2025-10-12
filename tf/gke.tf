variable "gke_username" {
  default     = ""
  description = "gke username"
}

variable "gke_password" {
  default     = ""
  description = "gke password"
}

variable "gke_num_nodes" {
  default     = 1
  description = "number of gke nodes"
}




resource "google_container_cluster" "primary" {
  name       = "${var.project_id}-gke"
  location = var.region

  enable_autopilot = true
}