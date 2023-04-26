#!/bin/bash
set -e
if [[ ! $(kustomize version) == *v5.* ]]; then
    echo "Kustomize version 5 or later required for chart build."
    echo "Please install a valid version then try again."
    exit 1
fi
kustomize build overlay/ --output kustomize-build-output.yml
python3 to-helm-chart.py
# git add ../kubeflow-azimuth-chart