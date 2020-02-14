# General Kubernetes Functions

## Abbreviated version of kubectl
function k([Parameter(ValueFromRemainingArguments = $true)]$params) { & kubectl $params }

## Abbreviated version of kubectl
function kc([Parameter(ValueFromRemainingArguments = $true)]$params) { & kubectl $params }

## Get all pods in all namespaces
function kgpa() {
    RunCommand("kubectl get pods -A")
}

## Get all pods in all namespaces with additional info
function kgpaw() {
    RunCommand("kubectl get pods -A -o wide")
}

## Get all Kubernetes objects in all namespaces
function kga() { RunCommand("kubectl get all -A") }

## Get all namespaces
function kgna() { RunCommand("kubectl get namespaces") }

## Get all services in all namespaces
function kgsa() { RunCommand("kubectl get services -A") }

## Get all deployments in all namespaces
function kgda() { RunCommand("kubectl get deployments -A") }

## Get all endpoints in all namespaces
function kgea() { RunCommand("kubectl get endpoints -A") }

## Get all secrets in all namespaces
function kgseca() { RunCommand("kubectl get secrets -A") }

## Get all ingresses in all namespaces
function kgia() { RunCommand("kubectl get ing -A") }

## Get all PVCs in all namespaces
function kgpvca() { RunCommand("kubectl get pvc -A") }

## Get all PVs in all namespaces
function kgpva() { RunCommand("kubectl get pv -A") }

## Get all nodes
function kgn() { RunCommand("kubectl get nodes") }

## Get logs for pod using shortname
function klogs([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl logs $(GetPodAttribute $params "Name") -n $(GetPodAttribute $params "Namespace")")
}

## Get and follow logs for pod using shortname
function klogsf([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl logs -f $(GetPodAttribute $params "Name") -n $(GetPodAttribute $params "Namespace")")
}

## Get logs of a speoific container inside a pod (for pods with multiple containers)
function klogsc() {
    Param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $podName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $container
    )
    RunCommand("kubectl logs $(GetPodAttribute $podName "Name") -c $container -n $(GetPodAttribute $podName "Namespace")")
}

## Get and follow logs of a speoific container inside a pod (for pods with multiple containers)
function klogscf() {
    Param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $podName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $container
    )
    RunCommand("& kubectl logs -f $(GetPodAttribute $podName "Name") -c $container -n $(GetPodAttribute $podName "Namespace")")
}

## Describe pod using shortname
function kdescp([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("& kubectl describe pods/$(GetPodAttribute $params "Name") -n $(GetPodAttribute $params "Namespace")")
}

## Describe service using shortname
function kdescs([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl describe services/$(GetServiceAttribute $params "Name") -n $(GetServiceAttribute $params "Namespace")")
}

## Describe deployoment using shortname
function kdescd([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl describe deployments/$(GetDeploymentAttribute $params "Name") -n $(GetDeploymentAttribute $params "Namespace")")
}

## Describe master node
function kdescn([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl describe node")
}

## Get pod using shortname and output to yaml
function kgpoy([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl get pods/$(GetPodAttribute $params "Name") -n $(GetPodAttribute $params "Namespace") --output=yaml")
}

## Get deployment using shortname and output to yaml
function kgdoy([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl get deployment/$(GetDeploymentAttribute $params "Name") -n $(GetDeploymentAttribute $params "Namespace") --output=yaml")
}

## Get service using shortname and output to yaml
function kgsoy([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl get service/$(GetServiceAttribute $params "Name") -n $(GetServiceAttribute $params "Namespace") --output=yaml")
}

## Get service using shortname and output to yaml
function kgooy() {
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $objectType,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $objectName
    )
    RunCommand("kubectl get $objectType/$(getObjectAttribute $objectName "Name" $objectType) -n $(getObjectAttribute $objectName "Namespace" $objectType) --output=yaml")
}

## Execute shell inside pod using shortname
function kshell([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl exec -it $(GetPodAttribute $params "Name") -n $(GetPodAttribute $params "Namespace") -- /bin/sh")
}

## Execute shell inside pod using shortname
function kshellc() {
    Param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $podName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $container
    )
    RunCommand("kubectl exec -it $(GetPodAttribute $podName "Name") -c $container -n $(GetPodAttribute $podName "Namespace") -- /bin/sh")
}

## Delete pod using shortname
function kdelp([Parameter(ValueFromRemainingArguments = $true)]$params) {
    RunCommand("kubectl delete pods/$(GetPodAttribute $params "Name") -n $(GetPodAttribute $params "Namespace")")
}

## Delete deployments in a specified namespace
function kdeld() {
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Deployment,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $Namespace
    )
    RunCommand("kubectl delete deployment/$Deployment -n $Namespace")
}

## Delete all objects belonging to a specific namespace
function kda([Parameter(ValueFromRemainingArguments = $true)]$params) { RunCommand("kubectl -n $params delete pod,svc,deployment,configmap,secret --all") }



# General Kubernetes Helper Functions #
function getObjectAttribute()
{
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $objectName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $objectAttribute,
        [Parameter(Mandatory = $true, Position = 2)]
        [string] $objectType
    )
    $getObjects =  $( &kubectl get $objectType -A -o jsonpath="{range .items[*]}{.metadata.name}{':'}{.metadata.namespace}{' '}{end}" )
    [string[]] $objects = $getObjects.Split(" ")
    $objectFullName = $null
    $objectNamespace = $null
    foreach ($obj in $objects){
        if($obj -like "*$objectName*"){
            $objectFullName,$objectNamespace = $obj.Split(":")
        }
    }
    if ($objectAttribute -eq "Name")
    {
        Return $objectFullName
    }
    elseif ($objectAttribute -eq "Namespace")
    {
        Return $objectNamespace
    }
}

function GetPodAttribute()
{
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $PodName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $PodAttribute
    )
    return getObjectAttribute $PodName $PodAttribute "pods"
}

function GetServiceAttribute()
{
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $ServiceName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $ServiceAttribute
    )
    return getObjectAttribute $ServiceName $ServiceAttribute "services"
}

function GetDeploymentAttribute()
{
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $DeploymentName,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $DeploymentAttribute
    )
    return getObjectAttribute $DeploymentName $DeploymentAttribute "deployments"
}

function CreateNamespaceIfNonExistent()
{
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $FilePath,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $Namespace
    )
    Write-Host "Checking if $Namespace exists..."
    [Hashtable]$Return = @{ }

    if ( [string]::IsNullOrWhiteSpace($( kubectl get namespace $Namespace --ignore-not-found=true )))
    {
        Write-Host "Namespace $Namespace doesn't exist, creating..."
        kubectl create -f $FilePath
    }
    else
    {
        Write-Host "Namespace already exists, skipping namespace creation"
    }
    return $Return
}

function DeleteNamespaceIfExists()
{
    Param
    (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $FilePath,
        [Parameter(Mandatory = $true, Position = 1)]
        [string] $Namespace
    )
    Write-Host "Checking if $Namespace exists..."
    [Hashtable]$Return = @{ }

    if ( ! [string]::IsNullOrWhiteSpace($( kubectl get namespace $Namespace --ignore-not-found=true )))
    {
        Write-Host "Namespace $Namespace exists, deleting..."
        kubectl delete -f $FilePath
    }
    else
    {
        Write-Host "Namespace doesn't exist, skipping namespace deletion"
    }
    return $Return
}

function RunCommand()
{
    Param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $cmd
    )

    Write-Host ">> $cmd"
    Invoke-Expression $cmd
}