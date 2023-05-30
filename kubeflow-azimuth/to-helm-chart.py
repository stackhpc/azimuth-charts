import yaml, re, shutil
from pathlib import Path

def make_helm_chart_template(chart_path, chart_yml, values_yml):
    """Creates a template directory structure for a helm chart"""
    print('Creating Helm chart at', chart_path.absolute())
    # Remove any existing content at chart path 
    # TODO: Add user confirmation and/or --force cmd line arg for deletion?
    try:
        shutil.rmtree(chart_path)
    except FileNotFoundError:
        pass
    # Create Helm chart directory structure
    chart_path.mkdir()
    (chart_path / 'templates').mkdir()
    (chart_path / 'crds').mkdir()
    # Write Chart.yaml
    with open(chart_path / 'Chart.yaml', 'w') as file:
        file.write(chart_yml)
    # Write values.yaml
    with open(chart_path / 'values.yaml', 'w') as file:
        file.write(values_yml)


crd_chart_path = Path("./kubeflow-crds")
crd_chart_yml = """---
apiVersion: v1
name: kubeflow-crds
version: 0.0.1
"""
crd_values_yml = ""
make_helm_chart_template(crd_chart_path, crd_chart_yml, crd_values_yml)

main_chart_path = Path("./kubeflow-azimuth-chart")
chart_yml = f"""---
apiVersion: v1
name: kubeflow-azimuth
version: 0.0.2
icon: https://www.kubeflow.org/images/logo.svg
description: A KubeFlow machine learning environment
dependencies:
  - name: kubeflow-crds
    version: ">=0-0"
    repository: file://../{crd_chart_path}
annotations:
  azimuth.stackhpc.com/label: KubeFlow
"""
values_yml = ""
make_helm_chart_template(main_chart_path, chart_yml, values_yml)

# Write values schema to be consumed by Azimuth UI
json_schema = """
{
    "$schema": "http://json-schema.org/schema#",
    "type": "object",
    "properties": {},
    "required": []
}
"""
with open(main_chart_path / 'values.schema.json', 'w') as schema_file:
    schema_file.write(json_schema)


