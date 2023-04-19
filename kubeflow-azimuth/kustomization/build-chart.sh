#!/bin/bash
kustomize build overlay --output kustomize-build-output.yml
python3 to-helm-chart.py