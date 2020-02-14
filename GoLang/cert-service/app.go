package main

import (
	"cert-service/pkg/rest"
	"github.com/gin-gonic/gin"
	"net/http"
)

func preflight(c *gin.Context) {
	c.Header("Access-Control-Allow-Origin", "*")
	c.Header("Access-Control-Allow-Headers", "access-control-allow-origin, access-control-allow-headers, Content-Type")
	c.JSON(http.StatusOK, struct{}{})
}

func DebugMiddleware(c *gin.Context) {
	c.Header("Access-Control-Allow-Origin", "*")
	c.Next()
}

func main() {
	DEBUG := true
	router := gin.Default()

	/*
		All endpoints are prepended with /cert
			- /cert/create/ca
			- /cert/create/client
			- /cert/sign
			- /cert/sign/default
	*/
	api := router.Group("/cert")
	{
		if DEBUG {
			api.Use(DebugMiddleware)
			api.OPTIONS("/upload/cert", preflight)
			api.OPTIONS("/sign/csr/:caId", preflight)
		}
		api.GET("/", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{
				"status": "OK",
			})
		})
		api.POST("/create/ca", rest.CreateCAHandler)
		api.POST("/create/client", rest.CreateClientCertHandler)
		api.POST("/sign/csr/:caId", rest.SignCSRHandler)
		api.POST("/file/sign/csr/:caId", rest.SignCSRFileHandler)

		api.GET("/sign/:caId/:certId", rest.SignClientCertWithCAHandler)
		api.GET("/download/:certId", rest.DownloadCACertHandler)
		api.GET("/view", rest.GetAllCerts)
		api.GET("/view/:certId", rest.GetCertJson)

		api.POST("/upload/cert", rest.UploadCertHandler)
		api.POST("/upload/cert-key", rest.UploadKeyAndCertHandler)

		// TODO: In the future it would be nice to upload a key or a cert individually, but the keys are stored with a certIndex and it can become confusing
		//  to start assigning keys without associated certificates
		//api.POST("/upload/key", rest.UploadKeyHandler)

	}

	router.Run(":3000")
}