# List of container images that have been synced to stackhpc's ghcr
# by the skopeo github workflow, we want to patch the relevant k8s
# manifests to prepend 'ghcr.io/stackhpc/azimuth-charts/' to these
# images paths so that the images are pulled from the ghcr mirror
# (doing so via a loop in this script is far simpler than adding a
# separate kustomize patch for each image)
MIRRORED_IMAGES = [
    'docker.io/istio/pilot:1.16.0',
    'docker.io/istio/proxyv2:1.16.0',
    'docker.io/kubeflowkatib/katib-controller:v0.15.0',
    'docker.io/kubeflowkatib/katib-db-manager:v0.15.0',
    'docker.io/kubeflowkatib/katib-ui:v0.15.0',
    'docker.io/kubeflownotebookswg/centraldashboard:v1.7.0',
    'docker.io/kubeflownotebookswg/jupyter-web-app:v1.7.0',
    'docker.io/kubeflownotebookswg/kfam:v1.7.0',
    'docker.io/kubeflownotebookswg/notebook-controller:v1.7.0',
    'docker.io/kubeflownotebookswg/poddefaults-webhook:v1.7.0',
    'docker.io/kubeflownotebookswg/profile-controller:v1.7.0',
    'docker.io/kubeflownotebookswg/tensorboard-controller:v1.7.0',
    'docker.io/kubeflownotebookswg/tensorboards-web-app:v1.7.0',
    'docker.io/kubeflownotebookswg/volumes-web-app:v1.7.0',
    'docker.io/metacontrollerio/metacontroller:v2.0.4',
    'gcr.io/arrikto/kubeflow/oidc-authservice:e236439',
    'gcr.io/knative-releases/knative.dev/eventing/cmd/controller@sha256:33d78536e9b38dbb2ec2952207b48ff8e05acb48e7d28c2305bd0a0f7156198f',
    'gcr.io/knative-releases/knative.dev/eventing/cmd/webhook@sha256:d217ab7e3452a87f8cbb3b45df65c98b18b8be39551e3e960cd49ea44bb415ba',
    'gcr.io/knative-releases/knative.dev/net-istio/cmd/controller@sha256:2b484d982ef1a5d6ff93c46d3e45f51c2605c2e3ed766e20247d1727eb5ce918',
    'gcr.io/knative-releases/knative.dev/net-istio/cmd/webhook@sha256:59b6a46d3b55a03507c76a3afe8a4ee5f1a38f1130fd3d65c9fe57fff583fa8d',
    'gcr.io/knative-releases/knative.dev/serving/cmd/activator@sha256:c3bbf3a96920048869dcab8e133e00f59855670b8a0bbca3d72ced2f512eb5e1',
    'gcr.io/knative-releases/knative.dev/serving/cmd/autoscaler@sha256:caae5e34b4cb311ed8551f2778cfca566a77a924a59b775bd516fa8b5e3c1d7f',
    'gcr.io/knative-releases/knative.dev/serving/cmd/controller@sha256:38f9557f4d61ec79cc2cdbe76da8df6c6ae5f978a50a2847c22cc61aa240da95',
    'gcr.io/knative-releases/knative.dev/serving/cmd/domain-mapping-webhook@sha256:a4ba0076df2efaca2eed561339e21b3a4ca9d90167befd31de882bff69639470',
    'gcr.io/knative-releases/knative.dev/serving/cmd/domain-mapping@sha256:763d648bf1edee2b4471b0e211dbc53ba2d28f92e4dae28ccd39af7185ef2c96',
    'gcr.io/knative-releases/knative.dev/serving/cmd/webhook@sha256:bc13765ba4895c0fa318a065392d05d0adc0e20415c739e0aacb3f56140bf9ae',
    'gcr.io/kubebuilder/kube-rbac-proxy:v0.13.1',
    'gcr.io/kubebuilder/kube-rbac-proxy:v0.8.0',
    'gcr.io/ml-pipeline/api-server:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/cache-server:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/frontend:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/metadata-envoy:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/metadata-writer:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/minio:RELEASE.2019-08-14T20-37-41Z-license-compliance',
    'gcr.io/ml-pipeline/mysql:8.0.26',
    'gcr.io/ml-pipeline/persistenceagent:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/scheduledworkflow:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/viewer-crd-controller:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/visualization-server:2.0.0-alpha.7',
    'gcr.io/ml-pipeline/workflow-controller:v3.3.8-license-compliance',
    'gcr.io/tfx-oss-public/ml_metadata_store_server:1.5.0',
    'kserve/kserve-controller:v0.10.0',
    'kserve/models-web-app:v0.10.0',
    'kubeflow/training-operator:v1-5a5f92d',
    'kubeflownotebookswg/jupyter-pytorch-cuda-full:v1.7.0',
    'kubeflownotebookswg/jupyter-pytorch-full:v1.7.0',
    'kubeflownotebookswg/jupyter-scipy:v1.7.0',
    'kubeflownotebookswg/jupyter-tensorflow-cuda-full:v1.7.0',
    'kubeflownotebookswg/jupyter-tensorflow-full:v1.7.0',
    'mysql:8.0.29',
    'python:3.7',
    'quay.io/jetstack/cert-manager-cainjector:v1.10.1',
    'quay.io/jetstack/cert-manager-controller:v1.10.1',
    'quay.io/jetstack/cert-manager-webhook:v1.10.1',
    'tensorflow/tensorflow:2.5.1',
]


# Write manifest files
with open('kustomize-build-output.yml', 'r') as input_file:
    # NOTE: Read input file as str instead of yaml to preserve newlines
    # all_manifests = yaml.load_all(input_file) 
    all_manifests = input_file.read().split("\n---\n")
    for i, manifest_str in enumerate(all_manifests):
        
        # Convert to yaml for field queries
        manifest = yaml.safe_load(manifest_str)
        
        # NOTE: CRDs and namespaces are placed in separate sub-chart since trying to
        # bundle all manifests into a single helm chart creates a helm release secret
        # > 1MB which etcd then refuses to store so installation fails
        manifest_name = manifest['metadata']['name'].replace('.', '-') + f'-{i+1}.yml'
        if manifest['kind'] == 'CustomResourceDefinition':
            manifest_path = crd_chart_path / 'crds' / manifest_name
        elif manifest['kind'] == 'Namespace':
            manifest_path = crd_chart_path / 'templates' / manifest_name
        else:
            manifest_path = main_chart_path / 'templates' / manifest_name
        print(f'{i+1}.\t Writing {manifest_path}')
        
        # NOTE: Some manifest files have '{{' and '}}' instances in comments
        # These need to be escaped so that helm doesn't try to template them
        # Regex should match everying within a curly bracket that isn't a curly bracket itself
        manifest_str = re.sub(r"{{([^\{\}]*)}}", r'{{ "{{" }}\1{{ "}}" }}', manifest_str)

        # Replace mirrored container images with path to stackhpc mirror
        for image in MIRRORED_IMAGES:
            manifest_str = re.sub(image, 'ghcr.io/stackhpc/azimuth-charts/' + image, manifest_str)

        # Write manifest to file
        # NOTE: Avoid using yaml.dumps here as it doesn't properly preserve multi-line
        # yaml blocks (e.g. key: | \n ...) and instead replaces all newlines with '\n' 
        # inside blocks, making final manifests less readable.
        with open(manifest_path, 'w') as output_file:
            output_file.write(manifest_str)
        