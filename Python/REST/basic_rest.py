import json

import requests

HTTP_GET = "GET"
HTTP_POST = "POST"
HTTP_PUT = "PUT"
HTTP_DELETE = "DELETE"
HTTP_PATCH = "PATCH"

HTTP_ACTIONS = {HTTP_GET, HTTP_POST, HTTP_PUT, HTTP_DELETE, HTTP_PATCH}


def do_rest(url, http_method, verbose=False, params=None, payload=None, headers=None, ca_verify=False):
    payload = json.dumps(payload)

    if verbose:
        print("URL: {}".format(url))
        print("\nHeaders: \n{}".format(json.dumps(headers, indent=4)))
        print("\nPayload: \n{}".format(json.dumps(json.loads(payload), indent=4)))

    if ca_verify:
        verify = 'cacert.pem'
    else:
        verify = False
        requests.packages.urllib3.disable_warnings()

    response = None
    if http_method == HTTP_GET:
        response = requests.get(url=url, headers=headers, params=params, verify=verify)
    elif http_method == HTTP_POST:
        response = requests.post(url=url, data=payload, headers=headers, params=params, verify=verify, cookies=None)
    elif http_method == HTTP_PUT:
        response = requests.put(url=url, data=payload, headers=headers, params=params, verify=verify)
    elif http_method == HTTP_DELETE:
        response = requests.delete(url=url, headers=headers, params=params, verify=verify)
    elif http_method == HTTP_PATCH:
        response = requests.patch(url=url, data=payload, headers=headers, params=params, verify=verify)

    content = json.loads(response.content)
    formatted_content = json.dumps(content, indent=4)

    if verbose:
        print("\nResponse Status/Reason: {} / {}".format(response.status_code, response.reason))
        print("\nResponse Body:")
        print(formatted_content)

    return response


def rest_get(url, params=None, headers=None):
    return do_rest(url, HTTP_GET, params=params, headers=headers)


def rest_post(url, payload, params=None, headers=None):
    return do_rest(url, HTTP_POST, params, payload, headers)


def rest_put(url, payload, params=None, headers=None):
    return do_rest(url, HTTP_PUT, params, payload, headers)


def rest_delete(url, params=None, headers=None):
    return do_rest(url, HTTP_DELETE, params=params, headers=headers)


def rest_patch(url, params=None, headers=None):
    return do_rest(url, HTTP_PATCH, params=params, headers=headers)
