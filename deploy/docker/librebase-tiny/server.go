// tiny-lb — minimal static HTTP CRUD server for the Librebase lidb engine.
//
// Speaks the lidb_embed `session` NDJSON protocol over a persistent child process
// so per-request latency stays sub-ms (no per-request spawn). Routes mirror the
// todo-app surface: GET/POST /rest/v1/todos, PATCH/DELETE /rest/v1/todos/{id},
// GET /health. Built CGO_ENABLED=0 → static, runs on scratch.
package main

import (
	"bufio"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"
)

var (
	sess    *exec.Cmd
	sessIn  io.WriteCloser
	sessOut *bufio.Scanner
	mu      sync.Mutex
)

type sessionRequest struct {
	Cmd    string          `json:"cmd"`
	SQL    string          `json:"sql"`
	Params json.RawMessage `json:"params"`
	Sub    string          `json:"sub"`
	Role   string          `json:"role"`
}

func sessionCall(cmd string, sql string, params json.RawMessage, sub, role string) (map[string]any, error) {
	mu.Lock()
	defer mu.Unlock()
	req := sessionRequest{Cmd: cmd, SQL: sql, Params: params, Sub: sub, Role: role}
	if cmd == "set_claims" {
		req = sessionRequest{Cmd: cmd, Sub: sub, Role: role}
	}
	b, _ := json.Marshal(req)
	if _, err := sessIn.Write(append(b, '\n')); err != nil {
		return nil, err
	}
	if !sessOut.Scan() {
		return nil, fmt.Errorf("session closed: %v", sessOut.Err())
	}
	var out map[string]any
	if err := json.Unmarshal(sessOut.Bytes(), &out); err != nil {
		return nil, err
	}
	return out, nil
}

func execSQL(sql string, params json.RawMessage) (map[string]any, error) {
	out, err := sessionCall("exec", sql, params, "", "")
	if err != nil {
		return nil, err
	}
	if ok, _ := out["ok"].(bool); !ok {
		return nil, fmt.Errorf("exec: %v", out["error"])
	}
	return out, nil
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func newUUID() string {
	var b [16]byte
	rand.Read(b[:])
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}

func timeNow() string {
	return time.Now().UTC().Format(time.RFC3339)
}

func main() {
	dataDir := os.Getenv("LI_DATA_DIR")
	if dataDir == "" {
		dataDir = "/data"
	}
	embed := os.Getenv("LIDB_EMBED")
	if embed == "" {
		embed = "/usr/local/bin/lidb_embed"
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "8788"
	}

	os.MkdirAll(dataDir, 0o755)
	migrations := os.Getenv("LIDB_MIGRATIONS")
	if migrations == "" {
		migrations = "/etc/librebase/migrations"
	}
	sess = exec.Command(embed, "session", dataDir)
	sess.Env = append(os.Environ(), "LIDB_MIGRATIONS="+migrations)
	in, err := sess.StdinPipe()
	if err != nil {
		panic(err)
	}
	out, err := sess.StdoutPipe()
	if err != nil {
		panic(err)
	}
	sess.Stderr = os.Stderr
	sessIn = in
	sessOut = bufio.NewScanner(out)
	if err := sess.Start(); err != nil {
		panic(err)
	}
	if !sessOut.Scan() {
		panic("session did not become ready")
	}
	ready := sessOut.Bytes()
	var readyJSON map[string]any
	_ = json.Unmarshal(ready, &readyJSON)
	if ok, _ := readyJSON["ready"].(bool); !ok {
		panic("lidb session not ready: " + string(ready))
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, map[string]any{"ok": true, "service": "librebase-tiny"})
	})
	mux.HandleFunc("/rest/v1/todos", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			out, err := execSQL("SELECT id, title, done, created_at FROM todos ORDER BY created_at LIMIT 100", nil)
			if err != nil {
				writeJSON(w, 500, map[string]any{"error": err.Error()})
				return
			}
			writeJSON(w, 200, out["rows"])
		case http.MethodPost:
			var body struct {
				Title  string `json:"title"`
				Done   bool   `json:"done"`
				UserID string `json:"user_id"`
			}
			if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
				writeJSON(w, 400, map[string]any{"error": "bad json"})
				return
			}
			if body.UserID == "" {
				body.UserID = "00000000-0000-0000-0000-000000000000"
			}
			id := newUUID()
			now := timeNow()
			doneStr := "false"
			if body.Done {
				doneStr = "true"
			}
			p := json.RawMessage(fmt.Sprintf(`[%q,%q,%q,%q,%q]`, id, body.UserID, body.Title, doneStr, now))
			out, err := execSQL("INSERT INTO todos (id, user_id, title, done, created_at) VALUES (?, ?, ?, ?, ?)", p)
			if err != nil {
				writeJSON(w, 500, map[string]any{"error": err.Error()})
				return
			}
			if aff, _ := out["affected"].(float64); aff == 0 {
				writeJSON(w, 500, map[string]any{"error": "insert affected 0"})
				return
			}
			writeJSON(w, 201, map[string]any{"id": id, "title": body.Title, "done": body.Done, "user_id": body.UserID, "created_at": now})
		default:
			writeJSON(w, 405, map[string]any{"error": "method not allowed"})
		}
	})
	mux.HandleFunc("/rest/v1/todos/", func(w http.ResponseWriter, r *http.Request) {
		id := strings.TrimPrefix(r.URL.Path, "/rest/v1/todos/")
		switch r.Method {
		case http.MethodPatch:
			var body struct {
				Done *bool `json:"done"`
			}
			if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
				writeJSON(w, 400, map[string]any{"error": "bad json"})
				return
			}
			if body.Done == nil {
				writeJSON(w, 400, map[string]any{"error": "done required"})
				return
			}
			doneStr := "false"
			if *body.Done {
				doneStr = "true"
			}
			p := json.RawMessage(fmt.Sprintf(`[%q,%q]`, doneStr, id))
			out, err := execSQL("UPDATE todos SET done = ? WHERE id = ?", p)
			if err != nil {
				writeJSON(w, 500, map[string]any{"error": err.Error()})
				return
			}
			if aff, _ := out["affected"].(float64); aff == 0 {
				writeJSON(w, 404, map[string]any{"error": "not found"})
				return
			}
			writeJSON(w, 200, map[string]any{"id": id, "done": *body.Done})
		case http.MethodDelete:
			p := json.RawMessage(fmt.Sprintf(`[%q]`, id))
			out, err := execSQL("DELETE FROM todos WHERE id = ?", p)
			if err != nil {
				writeJSON(w, 500, map[string]any{"error": err.Error()})
				return
			}
			if aff, _ := out["affected"].(float64); aff == 0 {
				writeJSON(w, 404, map[string]any{"error": "not found"})
				return
			}
			writeJSON(w, 204, nil)
		default:
			writeJSON(w, 405, map[string]any{"error": "method not allowed"})
		}
	})

	http.ListenAndServe(":"+port, mux)
}
