# Copilot Instructions for evcon-infra

## Project Overview
**evcon-infra** is a GCP infrastructure-as-code (IaC) project that powers **trophypace.com**, a Premier League standings visualization platform inspired by pennant-race.com. The project consists of:

1. **Terraform configuration** (`/tf`) - GCP resources including GKE cluster, Cloud Functions, Firestore, Cloud Storage, and related services
2. **Python Cloud Functions** (`/src`) - Microservices that fetch league data and serve it to the frontend
3. **Certification** (`/cert`) - TLS/SSL configuration for managed certificates and ingress

## Architecture & Data Flow

### Cloud Functions (Python)
Four main HTTP-triggered Cloud Functions deployed via Terraform:

- **`populateLeagueSeason`** (`src/populateLeagueSeason/`): Main data aggregator
  - Fetches league standings/fixtures from external API (v3.football.api-sports.io)
  - Loads secrets (API key) from Google Secret Manager
  - Writes processed data to Firestore in structure: `countries/{code}/leagues/{id}/seasons/{year}`
  - Calls `buildIndex()` to generate the index document used by frontend
  - Triggered periodically to keep standings current

- **`getIndex`** (`src/getIndex/`): Frontend data endpoint
  - Returns latest index from `Firestore/index/latest` as JSON
  - Implements CORS for requests from trophypace.com and localhost:1234
  - Structured logging via JSON to Cloud Logging

- **`getSeason`** (`src/getSeason/`): Season data retrieval
  - Query params: `countryCode` (2-letter), `leagueID` (int), `season` (year)
  - Returns specific season standings from Firestore
  - CORS-enabled

- **`betterHalf`** (`src/betterHalf/`): Seasonal trend analyzer
  - Compares first-half vs second-half performance for teams

### Data Storage
**Firestore** (NoSQL document database):
- Root-level collections: `countries`, `index`
- Nested structure: `countries/{code}/leagues/{id}/seasons/{year}/` contains fixture data
- `index/latest` document is frontend's primary data source

**Cloud Storage**:
- Terraform state bucket (versioned)
- Function source code bucket (auto-zipped during deployment)

### External Dependencies
- **football.api-sports.io** - Sports data provider (API key stored in Secret Manager)
- **Google Cloud Libraries**: firestore, secretmanager, functions-framework

## Deployment & Environments

### Terraform Workspaces
Two distinct environments managed via Terraform workspaces:
- **`dev` workspace** - Uses `dev.tfvars` variables
- **`default` workspace** (prod) - Uses `prod.tfvars` variables

### Deployment Commands (via Makefile)
```bash
make dev         # Deploy to dev workspace with dev.tfvars
make prod        # Deploy to default workspace with prod.tfvars
make dev-destroy # Destroy dev resources
make prod-destroy # Destroy prod resources
```

Each target selects/creates the workspace, then runs `terraform apply -var-file=<env>.tfvars`.

### Cloud Function Deployment Pattern
- Terraform archives source code as zip from respective `/src/<function>` directory
- Stores zip in Cloud Storage bucket with MD5-based naming (triggers update on code change)
- Deploys with `entry_point` matching the function name in `main.py`
- Sets `PROJECT_ID` environment variable at deployment time
- Functions use service account `cloudfunction_service_account` with Secret Manager access

## Key Development Patterns

### Python Cloud Function Structure
All Cloud Functions follow this pattern (see `getIndex/main.py` as reference):

```python
import functions_framework
import os
from google.cloud import firestore

project_id = os.environ["PROJECT_ID"]
db = firestore.Client(project=project_id)

@functions_framework.http
def functionName(request):
    # CORS preflight handling
    if request.method == "OPTIONS":
        return ("", 204, {headers...})
    
    # JSON logging for Cloud Logging
    log_json("INFO", "message", key=value)
    
    # Core logic
    try:
        # return (body, status_code, headers)
    except Exception as e:
        log_json("ERROR", "Exception message", error=str(e), traceback=traceback.format_exc())
```

### Logging Convention
Use structured JSON logging for Cloud Logging parsing:
```python
entry = {
    "severity": level,      # "INFO", "ERROR", etc.
    "message": message,
    **kwargs                # Additional context
}
print(json.dumps(entry))    # stdout → Cloud Logging
```

### CORS Configuration
Allowed origins currently hardcoded in functions (work in progress):
- `https://trophypace.com`
- `http://trophypace.com`
- `http://localhost:1234` (development)

Update `ALLOWED_ORIGINS` set in each function when adding new frontend domains. Future: move to environment variables/Terraform configuration for better multi-environment management.

