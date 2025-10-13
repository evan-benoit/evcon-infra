.PHONY: dev prod

dev:
	terraform -chdir=tf workspace select dev || terraform workspace new dev
	terraform -chdir=tf apply -var-file=dev.tfvars

prod:
	terraform -chdir=tf workspace select default || terraform workspace new default
	terraform -chdir=tf apply -var-file=prod.tfvars