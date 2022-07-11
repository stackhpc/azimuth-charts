# daskhub-zenith-nfs-lustre

This Helm chart deploys a JupyterHub with Dask/Pangeo workers that is 
exposed via Zenith. Authentication and authorization is determined by 
the authenticated Azimuth portal user.

An NFS export (`/mnt/lustre`) from an external NFS server (`192.168.3.4`)
is mounted at `/lustre`. This default configuration is used to expose a
Lustre filesystem to Jupyter notebooks in `rcp-cloud-portal-demo`, but in
principle should work with any NFS server external-to but accessible-from
Kubernetes worker nodes.

Updates to this configuration are not possible using the Kubeapps form, but
all values can be edited in the YAML tab of the Kubeapps deployment dialog.
