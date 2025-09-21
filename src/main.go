package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	fs := http.FileServer(http.Dir("./static"))
	http.Handle("/", fs)

	// Echo endpoint
	http.HandleFunc("/echo", func(w http.ResponseWriter, r *http.Request) {
		msg := r.URL.Query().Get("msg")
		if msg == "" {
			msg = "No message provided"
		}
		fmt.Fprint(w, msg)
	})

	port := ":8080"
	log.Println("Server running at http://localhost" + port)
	log.Fatal(http.ListenAndServe(port, nil))
}
