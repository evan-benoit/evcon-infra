#From https://gist.github.com/palewire/12c4b2b974ef735d22da7493cf7f4d37

export PROJECT_ID=evcon-app
export SERVICE_ACCOUNT=art-reg-service-account
gcloud iam service-accounts create "${SERVICE_ACCOUNT}" \
  --project "${PROJECT_ID}"


gcloud services enable iamcredentials.googleapis.com \
--project "${PROJECT_ID}"

export WORKLOAD_IDENTITY_POOL=github-pool
gcloud iam workload-identity-pools create "${WORKLOAD_IDENTITY_POOL}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="${WORKLOAD_IDENTITY_POOL}"


#projects/488133362511/locations/global/workloadIdentityPools/github-pool
gcloud iam workload-identity-pools describe "${WORKLOAD_IDENTITY_POOL}" \
--project="${PROJECT_ID}" \
--location="global" \
--format="value(name)"

export WORKLOAD_IDENTITY_POOL_ID=projects/488133362511/locations/global/workloadIdentityPools/github-pool


export WORKLOAD_PROVIDER=gh-provider
gcloud iam workload-identity-pools providers create-oidc "${WORKLOAD_PROVIDER}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="${WORKLOAD_IDENTITY_POOL}" \
  --display-name="${WORKLOAD_PROVIDER}" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"


#[evtodo] I assume he means github username and repo?
# export REPO=my-username/my-repository
export REPO=evan-benoit/evcon

gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}"


#projects/488133362511/locations/global/workloadIdentityPools/github-pool/providers/gh-provider
gcloud iam workload-identity-pools providers describe "${WORKLOAD_PROVIDER}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="${WORKLOAD_IDENTITY_POOL}" \
  --format="value(name)"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"


gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format='table(bindings.role)' \
    --filter="bindings.members:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"


