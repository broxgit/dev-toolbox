import requests
import zipfile
import io

CSR_FILE_LOCATION = "test.csr"
CERTS_OUTPUT_DIR = "test/generated_certs/"


data = {
    "organizationalUnit": "Brock",
    "organization": "Brock GitHub",
    "country": "US",
    "state": "Utah",
    "city": "Salt Lake City",
    "streetAddress": "123 Fake Street",
    "postalCode": "84121",
    "CN": "brock-github.com"
}

print("Creating Certificate Authority...")
res = requests.post('http://localhost:3000/cert/create/ca', json=data)
print("Certificate Authority Created!")

caId = res.json()['id']

# print('ca id', caId)

# res = requests.post('http://localhost:3000/cert/create/client', json=data)
# clientId = res.json()['id']

# print('ca', caId, 'client', clientId)

# res = requests.get('http://localhost:3000/cert/sign/{}/{}'.format(caId, clientId))
# print(res.text)

print("Signing CSR with CA...")
with open('{}'.format(CSR_FILE_LOCATION)) as csr_file:
    res = requests.post('http://localhost:3000/cert/file/sign/csr/{}'.format(caId), files={'csr': csr_file})
    with open('{}/client.pem'.format(CERTS_OUTPUT_DIR),  'bw+') as certfile:
        certfile.write(res.content)
print("Client Cert generated from CSR!")

print("CSR signed with CA Cert!")

ca_download = "http://127.0.0.1:3000/cert/download/{}".format(caId)

r = requests.get(ca_download)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("{}".format(CERTS_OUTPUT_DIR))

print("Client Cert is located at: test/generated_certs/client.pem")
print("CA Cert is located at: test/generated_certs/caCert.pem")
print("CA Key is located at: test/generated_certs/privKey.key")

