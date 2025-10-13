provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.kube_context
}

variable "kube_context" {}
variable "project_id" {}
variable "git_sha" { default = "latest" }
variable "load_balancer_ip" { default = null }

resource "kubernetes_deployment" "webserver" {
  metadata {
    name = "webserver"   
  }

  spec {
    replicas = 2
    selector {
      match_labels = {
        app = "webserver"
      }
    }
    template {
      metadata {
        labels = {
          app = "webserver"
        }
      }
      spec {
        container {
          name  = "webserver-container"
          image = "us-east1-docker.pkg.dev/${var.project_id}/my-repository/webserver:${var.git_sha}"
          port {
            container_port = 80
          }
          resources {
            limits = {
              cpu    = "250m"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "webserver" {
  metadata {
    name = "webserver"
  }

  spec {
    selector = {
      app = "webserver"
    }
    port {
      port        = 80
      target_port = 80
    }

    type = "LoadBalancer"
    load_balancer_ip = var.load_balancer_ip
  }
}