### Secret Management
- Secrets stored in Google Secret Manager
- Accessed via `secretmanager.SecretManagerServiceClient()`
- Service account must have `roles/secretmanager.secretAccessor` binding (defined in `secrets.tf`)
- Example: Football API key accessed as `projects/{project_id}/secrets/football-api-key/versions/latest`

### Firestore Best Practices Observed
- Service accounts authenticated via Application Default Credentials (`google.auth.default()`)
- Document references used for reads: `db.document("path/to/doc").get().to_dict()`
- Batch operations for efficiency in populateLeagueSeason
- PROJECT_ID from environment variable, fallback to hardcoded default in helper modules

## Terraform Structure & Variables

### Key Configuration Files
- `main.tf` - Core project setup, state bucket, API enablement
- `versions.tf` - Terraform/provider version constraints (Terraform ~1.13.0, Google ~7.6)
- `cloud_function.tf` - Cloud Function definitions with source zipping
- `secrets.tf` - Secret Manager resources and IAM bindings
- `gke.tf` - GKE cluster (autopilot enabled)
- `vpc.tf`, `dns.tf`, `cdn.tf` - Network/DNS/CDN resources
- `accounts.tf` - Service account definitions and roles
- `gke.tf` - GKE Autopilot cluster (enabled for future containerized services)
- `pagerduty/pagerduty.tf` - PagerDuty integration for alerting

### Environment-Specific Variables
- `dev.tfvars` - Development environment (lower resource counts, dev domains)
- `prod.tfvars` - Production environment (higher resource counts, prod domains)
- Both define: `project_id`, `region`, and environment-specific settings

### Common Variables
- `project_id` - GCP project ID
- `region` - GCP region (default in variables.tf)

## Testing & Validation

### Local Development Setup
Local development works against a dev GCP project (`dev.tfvars` environment). No local Firestore emulation required—functions interact with live dev Firestore.

### Cloud Function Testing
Cloud Functions can be tested against deployed dev functions using curl. Example from `betterHalf/test.sh`:
```bash
curl -m 70 -X POST "https://<region>-<project>.cloudfunctions.net/<function>?<params>"
  -H "Content-Type: application/json" \
  -d '{}'
```

### No Unit Tests Yet
No automated test suite currently exists. Future testing should cover:
- Firestore integration tests (mock or dev project)
- External API mocking (football.api-sports.io)
- CORS header validation

## Common Workflows

### Adding a New Cloud Function
1. Create directory in `/src/<functionName>/` with `main.py` and `requirements.txt`
2. Implement `@functions_framework.http` decorated function
3. Add Terraform resource in `cloud_function.tf`:
   - `archive_file` data source
   - `google_storage_bucket_object` for zipped source
   - `google_cloudfunctions_function` resource with entry_point matching function name
4. Set `PROJECT_ID` environment variable in function definition
5. Test locally with functions-framework
6. Deploy: `make dev` or `make prod`

### Modifying Firestore Schema
- Schema is inferred from code (no explicit schema definition)
- Changes in `populateLeagueSeason/main.py` and `buildIndex.py` define structure
- Existing data may require migration (manual Firestore update)
- Test against `db.collection().stream()` queries match expected documents

### Updating External Dependencies
- Python: Edit `requirements.txt` in function directory
- Terraform: Edit `versions.tf` and re-run `terraform plan`
- Cloud Functions automatically re-archive and redeploy on code change (MD5-based detection)

## Critical Files to Know
- `/src/populateLeagueSeason/main.py` - Data ingestion logic and API calls
- `/src/populateLeagueSeason/buildIndex.py` - Index generation from raw data
- `/src/populateLeagueSeason/colors.py` - Team-specific styling constants
- `/src/getIndex/main.py` - Frontend data API reference implementation
- `/tf/cloud_function.tf` - Function deployment configuration
- `/tf/secrets.tf` - Secret Manager and service account IAM setup
- `Makefile` - Deployment commands

## Gotchas & Considerations
- **Terraform state**: Stored in versioned GCS bucket; workspace-aware
- **Python 3.9**: Cloud Functions runtime specified as `python39` (legacy, consider updating)
- **API rate limiting**: football.api-sports.io has strict rate limits; backdate logic avoids unnecessary calls
- **Environment variables**: Set at deployment time; must match function expectations (e.g., `PROJECT_ID`)
- **CORS hardcoding**: Origins hardcoded in function code (work in progress); future refactor to environment variables
- **GKE Autopilot**: Enabled and configured but not yet in use; reserved for future containerized services
