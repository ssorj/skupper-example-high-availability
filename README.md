# Skupper and highly available services

## Running it

1. Set up a kubeconfig at `~/.kube/config-gke`.
2. Run `make run`.

## The deployment

- North and south are edge clusters.  Both run in Minikube.
- The east and west clusters run on GKE.
