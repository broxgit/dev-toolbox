#!/usr/bin/python
from __future__ import print_function
from argparse import RawTextHelpFormatter

import re
from inspect import getmembers, isfunction

import argparse
import time
import os

import psycopg2
from kubernetes import client, config
from kubernetes.client.rest import ApiException

PV_TYPE_PVC = "PVC"
PV_TYPE_PV = "PV"

"""
--------------------------
  USER-DEFINED VARIABLES 
--------------------------    
"""

# Provide a list of your namespaces
# These values will be used when invoking the --cleanup command
NAMESPACES = [
    'logging',
    'frontend',
    'backend'
]

# Provide a list of your PVCs that need extra cleanup
# These values will be used when invoking the --cleanup and --nuke commands
PVC_LIST = [
    'consul',
    'postgres'
]

# Provide a list of your Helm Charts and their related namespaces
# These values will be used when invoking the --nuke argument
HELM_CHARTS = {
    'main': ['frontend', 'backend', 'logging'],
    'auxiliary': ['auxiliary-providers']
}

""" 
--------------------------
    UTILITY FUNCTIONS 
--------------------------    
"""


def log_title(msg):
    """
    Utility function for pretty-printing a message to the user
    :param msg: the message to encapsulate and pretty-print
    """
    message = ' {} '.format(msg)
    print("\n\n----------------------------------------------------")
    print(message.center(52, '-'))
    print("----------------------------------------------------")


def get_env_variable(env_var):
    """
    Gets the environment variable value from the OS if it exists
    :param env_var: Environment Variable Key
    :return: Environment Variable Value
    """
    env_variables = os.environ
    if not env_var in env_variables:
        return None
    else:
        return env_variables[env_var]


def get_env_var_or_default(default, *env_var):
    """
    Gets the environment variable using the key(s) provided,
    if an environment variable doesn't exist using those keys, the default value is returned
    :param default: the default value to use if the environment variable doesn't exist
    :param env_var: Environment Variable Key
    :return: Environment Variable Value or Default
    """
    val = None
    for ev in env_var:
        val = get_env_variable(ev)
        if val:
            # print("{} set to {} in user's environment variables, using this value".format(ev, val))
            return val
    if not val:
        # print("{} not set in user's environment variables, using default value.".format(env_var))
        return default


def get_all_k8s_list_namespaced_functions():
    """
    Iterates through the entire Kubernetes Python Client and grabs all
    functions that contain 'list_namespaced' in their name
    """
    list_functions = []

    for i in dir(client):
        m = globals()['client']
        f = getattr(m, i)
        members = getmembers(f)
        for ob in members:
            fu = ob[1]
            if isfunction(fu):
                name = fu.__name__
                if re.match(r'list_namespaced_.*', name):
                    if 'http_info' not in name:
                        list_functions.append(fu)

    for lf in list_functions:
        print("{} -- {}".format(lf.__name__, lf.__module__))


""" 
--------------------------
      POD FUNCTIONS 
--------------------------    
"""


def get_pod_name_namespace(pod_shortname):
    """
    Gets the fully qualified name and namespace of a Pod using any unique portion of a pod name
    :param pod_shortname: any unqiue portion of a pod name (i.e. 'consul')
    :return: fully qualified name and namespace of a Pod
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False)

    pod_fqn = None
    pod_namespace = None

    for i in ret.items:
        if pod_shortname in i.metadata.name:
            pod_fqn = i.metadata.name
            pod_namespace = i.metadata.namespace
            break

    if not pod_fqn:
        print("Pod fully qualified name could not be found using provided shortname.")

    if not pod_namespace:
        print("Pod namespace could not be found using provided shortname.")

    return pod_fqn, pod_namespace


def get_all_pods():
    """
    Retrieves all pods in a cluster and prints the results with their respective IP addresses
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def get_pod_information(pod_shortname):
    """
    Gets pod logs and 'describe'
    :param pod_shortname: any unique portion of a pod name (i.e. 'consul')
    :return: dictionary containing pod 'describe' and logs
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pod_fqn, pod_namespace = get_pod_name_namespace(pod_shortname)

    if not pod_fqn or not pod_namespace:
        print("Pod with name containing '{}' was not found, exiting...".format(pod_shortname))
        return

    pod = v1.read_namespaced_pod(pod_fqn, pod_namespace, pretty=True)

    container = pod_fqn

    if len(pod.spec.containers) > 1:
        for c in pod.spec.containers:
            if ('audit' not in c.name) and ('debug' not in c.name) and ('sidecar' not in c.name):
                container = c.name
                break

    log = v1.read_namespaced_pod_log(pod_fqn, pod_namespace, container=container, limit_bytes='5000000')

    pod_details = {
        'pod': pod,
        'log': log
    }

    return pod_details


""" 
--------------------------
    STORAGE FUNCTIONS
