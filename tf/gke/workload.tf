
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
  backend "gcs" {
    bucket  = "85025690a453809d-bucket-tfstate"
    prefix  = "terraform/gke-state"
  }

}
provider "kubernetes" {
  config_path = "~/.kube/config"
  config_context = "gke_evcon-app_us-east1_evcon-app-gke"
}

resource "kubernetes_deployment" "webserver" {
  metadata {
    name      = "webserver"
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
          image = "us-east1-docker.pkg.dev/evcon-app/my-repository/webserver:latest"
          name  = "webserver-container"
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


