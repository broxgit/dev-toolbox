from __future__ import print_function

import argparse
import time

from util_config import NAMESPACES, PVC_LIST

from kubernetes import client, config
from kubernetes.client.rest import ApiException

PV_TYPE_PVC = "PVC"
PV_TYPE_PV = "PV"


def log_title(msg):
    message = ' {} '.format(msg)
    print("\n\n----------------------------------------------------")
    print(message.center(52, '-'))
    print("----------------------------------------------------")


def get_node_hostname():
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


def get_all_pods():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def get_pod_information(pod_shortname):
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


def get_default_storage_class():
    config.load_kube_config()
    v1 = client.StorageV1Api()

    sc = v1.list_storage_class()
    for i in sc.items:
        if 'storageclass.kubernetes.io/is-default-class' in i.metadata.annotations:
            return i.metadata.name


def delete_persistent_data_objects_by_pvc_name(pvc_name):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pvc_found = False

    pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
    for i in pvcs.items:
        if pvc_name in i.metadata.name:
            pvc_found = True
            pvc_fqn = i.metadata.name
            namespace = i.metadata.namespace
            print("\n- Deleting PersistentVolumeClaim: \n- name: {}  \n- namespace: {}".format(pvc_fqn, namespace))
            v1.delete_namespaced_persistent_volume_claim(pvc_fqn, namespace)
            watch_persistent_data_object(PV_TYPE_PVC, name=pvc_fqn, namespace=namespace)

    if not pvc_found:
        print("- Persistent Volume Claim containing '{}' not found - no need to delete".format(pvc_name))

    pvs = v1.list_persistent_volume()

    pv_found = False

    for i in pvs.items:
        if pvc_name in i.spec.claim_ref.name:
            pv_found = True
            pv_fqn = i.metadata.name
            print("\n- Deleting PersistentVolume: \n- name: {}  \n- Bound PVC: {}".format(pv_fqn, i.spec.claim_ref.name))

            try:
                v1.delete_persistent_volume(pv_fqn)
            except ApiException as ae:
                # Often times deleting the PVC that is bound to the PV will automatically trigger the PV for deletion,
                # so our delete command might not succeed before that event happens
                if "Not Found" in ae.reason:
                    print("- PV was likely deleted when its bound PVC was removed.")
                else:
                    raise ae

            watch_persistent_data_object(PV_TYPE_PV, name=pv_fqn)

    if not pv_found:
        print("- No PVs that are bound to PVCs containing name: '{}' were found - no need to delete".format(pvc_name))


def delete_persistent_data_objects_by_namespace(namespace):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    print("- Checking namespace: '{}' for Persistent Volume Claims...".format(namespace))

    pvcs = v1.list_namespaced_persistent_volume_claim(namespace)
    if len(pvcs.items) < 1:
        print(" -- No Persistent Volume Claims were found in this namespace: {}\n".format(namespace))
    else:
        print(" -- Deleting all Persistent Volume Claims belonging to namespace: {}\n".format(namespace))
        v1.delete_collection_namespaced_persistent_volume_claim(namespace)


def watch_persistent_data_object(pv_type, **kwargs):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    count = 30
    metadata = ''

    if 'name' in kwargs:
        metadata += 'name={}'.format(kwargs['name'])
    if 'namespace' in kwargs:
        metadata += '  namespace={}'.format(kwargs['namespace'])

    print("Verifying {} was deleted".format(pv_type), end="")

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

    print("\nAn issue was encountered when attempting to delete {}  ({})".format(pv_type, metadata))


def check_for_persistent_data_objects():
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
        print("- No PersistentVolumes in cluster...")

    pvcs = v1.list_persistent_volume_claim_for_all_namespaces()

    if len(pvcs.items) > 0:
        print("\nThere are some PersistentVolumesClaims remaining:")
        for i in pvcs.items:
            pvc_name = i.metadata.name
            namespace = i.metadata.namespace
            print("\nPersistentVolumeClaim: \n- name: {}  \n- namespace: {}".format(pvc_name, namespace))
    else:
        print("- No PersistentVolumeClaims in cluster...")


def get_values_for_values_yaml():
    hostname = get_node_hostname()
    storageclass = get_default_storage_class()
    print("Use these in your values.yaml: ")
    print("- <>.<>.hostname: {}".format(hostname))
    print("- <>.<>.storageclass: {}".format(storageclass))


def cleanup_persistent_data():
    for pvc in PVC_LIST:
        log_title("Cleaning up {} Persistent Data".format(pvc))
        delete_persistent_data_objects_by_pvc_name(pvc)

    log_title("Checking Namespaces for Remaining PVCs")
    for ns in NAMESPACES:
        delete_persistent_data_objects_by_namespace(ns)

    log_title("Checking Cluster for PVs and PVCs")
    check_for_persistent_data_objects()

    print("\nCLEANUP COMPLETED\n")


def debug_pod(pod_shortname):
    pod_info = get_pod_information(pod_shortname)
    print('Pod Description: \n{}'.format(pod_info['pod']))
    print('\n\n\nPod Logs: \n{}'.format(pod_info['log']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="K8s Utility Script")

    parser.add_argument("--debugpod", help='Provide information about a pod using a portion of it\'s name')

    parser.add_argument("--cleanup", default=False, const=True,
                        nargs='?', help='Cleanup lingering persistent data objects')

    parser.add_argument("--listpods", default=False, const=True,
                        nargs='?', help='List all pods')

    parser.add_argument("--values", default=False, const=True,
                        nargs='?', help='Get dynamic values needed for values.yaml')

    args = parser.parse_args()

    if args.cleanup:
        cleanup_persistent_data()
    elif args.listpods:
        get_all_pods()
    elif args.values:
        get_values_for_values_yaml()
    elif args.debugpod:
        debug_pod(args.debugpod)