--------------------------    
"""


def delete_persistent_data_objects_by_pvc_name(pvc_name):
    """
    Delete PVCs and their related PVs using a unique portion of the PVC name
    :param pvc_name: a unique portion of the PVC name (i.e. 'consul')
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pvc_found = False

    pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
    for i in pvcs.items:
        if pvc_name in i.metadata.name:
            pvc_found = True
            pvc_fqn = i.metadata.name
            namespace = i.metadata.namespace
            print("Deleting PersistentVolumeClaim: \n- name: {}  \n- namespace: {}".format(pvc_fqn, namespace))
            v1.delete_namespaced_persistent_volume_claim(pvc_fqn, namespace)
            verify_persistent_data_object_deletion(PV_TYPE_PVC, name=pvc_fqn, namespace=namespace)

    if not pvc_found:
        print("Persistent Volume Claim containing '{}' not found - no need to delete".format(pvc_name))

    pvs = v1.list_persistent_volume()

    pv_found = False

    print("\nChecking for PVs that are bound to this PVC...")
    for i in pvs.items:
        if pvc_name in i.spec.claim_ref.name:
            pv_found = True
            pv_fqn = i.metadata.name
            print("- PV")
            print(
                "Deleting PersistentVolume: \n- name: {}  \n- Bound PVC: {}".format(pv_fqn, i.spec.claim_ref.name))

            try:
                v1.delete_persistent_volume(pv_fqn)
            except ApiException as ae:
                # Often times deleting the PVC that is bound to the PV will automatically trigger the PV for deletion,
                # so our delete command might not succeed before that event happens
                if "Not Found" in ae.reason:
                    print("- PV was likely deleted when its bound PVC was removed.")
                else:
                    raise ae

            verify_persistent_data_object_deletion(PV_TYPE_PV, name=pv_fqn)

    if not pv_found:
        print("- No PVs that are bound to PVCs containing name: '{}' were found - no need to delete".format(pvc_name))


def get_persistent_data_objects_by_namespace(namespace):
    """
    Gets any and all PVs/PVCs in the specified namespace
    :param namespace: the namespace containing the PVs and PVCs
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()
    print("Checking namespace: '{}' for Persistent Volume Claims...".format(namespace))

    pvcs = v1.list_namespaced_persistent_volume_claim(namespace)
    if len(pvcs.items) < 1:
        print("- No Persistent Volume Claims were found in this namespace: {}\n".format(namespace))
        return None
    else:
        return pvcs


def delete_persistent_data_objects_by_namespace(namespace):
    """
    Deletes any and all PVs/PVCs in the specified namespace
    :param namespace: the namespace containing the PVs and PVCs to delete
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pvcs = get_persistent_data_objects_by_namespace(namespace)

    if pvcs:
        print("- Deleting all Persistent Volume Claims belonging to namespace: {}\n".format(namespace))
        for pvc in pvcs.items:
            delete_persistent_data_objects_by_pvc_name(pvc.metadata.name)


