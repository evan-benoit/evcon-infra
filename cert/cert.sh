# https://cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs#gcloud

gcloud compute ssl-certificates create trophypace-cert \
    --description=SSL \
    --domains=trophypace.com,www.trophypace.com \
    --global

gcloud compute ssl-certificates list \
   --global


gcloud compute ssl-certificates describe trophypace-cert \
   --global \
   --format="get(name,managed.status, managed.domainStatus)"


# https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address

gcloud compute addresses create trophypace \
  --global \
  --ip-version IPV4 


# https://cloud.google.com/kubernetes-engine/docs/how-to/managed-certs

gcloud compute addresses describe trophypace --global
# address: 34.120.168.62

kubectl apply -f managed-cert.yaml

kubectl apply -f mc-service.yaml

kubectl apply -f managed-cert-ingress.yaml


kubectl get ingress
# managed-cert-ingress   <none>   *       34.120.168.62   80      119s
# yeah, it matches what I expected

# Change dns.tf

terraform apply

dig trophypace.com
# www.trophypace.com.	300	IN	CNAME	trophypace.com.
# trophypace.com.		300	IN	A	34.120.168.62



kubectl describe managedcertificate managed-cert

