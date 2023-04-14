import yaml
from pathlib import Path

# Create Helm chart directory structure
chart_path = Path("../kubeflow-azimuth-chart")
print('Creating Helm chart at', chart_path.absolute())
chart_path.mkdir(exist_ok=True)
(chart_path / 'templates').mkdir(exist_ok=True)
(chart_path / 'crds').mkdir(exist_ok=True)
(chart_path / 'chart.yaml').touch(exist_ok=True)
(chart_path / 'values.yaml').touch(exist_ok=True)

# Write chart.yaml
chart_yml = """---
apiVersion: v1
name: kubeflow-azimuth
version: 0.0.1
"""
with open(chart_path / 'chart.yaml', 'w') as file:
    file.write(chart_yml)

# Write manifest files
with open('build-output.yml', 'r') as input_file:
    all_manifests = yaml.safe_load_all(input_file)
    for i, manifest in enumerate(all_manifests):
        manifest_name = manifest['metadata']['name'].replace('.', '-') + '.yml'
        manifest_path = chart_path / ('crds' if manifest['kind'] == 'CustomResourceDefinition' else 'templates') / manifest_name
        print(f'{i+1}.\t Writing {manifest_path}')
        with open(manifest_path, 'w') as output_file:
            yaml.dump(manifest, output_file)