"""
This script should be fed the `FILE_PATH` output of the following kubectl command which
lists all container images currently in use on the target kubernetes cluster:

kubectl get pods --all-namespaces -o jsonpath="{.items[*].spec.containers[*].image}" \ 
| tr -s '[[:space:]]' '\n' | sort | uniq > FILE_PATH

The script will then generate an output file named skopeo-manifest-{FILE_PATH}.yaml which 
is formatted such that it can be fed into the sync-images.yml github workflow to copy any 
required images into a dedicated container registry.

NOTE: In order to capture the images used by the deployed platforms (e.g. the jupyter 
notebook container) the relevant platform components should be deployed cluster before 
running this script.
"""

import sys, yaml
from pathlib import Path
from functools import reduce

if len(sys.argv) != 2:
    print("Path to input file must be the sole command line arg to this script")
    sys.exit(1)

file_path = Path(sys.argv[1])
# Kubernetes assumes docker registry by default:
# https://kubernetes.io/docs/concepts/containers/images/#image-names
default_registry = "docker.io"


def split_image_url(url: str):
    try:
        parts = url.strip("\n").split("/")
        registry = parts[0] if len(parts) > 1 else default_registry
        # TODO: Check if skopeo copy a no-op when
        #       source and destination are the same
        if registry == "ghcr.io":
            return {}
        repo_plus_version = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
        repo, version = repo_plus_version.split(":")
        if "@sha256" in repo:
            repo = repo.replace("@sha256", "")
            version = "sha256:" + version
        return {registry: {"images": {repo: [version]}}}
    except Exception as e:
        raise Exception(f"Failed to parse url: {url}\nException was:", e)


def dict_merge_recursive(d1, d2):
    """update first dict with second recursively"""
    try:
        for k, v in d1.items():
            if k in d2:
                if isinstance(v, list):
                    d2[k] += v
                else:
                    d2[k] = dict_merge_recursive(v, d2[k])
        d1.update(d2)
        return d1
    except Exception as e:
        raise Exception(f"Failed to merge dicts: {d1} & {d2}\nException was:", e)


# Loop through lines in file and convert to a nested dict
with open(file_path, "r") as file:
    result_dict = reduce(dict_merge_recursive, map(split_image_url, file.readlines()))
    with open(f"skopeo-manifest-{file_path.stem}.yml", "w") as out_file:
        yaml.safe_dump(result_dict, out_file)
