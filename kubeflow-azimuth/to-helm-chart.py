import yaml, re, shutil
from pathlib import Path


def make_helm_chart_template(chart_path, chart_yml, values_yml):
    """Creates a template directory structure for a helm chart"""
    print("Creating Helm chart at", chart_path.absolute())
    # Remove any existing content at chart path
    # TODO: Add user confirmation and/or --force cmd line arg for deletion?
    try:
        shutil.rmtree(chart_path)
    except FileNotFoundError:
        pass
    # Create Helm chart directory structure
    chart_path.mkdir()
    (chart_path / "templates").mkdir()
    (chart_path / "crds").mkdir()
    # Write Chart.yaml
    with open(chart_path / "Chart.yaml", "w") as file:
        file.write(chart_yml)
    # Write values.yaml
    with open(chart_path / "values.yaml", "w") as file:
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
with open(main_chart_path / "values.schema.json", "w") as schema_file:
    schema_file.write(json_schema)

# Read the skopeo container manifest so that we can redirect image pulls to
# stackhpc's ghcr mirror
with open("../skopeo-manifests/kubeflow.yml", "r") as container_manifests_file:
    CONTAINER_MANIFEST = yaml.safe_load(container_manifests_file)

# Write manifest files
with open("kustomize-build-output.yml", "r") as input_file:
    # NOTE: Read input file as str instead of yaml to preserve newlines
    # all_manifests = yaml.load_all(input_file)
    all_manifests = input_file.read().split("\n---\n")
    for i, manifest_str in enumerate(all_manifests):
        # Convert to yaml for field queries
        manifest = yaml.safe_load(manifest_str)

        # NOTE: CRDs and namespaces are placed in separate sub-chart since trying to
        # bundle all manifests into a single helm chart creates a helm release secret
        # > 1MB which etcd then refuses to store so installation fails
        manifest_name = manifest["metadata"]["name"].replace(".", "-") + f"-{i+1}.yml"
        if manifest["kind"] == "CustomResourceDefinition":
            manifest_path = crd_chart_path / "crds" / manifest_name
        elif manifest["kind"] == "Namespace":
            manifest_path = crd_chart_path / "templates" / manifest_name
        else:
            manifest_path = main_chart_path / "templates" / manifest_name
        print(f"{i+1}.\t Writing {manifest_path}")

        # NOTE: Some manifest files have '{{' and '}}' instances in comments
        # These need to be escaped so that helm doesn't try to template them
        # Regex should match everying within a curly bracket that isn't a curly bracket itself
        manifest_str = re.sub(
            r"{{([^\{\}]*)}}", r'{{ "{{" }}\1{{ "}}" }}', manifest_str
        )

        # Replace mirrored container images with path to stackhpc mirror
        # for image in MIRRORED_IMAGES:
        #     manifest_str = re.sub(
        #         image, "ghcr.io/stackhpc/azimuth-charts/" + image, manifest_str
        #     )
        for registry, contents in CONTAINER_MANIFEST.items():
            images = contents["images"]
            for image, versions in images.items():
                for v in versions:
                    # NOTE: since some container image paths omit the registry
                    # and rely on k8s defaulting to docker.io, we have to be careful
                    # with the logic here and handle several cases explicitly

                    image_url = (
                        f"{image}:{v}" if "sha256" not in v else f"{image}@sha256:{v}"
                    )

                    # Case where registry is given upstream
                    if f"{registry}/{image_url}" in manifest_str:
                        new_prefix = "ghcr.io/stackhpc/azimuth-charts/"
                        # Replace image url in k8s manifest
                        manifest_str = re.sub(
                            f"{registry}/{image_url}",
                            new_prefix + f"{registry}/{image_url}",
                            manifest_str,
                        )
                    # Case where default registry is omitted upstream
                    elif image_url in manifest_str:
                        new_prefix = "ghcr.io/stackhpc/azimuth-charts/docker.io/"
                        # NOTE: Skopeo seems to sync these two images to ghcr as docker.io/library/<image>,
                        # haven't worked out why so handle it here for now
                        if image in ["python", "mysql"]:
                            new_prefix += f"library/"
                        # Replace image url in k8s manifest
                        manifest_str = re.sub(
                            image_url, new_prefix + image_url, manifest_str
                        )

        # Write manifest to file
        # NOTE: Avoid using yaml.dumps here as it doesn't properly preserve multi-line
        # yaml blocks (e.g. key: | \n ...) and instead replaces all newlines with '\n'
        # inside blocks, making final manifests less readable.
        with open(manifest_path, "w") as output_file:
            output_file.write(manifest_str)
