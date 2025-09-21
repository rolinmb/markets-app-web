package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strings"
)

// Map modes to Python scripts
var modeScripts = map[string]string{
	"Equities":        "scripts/equities.py",
	"Cryptocurrencies": "scripts/crypto.py",
	"Foreign Exchange": "scripts/forex.py",
	"Commodities":     "scripts/commodities.py",
	"Bonds":           "scripts/bonds.py",
	"Options":         "scripts/options.py",
}

var allowedCommodities = map[string]bool{
	"wti": true, "brent": true, "natural_gas": true, "copper": true,
	"aluminum": true, "wheat": true, "corn": true, "cotton": true,
	"sugar": true, "coffee": true, "all_commodities": true,
}

func main() {
	for _, dir := range []string{"static/data", "static/img"} {
		if err := os.MkdirAll(dir, 0755); err != nil {
			log.Fatalf("Failed to create directory %s: %v", dir, err)
		}
	}
	// Serve static files (HTML/JS)
	http.Handle("/", http.FileServer(http.Dir("./static")))
	// Serve the img folder
	http.Handle("/img/", http.StripPrefix("/img/", http.FileServer(http.Dir("static/img"))))
	http.HandleFunc("/list-images", func(w http.ResponseWriter, r *http.Request) {
		files, err := os.ReadDir("static/img")
		if err != nil {
			http.Error(w, "Failed to list images", http.StatusInternalServerError)
			return
		}
		var bmpFiles []string
		for _, f := range files {
			if !f.IsDir() && strings.HasSuffix(strings.ToLower(f.Name()), ".bmp") {
				bmpFiles = append(bmpFiles, f.Name())
			}
		}
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, "[\"" + strings.Join(bmpFiles, `","`) + "\"]")
	})
	http.HandleFunc("/run", func(w http.ResponseWriter, r *http.Request) {
		mode := r.URL.Query().Get("mode")
		script, ok := modeScripts[mode]
		if !ok {
			http.Error(w, "Invalid mode", http.StatusBadRequest)
			return
		}
		asset := strings.TrimSpace(r.URL.Query().Get("asset"))
		// Validate asset
		switch mode {
		case "Commodities":
			if !allowedCommodities[asset] {
				http.Error(w, "Invalid commodity selected", http.StatusBadRequest)
				return
			}
		case "Equities", "Options":
			if len(asset) == 0 || len(asset) > 4 {
				http.Error(w, "Equities/Options asset must be 1-4 characters", http.StatusBadRequest)
				return
			}
		case "Foreign Exchange":
			if len(asset) != 6 {
				http.Error(w, "Foreign Exchange asset must be exactly 6 characters", http.StatusBadRequest)
				return
			}
		case "Cryptocurrencies":
			if len(asset) == 0 || len(asset) > 15 {
				http.Error(w, "Cryptocurrency asset must be 1-15 characters", http.StatusBadRequest)
				return
			}
		case "Bonds":
			asset = ""
		}
		args := []string{script}
		if asset != "" {
			args = append(args, asset)
		}
		cmd := exec.Command("python", args...)
		out, err := cmd.CombinedOutput()
		if err != nil {
			http.Error(w, fmt.Sprintf("Error running script: %v\nOutput: %s", err, out), http.StatusInternalServerError)
			return
		}
		fmt.Fprint(w, string(out))
	})

	port := ":8080"
	log.Println("Server running at http://localhost" + port)
	log.Fatal(http.ListenAndServe(port, nil))
}
