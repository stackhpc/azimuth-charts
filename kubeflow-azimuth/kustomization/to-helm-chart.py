import yaml, re, shutil
from pathlib import Path

# A list of resource to include in the sub-chart
# NOTE: This is an attempt to mimic the `sortOptions` kustomization field used in
#       https://github.com/kubeflow/manifests/blob/master/example/kustomization.yaml
#       (I can't find any Helm docs stating whether dependency resources are 
#       actually installed first or not.)
DEPENDENCY_RESOURCES = [
    "Namespace",
    "ResourceQuota",
    "StorageClass",
    "MutatingWebhookConfiguration",
    "ServiceAccount",
    "PodSecurityPolicy",
    "Role",
    "ClusterRole",
    "RoleBinding",
    "ClusterRoleBinding",
    "ConfigMap",
    "Secret",
    "Endpoints",
    "Service",
]

def make_helm_chart_template(chart_path, chart_yml):
    """Creates a template directory structure for a helm chart"""
    print('Creating Helm chart at', chart_path.absolute())
    # Remove any existing content at chart path 
    # TODO: Add user confirmation & --force cmd line arg?
    shutil.rmtree(chart_path)
    # Create Helm chart directory structure
    chart_path.mkdir()
    (chart_path / 'templates').mkdir()
    (chart_path / 'crds').mkdir()
    (chart_path / 'values.yaml').touch()
    # Write Chart.yaml
    with open(chart_path / 'Chart.yaml', 'w') as file:
        file.write(chart_yml)


main_chart_path = Path("../kubeflow-azimuth-chart")
chart_yml = """---
apiVersion: v1
name: kubeflow-azimuth
version: 0.0.2
icon: https://www.kubeflow.org/images/logo.svg
description: A KubeFlow machine learning environment
dependencies:
  - name: kubeflow-crds
    version: ">=0-0"
    repository: file://../kubeflow-crds
annotations:
  azimuth.stackhpc.com/label: KubeFlow
"""
make_helm_chart_template(main_chart_path, chart_yml)

# Write values schema
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


crd_chart_path = Path("../kubeflow-crds")
crd_chart_yml = """---
apiVersion: v1
name: kubeflow-crds
version: 0.0.1
"""
make_helm_chart_template(crd_chart_path, crd_chart_yml)


# Write manifest files
with open('kustomize-build-output.yml', 'r') as input_file:
    # all_manifests = yaml.load_all(input_file)
    all_manifests = input_file.read().split("\n---\n")
    for i, manifest_str in enumerate(all_manifests):
        manifest = yaml.load(manifest_str)
        manifest_name = manifest['metadata']['name'].replace('.', '-') + f'-{i+1}.yml'
        if manifest['kind'] == 'CustomResourceDefinition':
            manifest_path = crd_chart_path / 'crds' / manifest_name
        elif manifest['kind'] in DEPENDENCY_RESOURCES:
            manifest_path = crd_chart_path / 'templates' / manifest_name
        else:
            manifest_path = main_chart_path / 'templates' / manifest_name
        print(f'{i+1}.\t Writing {manifest_path}')
        # Some manifest files have '{{' and '}}' instances in comments
        # These need to be escaped so that helm doesn't try to template them
        # Note - Regex should match everying within a curly bracket that isn't a curly bracket itself
        # manifest_str = re.sub(r"{{([a-zA-Z\-\(\)\.\ \`]+)}}", r'{{ "{{" }}\1{{ "}}" }}', manifest_str)
        manifest_str = re.sub(r"{{([^\{\}]*)}}", r'{{ "{{" }}\1{{ "}}" }}', manifest_str)
        # Write manifest to file
        with open(manifest_path, 'w') as output_file:
            output_file.write(manifest_str)
        # NOTE: Alternative version below using yaml.dumps doesn't preserve yaml blocks (e.g. key: | ...)
        #       properly replaces all newlines with \n inside blocks, making final manifests less readable
        # yaml_str = yaml.dump(manifest, indent=2)
        # yaml_str = re.sub(r"{{ (.*) }}", r'{{ "{{" }} \1 {{ "}}" }}', yaml_str)
        # # Write manifest to file
        # with open(manifest_path, 'w') as output_file:
        #     output_file.write(yaml_str)