def verify_persistent_data_object_deletion(pv_type, **kwargs):
    """
    Watches a particular PV or PVC for 30 seconds to verify it was deleted
    :param pv_type: PV or PVC
    :param kwargs: name (and namespace for PVCs)
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    count = 30
    metadata = ''

    if 'name' in kwargs:
        metadata += 'name={}'.format(kwargs['name'])
    if 'namespace' in kwargs:
        metadata += '  namespace={}'.format(kwargs['namespace'])

    print("\nVerifying {} was deleted".format(pv_type), end="")

    for i in range(0, count):
        print(".", end="")
        try:
            if pv_type == PV_TYPE_PV:
                v1.read_persistent_volume(**kwargs)
            elif pv_type == PV_TYPE_PVC:
                v1.read_namespaced_persistent_volume_claim(**kwargs)
        except ApiException as ae:
            if "Not Found" in ae.reason:
                print("\n- {} ({}) successfully deleted.".format(pv_type, metadata))
                return
        time.sleep(1)

    print("\n- Error: An issue was encountered when attempting to delete {}  ({})".format(pv_type, metadata))


def check_for_persistent_data_objects():
    """
    Checks for the existence of PersistentVolumes and PersistentVolumeClaims in the cluster
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pvs = v1.list_persistent_volume()
    if len(pvs.items) > 0:
        print("\nThere are some PersistentVolumes remaining:")
        for i in pvs.items:
            name = i.metadata.name
            bound_pvc = i.spec.claim_ref.name
            print("\nPersistentVolume: \n- name: {}  \n- Bound PVC: {}".format(name, bound_pvc))
    else:
        print("No PersistentVolumes in cluster...")

    pvcs = v1.list_persistent_volume_claim_for_all_namespaces()

    if len(pvcs.items) > 0:
        print("\nThere are some PersistentVolumesClaims remaining:")
        for i in pvcs.items:
            pvc_name = i.metadata.name
            namespace = i.metadata.namespace
            print("\nPersistentVolumeClaim: \n- name: {}  \n- namespace: {}".format(pvc_name, namespace))
    else:
        print("No PersistentVolumeClaims in cluster...")


"""
--------------------------    
   NAMESPACE FUNCTIONS 
--------------------------    
"""


def get_all_items_in_namespace(namespace):
    """
    Gets all Kubernetes API Objects related to the specified namespace
    :param namespace: the namespace to query for K8s objects
    :return: a dictionary of all items
    """
    config.load_kube_config()
    core_v1_api = client.CoreV1Api()
    apps_v1_api = client.AppsV1Api()
    rbac_v1_api = client.RbacAuthorizationV1Api()
    nets_v1_api = client.NetworkingV1beta1Api()
    jobs_v1_api = client.BatchV1Api()
    cjob_v1_api = client.BatchV1beta1Api()

    core_v1 = {}
    apps_v1 = {}
    rbac_v1 = {}
    nets_v1 = {}
    jobs_v1 = {}

    k8s_obj_list = [core_v1, apps_v1, rbac_v1, nets_v1, jobs_v1]

    try:
        ns = core_v1_api.read_namespace(namespace)
    except ApiException:
        print("Namespace '{}' not found! Exiting script.".format(namespace))
        return
    if ns.status:
        status = ns.status
        # Verify that namespace status is active
        if 'active' in status.phase.lower():
            core_v1['configMaps'] = core_v1_api.list_namespaced_config_map(namespace)
            core_v1['endpoints'] = core_v1_api.list_namespaced_endpoints(namespace)
            core_v1['persistentVolumeClaims'] = core_v1_api.list_namespaced_persistent_volume_claim(namespace)
            core_v1['pods'] = core_v1_api.list_namespaced_pod(namespace)
            core_v1['podTemplates'] = core_v1_api.list_namespaced_pod_template(namespace)
            core_v1['replicationControllers'] = core_v1_api.list_namespaced_replication_controller(namespace)
            core_v1['resourceQuotas'] = core_v1_api.list_namespaced_resource_quota(namespace)
            core_v1['secrets'] = core_v1_api.list_namespaced_secret(namespace)
            core_v1['serviceAccounts'] = core_v1_api.list_namespaced_service_account(namespace)
            core_v1['services'] = core_v1_api.list_namespaced_service(namespace)

            apps_v1['controllerRevisions'] = apps_v1_api.list_namespaced_controller_revision(namespace)
            apps_v1['daemonSets'] = apps_v1_api.list_namespaced_daemon_set(namespace)
            apps_v1['deployments'] = apps_v1_api.list_namespaced_deployment(namespace)
            apps_v1['replicaSets'] = apps_v1_api.list_namespaced_replica_set(namespace)
            apps_v1['statefulSets'] = apps_v1_api.list_namespaced_stateful_set(namespace)

            rbac_v1['roles'] = rbac_v1_api.list_namespaced_role(namespace)
            rbac_v1['roleBindings'] = rbac_v1_api.list_namespaced_role_binding(namespace)

            nets_v1['ingresses'] = nets_v1_api.list_namespaced_ingress(namespace)

            jobs_v1['jobs'] = jobs_v1_api.list_namespaced_job(namespace)
            jobs_v1['cronJobs'] = cjob_v1_api.list_namespaced_cron_job(namespace)

        else:
            print("Expected namespace status to be active, instead status is '{}', exiting script.".format(status))
            return
    else:
        print("An error occurred when reading the namespace '{}'. "
              "Namespace does not contain a status field. Exiting script.".format(namespace))
        return

    return k8s_obj_list


