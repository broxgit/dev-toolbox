# Kubernetes Aliases
The file containing the aliases is located here in the repository: **powershell\Kubernetes_Aliases.ps1**. You can add these aliases to your PowerShell profile by following these steps:    

1. Copy the Kubernetes_Aliases.ps1 file to your **$HOME\Documents\WindowsPowerShell** directory.    
Example: _C:\Users\chad\Documents\WindowsPowerShell_
2. Open your **$HOME\Documents\WindowsPowerShell\PowerShell_profile.ps1** file, if you do not have one, create one. 
3. Add the following lines to the top of the **PowerShell_profile.ps1** file:    
    ```powershell
    $CurrentLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
    Import-Module "$CurrentLocation\Kubernetes_Aliases.ps1" -Force
    ```    
4. Close all open PowerShell Windows and re-open PowerShell to load the changes, or type `$ .profile` in a currently open PowerShell window.  

#### Commands/Aliases
| Shortcut/Alias          	| Command                                                        	| Description                                                                                   	| Example            	|
|-------------------------	|----------------------------------------------------------------	|-----------------------------------------------------------------------------------------------	|--------------------	|
| k $args                 	| kubectl $args                                                  	| Abbreviate version of kubectl $args                                                           	| k get pods         	|
| kgpa                    	| kubectl get pods -A                                            	| Gets all pods in all namespaces                                                               	|                    	|
| kgpaw                   	| kubectl get pods -A -o wide                                    	| Gets all pods in all namespaces with additional info                                          	|                    	|
| kga                     	| kubectl get all -A                                             	| Get all Kubernetes objects in all namespaces                                                  	|                    	|
| kgna                    	| kubectl get namespaces                                         	| Get all namespaces                                                                            	|                    	|
| kgsa                    	| kubectl get services -A                                        	| Get all services in all namespaces                                                            	|                    	|
| kgda                    	| kubectl get deployments -A                                     	| Get all deployments in all namespaces                                                         	|                    	|
| kgea                    	| kubectl get endpoints -A                                       	| Get all endpoints in all namespaces                                                           	|                    	|
| kgseca                  	| kubectl get secrets -A                                         	| Get all secrets in all namespaces                                                             	|                    	|
| kgia                    	| kubectl get ingress -A                                         	| Get all ingresses in all namespaces                                                           	|                    	|
| kgn                     	| kubectl get nodes                                              	| Get all nodes                                                                                 	|                    	|
| klogs $pod              	| kubectl logs pods/$pod                                         	| Get logs for specified pod using the shortname (any unique part of the pod name)              	| klogs rest         	|
| klogsf $pod             	| kubectl logs pods/$pod -f                                      	| Get and follow logs for specified pod using the shortname (any unique part of the pod name)   	| klogsf rest        	|
| klogsc $pod $container  	| kubectl logs pods/$pod $container                              	| Get logs for specified container of pod using the shortname (any unique part of the pod name) 	| klogsc rest audit  	|
| kdescp $pod             	| kubectl describe pods/$pod                                     	| Describe a pod using the shortname (any unique part of pod name)                              	| kdescp keyserver   	|
| kdescs $service         	| kubectl describe services/$service                             	| Describe a service using the shortname (any unique part of the service name)                  	| kdescs consul      	|
| kdescd $deployment      	| kubectl describe deployments/$deployment                       	| Describe a deployment using the shortname (any unique part of the deployment name)            	| kdescd kdc         	|
| kshell $pod             	| kubectl exec -it podname -n podnamespace -- /bin/sh            	| Shell into a pod using the pod shortname                                                      	| kshell rest        	|
| kshellc $pod $container 	| kubectl exec -it podname $container -n podnamespace -- /bin/sh 	| Shell into a specific container inside a pod using the pod and container shortnames          	    | kshellc rest audit 	|