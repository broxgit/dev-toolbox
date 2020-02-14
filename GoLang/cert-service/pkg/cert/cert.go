package cert

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"time"
	"errors"
)

func init() {
	cacheCert = make(map[int]*x509.Certificate)
	cacheKey = make(map[int]*rsa.PrivateKey)
	certIndex = 1
}

var cacheCert map[int]*x509.Certificate
var cacheKey map[int]*rsa.PrivateKey
var certIndex int

type CertInfo struct {
	OrganizationalUnit string
	Organization       string
	Country            string
	State              string
	City               string
	StreetAddress      string
	PostalCode         string
	Sans               []string
	CommonName         string `json:"CN"`
}

type CertKeyData struct {
	CertData *x509.Certificate
	KeyData  *rsa.PrivateKey
}

func getCertificateFromCache(index int) (CertKeyData, error) {
	cert, found := cacheCert[index]
	if !found {
		return CertKeyData{}, errors.New("cert not found in cache")
	}
	key, found := cacheKey[index]
	if !found {
		return CertKeyData{}, errors.New("key not found in cache")
	}
	return CertKeyData{cert, key}, nil
}

func saveCertificateToCache(data CertKeyData) (int, error) {
	cacheCert[certIndex] = data.CertData
	cacheKey[certIndex] = data.KeyData
	certIndex += 1

	return certIndex - 1, nil
}

func GetAllCertRefs() []map[string]interface{} {
	out := make([]map[string]interface{}, 0)
	for key, _ := range cacheCert {
		// ignore error since only possible error is from key not in dictionary that we are iterating over
		curKey, _ := getCertificateFromCache(key)
		cur := make(map[string]interface{})
		cur["subject"] = curKey.CertData.Subject
		cur["id"] = key
		
		out = append(out, cur)
	}
	return out
}

func GenerateRootCertificate(cert CertInfo) (int, error) {
	caId, err := generateCertificate(cert, true)
	return caId, err
}

func GenerateCertificate(certInfo CertInfo) (int, error) {
	certId, err := generateCertificate(certInfo, false)
	return certId, err
}

func GetSignedRootCertificate(certId int) (*pem.Block, error) {
	ca, err := getCertificateFromCache(certId)
	if err != nil {
		return nil, err
	}
	caBytes, err := x509.CreateCertificate(rand.Reader, ca.CertData, ca.CertData, &ca.KeyData.PublicKey, ca.KeyData)
	if err != nil {
		return nil, err
	}
	return &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: caBytes,
	}, nil
}

func GetCertificatePrivateKey(certId int) (*pem.Block, error) {
	ca, err := getCertificateFromCache(certId)
	if err != nil {
		return nil, err
	}
	keyBlock := &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(ca.KeyData),
	}
	return keyBlock, nil
}

func SignClientCertificate(caId, certId int) (*pem.Block, error) {
	ca, err := getCertificateFromCache(caId)
	if err != nil {
		return nil, err
	}
	cert, err := getCertificateFromCache(certId)
	if err != nil {
		return nil, err
	}
	certBytes, err := x509.CreateCertificate(rand.Reader, cert.CertData, ca.CertData, &cert.KeyData.PublicKey, ca.KeyData)
	return &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: certBytes,
	}, err
}

func generateCertificate(certInfo CertInfo, ca bool) (int, error) {
	certDuration := time.Now().AddDate(1, 0, 0)
	if ca {
		certDuration = time.Now().AddDate(10, 0, 0)
	}
	cert := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			CommonName:         certInfo.CommonName,
			OrganizationalUnit: []string{certInfo.OrganizationalUnit},
			Organization:       []string{certInfo.Organization},
			Country:            []string{certInfo.Country},
			Province:           []string{certInfo.State},
			Locality:           []string{certInfo.City},
			StreetAddress:      []string{certInfo.StreetAddress},
			PostalCode:         []string{certInfo.PostalCode},
		},
		DNSNames:              certInfo.Sans,
		NotBefore:             time.Now().AddDate(0, 0, -1),
		NotAfter:              certDuration,
		IsCA:                  ca,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth, x509.ExtKeyUsageServerAuth},
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		BasicConstraintsValid: true,
	}
	privKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return -1, err
	}
	return saveCertificateToCache(CertKeyData{cert, privKey})
}

func GenerateClientCertFromCSR(csr x509.CertificateRequest, caId int) (*pem.Block, error) {
	certDuration := time.Now().AddDate(1, 0, 0)
	cert := &x509.Certificate{
		Signature:          csr.Signature,
		SignatureAlgorithm: csr.SignatureAlgorithm,

		PublicKeyAlgorithm: csr.PublicKeyAlgorithm,
		PublicKey:          csr.PublicKey,

		SerialNumber: big.NewInt(1),
		Subject:      csr.Subject,
		NotBefore:    time.Now().AddDate(0, 0, -1),
		NotAfter:     certDuration,
		// KeyUsage:     x509.KeyUsageDigitalSignature,
		// ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth},
		IsCA:         false,
		DNSNames:     csr.DNSNames,
		SubjectKeyId: []byte("brock and cody"),
	}

	ca, err := getCertificateFromCache(caId)
	if err != nil {
		return nil, err
	}
	caCRT := ca.CertData
	caPrivKey := ca.KeyData

	clientCRTRaw, err := x509.CreateCertificate(rand.Reader, cert, caCRT, cert.PublicKey, caPrivKey)

	saveCertificateToCache(CertKeyData{cert, nil})

	return &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: clientCRTRaw,
	}, err
}

func CacheUserCertificateAndKey(certKeyData CertKeyData) (int, error) {
	i, err := saveCertificateToCache(certKeyData)
	return i, err
}

func GetCertType(data string) string {
	cert, _ := pem.Decode([]byte(data))
	if cert == nil {
		return ""
	}
	return cert.Type
}

func GetCertJson(key int) (map[string]interface{}, error) {
	out := make(map[string]interface{})
	certKeyData, err := getCertificateFromCache(key)
	if err != nil {
		return nil, err
	}
	out["certs"] = certKeyData
	return out, nil
}