"""
--------------------------    
    SERVICE FUNCTIONS 
--------------------------    
"""


def get_service_name_namespace(service_shortname):
    """
    Gets the name and namespace of a service containing the service shortname
    :param service_shortname: a unique portion of the service name
    :return: the service's name and namespace
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    name = None
    namespace = None

    services = v1.list_service_for_all_namespaces()
    for i in services.items:
        if service_shortname.lower() in i.metadata.name.lower():
            name = i.metadata.name
            namespace = i.metadata.namespace

    if not name or not namespace:
        print("Service matching the shortname '{}' could not be found!".format(service_shortname))

    return name, namespace


def get_service_object(service_shortname):
    """
    Get the service object whose name contains the service_shortname provided
    :param service_shortname: a unique portion of the service name
    :return: a Kubernetes Service Object
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()
    name, namespace = get_service_name_namespace(service_shortname)

    return v1.read_namespaced_service(name, namespace)


def get_service_port(service_shortname):
    """
    Get the port for a service using a unique portion of the service name
    :param service_shortname: a unique portion of the service name
    :return: the node port number
    """
    try:
        service = get_service_object(service_shortname)
        port = service.spec.ports[0].node_port
    except Exception as e:
        print("Exception encountered when trying to get service port: [{}]".format(e))
        return

    return port


"""
--------------------------    
    MISC K8S FUNCTIONS 
--------------------------    
"""


def get_node_hostname():
    """
    Gets the hostname of the master node
    :return: hostname of the master node
    """
    volumes_hostname = ""

    config.load_kube_config()
    v1 = client.CoreV1Api()
    kobj = v1.list_node()

    if len(kobj.items) == 1:
        volumes_hostname = kobj.items[0].metadata.name
    else:
        for i in kobj.items:
            for l in i.metadata.labels:
                if "master" in str(l):
                    volumes_hostname = i.metadata.name
    return volumes_hostname


def get_default_storage_class():
    """
    Gets the default storage class of the cluster
    :return: the default storage class of the cluster
    """
    config.load_kube_config()
    v1 = client.StorageV1Api()

    sc = v1.list_storage_class()
    for i in sc.items:
        if 'storageclass.kubernetes.io/is-default-class' in i.metadata.annotations:
            return i.metadata.name


def clear_pg_database():
    """
    This will clear a Postgres Database (if exists in the namespace) of all data while retaining the tables and databases
    """
    print("- Cleaning up Postgres Database...")
    host = get_env_var_or_default('localhost', 'PGHOST', 'PGHOSTADDR')
    database = get_env_var_or_default('postgres', 'PGDATABASE')
    username = get_env_var_or_default('postgres', 'POSTGRES_USER', 'PGUSER')
    password = get_env_var_or_default('postgres', 'POSTGRES_PASSWORD', 'PGPASSWORD')

    port = None
    try:
        svc_port = get_service_port('postgres')
        if svc_port:
            port = svc_port
    except Exception as e:
        print("Couldn't get Postgres service port due to exception:  {},  using default port".format(e))
        port = None
    if not port:
        port = get_env_var_or_default('PGPORT', 5432)

    try:
        conn = psycopg2.connect(host=host, port=port, database=database, user=username, password=password)
    except psycopg2.OperationalError as oe:
        print("Error: Couldn't connect to Postgres database due to exception:  {}".format(oe.pgerror))
        return

    cursor = conn.cursor()
    statement = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    cursor.execute(statement)

    print("\nDeleting all data from all tables in the database")

    for table in cursor.fetchall():
        try:
            statement = "DELETE FROM {}".format(table[0])
            print("- Deleting all table data in table: {}".format(table[0]))
            print("-- SQL Statement: '{}'\n".format(statement))
            cursor.execute(statement)
        except Exception as e:
            print("Could not delete table data in table: '{}' due to exception:  {}".format(table, e))
            return

    # conn = psycopg2.connect(host=host, port=port, user=username, password=password)
    # conn.set_isolation_level(0)
    # cursor = conn.cursor()
    #
    # try:
    #     print("Deleting '{}' Database from Postgres...".format(database))
    #     cursor.execute("DROP DATABASE {}".format(database)
    # except Exception as e:
    #     print("Could not drop '{}' database due to exception:  {}".format(database, e))
    #     return

    print("Postgres operations completed successfully")


