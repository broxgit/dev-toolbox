# Python Kubernetes Client
A collection of scripts that use the Python Kubernetes Client

## k8s_util.py
A script that is used to perform various tasks against a K8s cluster:
```powershell
python k8s_util.py <flag> <(optional) arguments>
```
#### Flags:
- **cleanup**: deletes PVs and PVCs according to the criteria defined in **_util_config.py_**
- **debug**: returns the logs and a `kubectl describe` for a pod using a shortname (any unique part of the pod name)
- **listpods**: returns all pods in the cluster