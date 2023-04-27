# KubeFlow Azimuth chart

## Overview 

This chart provides support for KubeFlow as an Azimuth platform. According to the kubeflow maintainers, the recommended way to install kubeflow on a kubernetes cluster is to use the provided [Kustomize manifests](https://github.com/kubeflow/manifests). However, Azimuth currently only supports Helm charts as the basis for platforms, therefore this chart's primary focus is providing the tools for converting the upstream Kustomize manifests into an installable Helm chart.

The starting point for this process is the `kustomization/base/kustomization.yaml` file, which pulls in a versioned release of the upstream KubeFlow manifests (so updates to the upstream manifests can therefore be pulled in by bumping the version reference in the `resources` section of this file then rebuilding the chart - see below). Further kustomizations are then applied in the `overlay` directory, these include:

- Converting the `istio-sidecar-injector` mutating webhook to a Helm pre-install hook to ensure all required pods receive the sidecar proxy container

- Adding the required `Client` and `Reservation` resource definitions to allow Zenith to proxy the KubeFlow web dashboard for external access

- Various Helm pre/post-delete hooks to clean up cluster resources when the platform is deleted

Finally, the `to-helm-chart.py` script converts these kustomized manifests into the Helm-installable `kubeflow-azimuth-chart` directory. The script also generates the `kubeflow-crds` chart which is added as a dependency of the main chart. This is done to work around the fact that the Helm release secret generated when trying to install all manifests in a single chart is >1MB in size and is therefore rejected by `etcd`, causing the installation to fail.

## Rebuilding the chart

After making any changes to the kustomizations or the chart-generating python script, the following steps should be run to update all relevant files and pick up the changes with git:

```bash
cd kubeflow-azimuth/kustomization
./build-chart.sh
git add ../
```

The `build-chart.sh` script will output all of the kustomized manifests to `kustomize-build-output.yml` (which can later be inspected to check that the desired kustomization were applied correctly) then runs the helm-chart-generating python script. Since the helm manifest file names are tagged with an iteration index to ensure uniqueness, any changes may generate new untracked files, hence the need to re-add the entire directory to `git` to pick up any changes.

## Updating Helm metadata

The current 'source of truth' for the Helm metadata (e.g. the chart release version) is the `to-helm-chart.py` script. This script deletes all files in the `kubeflow-azimuth-chart` and `kubeflow-crds` directories before any chart build, therefore any changes made directly to the files in these charts will not presist. To update Helm metadata files (e.g. `Chart.yaml`, `values.yaml` & `values.schema.json`) you should instead modified the relevant sections of the python script.