"""
--------------------------    
     SCRIPT FUNCTIONS 
--------------------------    
"""


def get_values_for_values_yaml():
    """
    Gets the 'dynamic' values for the values.yaml
    """
    hostname = get_node_hostname()
    storageclass = get_default_storage_class()
    print("Use these in your values.yaml: ")
    print("- hostname: {}".format(hostname))
    print("- storageclass: {}".format(storageclass))


def cleanup_persistent_data():
    """
    Deletes all PersistentVolumes and PersistentVolumeClaims as defined in the PVC_LIST variable
    Checks the cluster for any other PVs or PVCs and prints the result
    """
    for pvc in PVC_LIST:
        log_title("Cleaning up {} Persistent Data".format(pvc.capitalize()))
        delete_persistent_data_objects_by_pvc_name(pvc)

    log_title("Checking Namespaces for Remaining PVCs")
    global NAMESPACES
    for ns in NAMESPACES:
        delete_persistent_data_objects_by_namespace(ns)

    log_title("Checking Cluster for PVs and PVCs")
    check_for_persistent_data_objects()

    log_title("CLEANUP COMPLETED")


def debug_pod(pod_shortname):
    """
    Gets the logs and the 'describe' for a pod using any unique part of the pod name (i.e. 'consul')
    :param pod_shortname: any unique portion of a pod name
    """
    pod_info = get_pod_information(pod_shortname)
    print('Pod Description: \n{}'.format(pod_info['pod']))
    print('\n\n\nPod Logs: \n{}'.format(pod_info['log']))


def print_all_objects_belonging_to_namespace(namespace):
    """
    Prints the names and types of all K8s objects belonging to a namespace
    :param namespace: namespace to search
    """
    k8s_obj_list = get_all_items_in_namespace(namespace)

    for o in k8s_obj_list:
        for k in o:
            obj = o[k]
            if len(obj.items) > 0:
                print("\n--- {} in {} ---".format(k.capitalize(), namespace))
                for item in obj.items:
                    print("- {}".format(item.metadata.name))


def nuke(helm_chart):
    """
    Attempts to delete ALL data and objects relating to a Helm Chart and its namespaces, including any Postgres data
    :param helm_chart: the name of the Helm chart to nuke
    """
    # Check for Postgres
    log_title("Postgres Check")
    s_name, s_namespace = get_service_name_namespace('postgres')
    print("Checking if Postgres exists in Helm Chart...")
    if s_name and s_namespace:
        if s_namespace in HELM_CHARTS[helm_chart]:
            clear_pg_database()

    # Run Helm Delete
    log_title("Deleting Helm Chart: '{}'".format(helm_chart))
    command = 'helm delete {} --purge'.format(helm_chart)
    os.system(command)

    # Remove all user defined namespaces from the NAMESPACES list in order to use the cleanup_persistent_data() function
    global NAMESPACES
    del NAMESPACES[:]

    for namespace in HELM_CHARTS[helm_chart]:
        NAMESPACES.append(namespace)

    cleanup_persistent_data()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="K8s Utility Script",
                                     formatter_class=RawTextHelpFormatter)

    pg = parser.add_mutually_exclusive_group()

    pg.add_argument("--cleanup", action='store_true',
                        help='Cleanup lingering persistent data objects')

    pg.add_argument("--listpods", action='store_true',
                        help='List all pods')

    pg.add_argument("--values", action='store_true',
                        help='Get dynamic values needed for values.yaml')

    pg.add_argument("--debugpod", metavar="POD_SHORTNAME",
                        help='Provide information about a pod using a portion of it\'s name')

    pg.add_argument("--nsobjects", metavar="NAMESPACE",
                    help="Get ALL objects belonging to the specified namespace")

    pg.add_argument("--nuke", metavar="HELM_CHART",
                        help="Perform a Helm Delete on the specified chart, remove all PVs/PVCs, "
                             "and remove any lingering objects belonging to the related namespaces")

    args = parser.parse_args()

    if args.cleanup:
        cleanup_persistent_data()
    elif args.listpods:
        get_all_pods()
    elif args.values:
        get_values_for_values_yaml()
    elif args.debugpod:
        debug_pod(args.debugpod)
    elif args.nsobjects:
        print_all_objects_belonging_to_namespace(args.nsobjects)
    elif args.nuke:
        nuke(args.nuke)
