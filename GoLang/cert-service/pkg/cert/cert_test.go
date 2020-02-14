package cert

import (
	"testing"
)

func TestGenerateRootCertificate(t *testing.T) {
	certInfo := CertInfo{
		OrganizationalUnit: "",
		Organization: "",
		Country: "US",
		State: "",
		City: "",
		StreetAddress: "",
		PostalCode: "",
	}
	caCert := generateCertificate(certInfo, true)
	if caCert.Subject.Country[0] != "US" {
		t.Fatalf("country was %s not %s", caCert.Subject.Country[0], "US")
	}
}