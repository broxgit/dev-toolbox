# Certificate Service in GoLang      

## Running in Docker
Within the root of the cert-service directory, run the following commands: 
### Build the Go Binary:
1. Create an environment variable for Go which will allow Windows users to build binaries for the Linux architecture: `GOOS=linux`
2.  **go build -o cert-service**

### Run the Docker Commands:
1. **docker build -t cert-service .**
2. **docker run -p 3000:3000 cert-service** 

## Current Features / Endpoints:
- **/cert/create/ca**: Create a Certificate Authority
- **/cert/create/client**: Create a Client Certificate
- **/cert/sign/csr/\<caId\>**: Sign a CSR with a generated CA
- **/cert/file/sign/csr/\<caId\>**: Sign a CSR with a generated CA using a CSR file
- **/cert/sign/\<caId\>/\<certId\>**: Sign a generated client certificate with a generated CA
- **/cert/download/\<certId\>**: Download a generated certificate
- **/cert/upload/cert**: Upload a certificate to memory
- **/cert/upload/cert-key**: Upload a certificate and private key to memory

## Generating Certs- Python Script:
We have included a _**test.py**_ script that can be used to create a CA, sign a CSR, and download the resulting client certificate, the CA cert, and CA private key.

Put this script wherever you want it and change the **CSR_FILE_LOCATION** and **CERTS_OUTPUT_DIR** variables to match your specific environment.

1. Export your CSR in your application and save it in your **CSR_FILE_LOCATION**
2. Run the script, the resulting files will be downloaded in your **CERTS_OUTPUT_DIR**
    - caCert.pem: CA Certificate
    - client.pem: Client Certificate (CSR signed with generated CA)
    - privKey.key: CA Private Key 

## Generating Certs - Manual Process:
1. Export your CSR in your application
2. Create a Certificate Authority Certificate with the following REST call:    
    - POST: http://localhost:3000/cert/create/ca
    - Payload: 
        ```json
        {
            "organizationalUnit": "<Your OU>",
            "organization": "<Your Organization>",
            "country": "<Country>",
            "state": "<State/Province>",
            "city": "<City>",
            "streetAddress": "<Street Address>",
            "postalCode": "<Zip/Postal Code>",
            "CN": "<CN/Hostname>",
            "SANS": ["<SAN-1>", "<SAN-2>"]
        }
        ```
        _The Response will contain the ID of the CA that was created (<CA-ID>), this will be used in subsequent REST calls._
3. Send the CSR to the Certificate Service to get a signed client certificate using the CA generated in Step 1 with the following REST call:
    - POST: http://localhost:3000/cert/sign/csr/<CA-ID>
    - Payload: 
         ```json
        {
            "csrData" : "-----BEGIN CERTIFICATE REQUEST-----\n<CERT DATA>\n-----END CERTIFICATE REQUEST-----\n"
        }
         ```    
        _The REST call will return a response body containing the certificate data, this should be stored in a *.pem file format._
    
4. Download the CA Certificate:
    - GET: http://localhost:3000/cert/download/<CA-ID>  
    
        _The REST call will return a zip file containing CA Certificate and the CA Private Key_    
