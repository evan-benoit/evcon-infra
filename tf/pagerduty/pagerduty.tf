
terraform {
  required_providers {
    pagerduty = {
      source  = "pagerduty/pagerduty"
      version = "2.2.1"
    }
  }
}

provider "pagerduty" {
    token = "u+Kxq1ZvddkPSXejGysw"
}


# Create a PagerDuty team
resource "pagerduty_team" "engineering" {
  name        = "Engineering"
  description = "All engineering"
}

# Create a PagerDuty user
resource "pagerduty_user" "evan_benoit" {
  name  = "Evan Benoit"
  email = "evan.benoit+evcon@expel.io"
}

# Create a PagerDuty user
resource "pagerduty_user" "johnny_comms" {
  name  = "Johnny Comms"
  email = "evan.benoit+evcon-comms@expel.io"
}


# Create a team membership
resource "pagerduty_team_membership" "evan_benoit_engineering" {
  user_id = pagerduty_user.evan_benoit.id
  team_id = pagerduty_team.engineering.id
}

# Create a team membership
resource "pagerduty_team_membership" "johnny_comms_engineering" {
  user_id = pagerduty_user.johnny_comms.id
  team_id = pagerduty_team.engineering.id
}


resource "pagerduty_escalation_policy" "engineering" {
  name      = "Engineering Escalation Policy"
  num_loops = 2
  teams     = [pagerduty_team.engineering.id]
  

  rule {
    escalation_delay_in_minutes = 10

    target {
      type = "user_reference"
      id   = pagerduty_user.evan_benoit.id
    }
  }
}

resource "pagerduty_service" "front_end" {
  name                    = "Frontend"
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 600
  escalation_policy       = pagerduty_escalation_policy.engineering.id
  alert_creation          = "create_alerts_and_incidents"
}


resource "pagerduty_service" "firestore" {
  name                    = "Firestore"
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 600
  escalation_policy       = pagerduty_escalation_policy.engineering.id
  alert_creation          = "create_alerts_and_incidents"
}

resource "pagerduty_service" "loader" {
  name                    = "Loader"
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 600
  escalation_policy       = pagerduty_escalation_policy.engineering.id
  alert_creation          = "create_alerts_and_incidents"
}


resource "pagerduty_service_dependency" "front_end_firestore" {
    dependency {
        dependent_service {
            id = pagerduty_service.front_end.id
            type = "service"
        }
        supporting_service {
            id = pagerduty_service.firestore.id
            type = "service"
        }
    }
}


resource "pagerduty_service_dependency" "loader_firestore" {
    dependency {
        dependent_service {
            id = pagerduty_service.loader.id
            type = "service"
        }
        supporting_service {
            id = pagerduty_service.firestore.id
            type = "service"
        }
    }
}