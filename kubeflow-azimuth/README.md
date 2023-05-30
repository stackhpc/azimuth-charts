# KubeFlow Azimuth chart

## Overview 

This chart provides support for KubeFlow as an Azimuth platform. According to the kubeflow maintainers, the recommended way to install kubeflow on a Kubernetes cluster is to use the provided [Kustomize manifests](https://github.com/kubeflow/manifests). However, Azimuth currently only supports Helm charts as the basis for platforms, therefore this chart's primary focus is providing the tools for converting the upstream Kustomize manifests into an installable Helm chart.

The starting point for this process is the `kustomization/base/kustomization.yaml` file, which pulls in a versioned release of the upstream KubeFlow manifests (so updates to the upstream manifests can therefore be pulled in by bumping the version reference in the `resources` section of this file then rebuilding the chart - see below). Further kustomizations are then applied in the `overlay` directory, these include:

- Converting the `istio-sidecar-injector` mutating webhook to a Helm pre-install hook to ensure all required pods receive the sidecar proxy container

- Adding the required `Client` and `Reservation` resource definitions to allow Zenith to proxy the KubeFlow web dashboard for external access

- Various Helm pre/post-delete hooks to clean up cluster resources when the platform is deleted

Finally, the `to-helm-chart.py` script converts these kustomized manifests into the Helm-installable `kubeflow-azimuth-chart` directory. The script also generates the `kubeflow-crds` chart which is added as a dependency of the main chart. This is done to work around the fact that the Helm release secret generated when trying to install all manifests in a single chart is >1MB in size and is therefore rejected by `etcd`, causing the installation to fail.

## Rebuilding the chart

When pushing changes to github, the `build-chart.sh` script is run automatically as part of the 'Publish charts' workflow. However, for local development and testing the chart can be rebuilt manually with

```bash
cd kubeflow-azimuth/
./build-chart.sh
```

The `build-chart.sh` script will output all of the kustomized manifests to `kustomize-build-output.yml` (which is git-ignored by default but can be inspected locally to check that the desired kustomization were applied correctly) before running the helm-chart-generating python script which reads from this file.

## Updating Helm metadata

The single 'source of truth' for the Helm metadata (e.g. the chart release version) is the `to-helm-chart.py` script; therefore, to update Helm metadata files (e.g. `Chart.yaml`, `values.yaml` & `values.schema.json`) the relevant sections of the python script should be modified.