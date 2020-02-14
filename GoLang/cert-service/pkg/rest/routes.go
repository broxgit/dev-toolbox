package rest

import (
	"archive/zip"
	"cert-manager/pkg/cert"
	"crypto/x509"
	"encoding/pem"
	"github.com/gin-gonic/gin"
	"io/ioutil"
	"log"
	"strconv"
	"errors"
	"net/http"
)

func handleError(c *gin.Context, err error) {
	log.Println(err.Error())
	c.JSON(500, gin.H{"message": err.Error()})
}

// This handles creating a Certificate Authority
func CreateCAHandler(c *gin.Context) {
	certInfo := cert.CertInfo{}
	err := c.BindJSON(&certInfo)
	if err != nil {
		log.Println("could not parse json")
		handleError(c, err)
		return
	}

	// Get pem and key from cert.go
	caId, err := cert.GenerateRootCertificate(certInfo)
	if err != nil {
		log.Println("could not generate cert")
		handleError(c, err)
		return
	}
	c.JSON(http.StatusOK, gin.H{"id": caId})
}

func DownloadCACertHandler(c *gin.Context) {
	certId, err := strconv.Atoi(c.Param("certId"))
	if err != nil {
		log.Println("could not parse certId provided")
		handleError(c, err)
	}

	pemB, err := cert.GetSignedRootCertificate(certId)
	if err != nil {
		log.Println("could not get signed cert")
		handleError(c, err)
		return
	}
	keyB, err := cert.GetCertificatePrivateKey(certId)
	if err != nil {
		handleError(c, err)
		return
	}

	// create zip to return certs in
	zipWriter := zip.NewWriter(c.Writer)
	certFile, err := zipWriter.Create("caCert.pem")
	if err != nil {
		log.Println("could not open zip file")
		handleError(c, err)
		return
	}
	pem.Encode(certFile, pemB)

	privKeyFile, err := zipWriter.Create("privKey.key")
	if err != nil {
		log.Println("could not open zip file")
		handleError(c, err)
		return
	}
	pem.Encode(privKeyFile, keyB)

	zipWriter.Close()
}

// This will handle creating a client certificate
func CreateClientCertHandler(c *gin.Context) {
	certInfo := cert.CertInfo{}
	err := c.BindJSON(&certInfo)
	if err != nil {
		log.Println("could not parse json")
		handleError(c, err)
		return
	}

	// Get pem and key from cert.go
	caId, err := cert.GenerateCertificate(certInfo)
	if err != nil {
		log.Println("could not generate cert")
		handleError(c, err)
		return
	}
	c.JSON(http.StatusOK, gin.H{"id": caId})

}

func SignCSRFileHandler(c *gin.Context) {
	caId, err := strconv.Atoi(c.Param("caId"))
	if err != nil {
		log.Println("could not parse caId provided")
		handleError(c, err)
	}

	csr, csrErr := c.FormFile("csr")
	if csrErr != nil {
		handleError(c, csrErr)
	}

	csrOut, _ := csr.Open()
	csrByte, _ := ioutil.ReadAll(csrOut)
	csrBlock, _ := pem.Decode(csrByte)

	clientCSR, _ := x509.ParseCertificateRequest(csrBlock.Bytes)

	csrClient, certErr := cert.GenerateClientCertFromCSR(*clientCSR, caId)
	if certErr != nil {
		log.Println("could not generate certificate from CSR")
		handleError(c, certErr)
	}
	pem.Encode(c.Writer, csrClient)

}

func SignCSRHandler(c *gin.Context) {
	caId, err := strconv.Atoi(c.Param("caId"))
	if err != nil {
		log.Println("could not parse caId provided")
		handleError(c, err)
		return
	}

	type CsrJson struct {
		CsrData string
	}
	csrData := CsrJson{}

	csrErr := c.BindJSON(&csrData)
	if csrErr != nil {
		handleError(c, csrErr)
		return
	}

	csrBlock, _ := pem.Decode([]byte(csrData.CsrData))
	if csrBlock == nil {
		handleError(c, errors.New("could not decode csr"))
		return
	}
	clientCSR, _ := x509.ParseCertificateRequest(csrBlock.Bytes)
	if clientCSR == nil {
		handleError(c, errors.New("could not decode csr"))
		return
	}

	csrClient, certErr := cert.GenerateClientCertFromCSR(*clientCSR, caId)
	if certErr != nil {
		log.Println("could not generate certificate from CSR")
		handleError(c, certErr)
		return
	}
	pem.Encode(c.Writer, csrClient)

}

// This handles signing a client certificate with the default CA (generated internally)
func SignClientCertWithCAHandler(c *gin.Context) {
	caId, err := strconv.Atoi(c.Param("caId"))
	if err != nil {
		log.Println("could not parse caId provided")
		handleError(c, err)
	}
	certId, err := strconv.Atoi(c.Param("certId"))
	if err != nil {
		log.Println("could not parse certId provided")
		handleError(c, err)
	}
	newCert, err := cert.SignClientCertificate(caId, certId)
	if err != nil {
		log.Println("could not sign certificate")
		handleError(c, err)
	}
	pem.Encode(c.Writer, newCert)
}

func UploadCertHandler(c *gin.Context) {
	UploadKeyAndCertHandler(c)
}

func UploadKeyAndCertHandler(c *gin.Context) {
	type CertJson struct {
		CertData string
		KeyData  string
	}

	certKeyData := cert.CertKeyData{}

	jsonData := CertJson{}
	jsonErr := c.BindJSON(&jsonData)
	if jsonErr != nil {
		handleError(c, jsonErr)
		return
	}

	certBlock, _ := pem.Decode([]byte(jsonData.CertData))
	if certBlock == nil {
		handleError(c, errors.New("could not decode pem certificate"))
		return
	}
	x509Cert, _ := x509.ParseCertificate(certBlock.Bytes)
	if x509Cert == nil {
		handleError(c, errors.New("could not decode certdata"))
		return
	}
	certKeyData.CertData = x509Cert

	keyBlock, _ := pem.Decode([]byte(jsonData.KeyData))
	if keyBlock == nil {
		handleError(c, errors.New("could not decode pem key"))
		return
	}
	x509Key, _ := x509.ParsePKCS1PrivateKey(keyBlock.Bytes)
	if x509Key == nil {
		handleError(c, errors.New("could not decode private key"))
		return
	}
	certKeyData.KeyData = x509Key

	certIdx, err := cert.CacheUserCertificateAndKey(certKeyData)
	if err != nil {
		handleError(c, errors.New("could not decode private key"))
		return
	}

	c.JSON(http.StatusOK, gin.H{"id": certIdx})
}

func GetAllCerts(c *gin.Context) {
	vals := cert.GetAllCertRefs()
	c.Header("Access-Control-Allow-Origin", "*")
	c.JSON(http.StatusOK, gin.H{"certs": vals})
}

func GetCertJson(c *gin.Context) {
	c.Header("Access-Control-Allow-Origin", "*")
	certId, err := strconv.Atoi(c.Param("certId"))
	if err != nil {
		log.Println("could not parse certId provided")
		handleError(c, err)
		return
	}
	certInfo, err := cert.GetCertJson(certId)
	if err != nil {
		handleError(c, err)
		return
	}
	c.JSON(http.StatusOK, certInfo)
}
//func UploadKeyHandler(c *gin.Context) {
//	UploadKeyAndCertHandler(c)
//}
