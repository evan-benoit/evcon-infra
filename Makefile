.PHONY: dev prod

dev:
	terraform -chdir=tf workspace select dev || terraform workspace new dev
	terraform -chdir=tf apply -var-file=dev.tfvars

prod:
	terraform -chdir=tf workspace select default || terraform workspace new default
	terraform -chdir=tf apply -var-file=prod.tfvars


dev-destroy:
	terraform -chdir=tf workspace select dev || terraform workspace new dev
	terraform -chdir=tf destroy -var-file=dev.tfvars

prod-destroy:
	terraform -chdir=tf workspace select default || terraform workspace new default
	terraform -chdir=tf destroy -var-file=prod.tfvars


