# Python Kubernetes Client    
A collection of scripts that use the Python Kubernetes Client

# K8s Utils 
### Name: k8s_utils.py
A utility script that provides various tools for managing your deployment and Kubernetes objects. 
## Information
There are some user-defined variables in the script that can be modified if the default values don't work for your setup. 
- **NAMESPACES**: This is a list of namespaces you would like the script to manage, currently this is used when invoking the **--cleanup** argument.    
This is currently setup with **logging**, **frontend**, and **backend**.

- **PVC_LIST**: A list of PVCs for the script to manage, this is currently used by the **--cleanup** argument.    
This is currently setup with **consul** and **postgres** PVCs.

- **HELM_CHARTS**: A dictionary of Helm Charts and the namespaces that belong to them respectively. These values are used when invoking the **--nuke** command, which expects the HELM_CHART value to have a mapping in the HELM_CHARTS dictionary.    
This is currently setup with **main** and **auxiliary**
## Usage
```powershell
k8s_utils.py        [-h] | [-c, --cleanup] | [-l, --listpods] | 
                    [-v, --values] | [--debugpod DEBUGPOD] |
                    [--nsobjects NSOBJECTS] | [--nuke NUKE]

Optional Arguments:                    
  -h, --help         show this help message and exit
  --cleanup          Cleanup lingering persistent data objects
  --listpods         List all pods
  --values           Get dynamic values needed for values.yaml
  
  --nuke HELM_CHART         Perform a Helm Delete on the specified chart, remove all PVs/PVCs, and remove any lingering objects belonging to the related namespaces
  --nsobjects NAMESPACE     Get ALL objects belonging to the specified namespace
  --debugpod POD_SHORTNAME  Provide information about a pod using a portion of it's name
```
### Cleanup
#### Info
Cleans up all PV/PVC objects defined in the PVC_LIST, and checks the namespaces in NAMESPACES for any lingering PV/PVC objects, if any are found they are deleted.
#### Command
**_--cleanup_**
#### Example
Cleanup all PV/PVCs in the PVC_LIST and cleanup any lingering PV/PVCs in the NAMESPACE list
```powershell
PS > python k8s_utils.py --cleanup
```
---
### List Pods
#### Info
Lists all pods in the cluster with their respective namespaces and IP addresses
#### Command
**_--listpods_**
#### Example
```powershell
PS > python k8s_utils.py --listpods
Listing pods with their IPs:
...
```
---
### Get Values
#### Info
Gets the 'dynamic' values for the values.yaml
#### Command
**_--values_**
#### Example
```powershell
PS > python k8s_utils.py --values
Use these in your values.yaml:
- hostname: docker-desktop
- storageclass: hostpath
```
---
### Nuke
#### Info
Runs a `helm delete <HELM_CHART> --purge` command, deletes all PV/PVC objects belonging to the namespaces in the chart, and clears Postgres (if exists) of all data in its tables.    

**_Note_**: The namespaces associated with the chart are defined in the **HELM_CHARTS** variable in the **_USER-DEFINED VARIABLES_** section of the script. There are currently Chart/Namespace mappings for **_main_** and **_auxiliary_**.
#### Command
**_--nuke [HELM_CHART]_**    
#### Example
Delete **main** chart, removing all PV/PVC objects, and clearing Postgres data
```powershell
python k8s_utils.py --nuke main
```
---
### Namespace Objects
#### Info
Retrieves and prints all K8s objects belonging to the specified namespace.
#### Command
**_--nsobjects [NAMESPACE]_**    
#### Example
Get all objects belonging to the **frontend** namespace
```powershell
python k8s_utils.py --nsobjects frontend
```
---
### Debug Pod
#### Info
Prints the logs and the result of 'kubectl describe' of a Pod that matches the specified short name. 
#### Command
**_--debugpod [POD_SHORTNAME]_**    
#### Example
Debug the Postgres pod
```powershell
python k8s_utils.py --debugpod postgres
```
---