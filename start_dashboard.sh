#!/bin/bash
# start_dashboard.sh — Launch the Jira proxy and dashboard server in two terminals

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting DORA Dashboard..."

# Terminal 1: Jira proxy
gnome-terminal --title="DORA Proxy" -- bash -c "
  cd '$REPO_DIR'
  echo '=== Jira CORS Proxy ===';
  python3 proxy/server.py;
  echo 'Proxy stopped. Press Enter to close.';
  read
"

# Terminal 2: Dashboard HTTP server
gnome-terminal --title="DORA Dashboard" -- bash -c "
  cd '$REPO_DIR/dashboard'
  echo '=== Dashboard Server ===';
  echo 'Open http://localhost:3000 in your browser';
  echo '';
  python3 -m http.server 3000;
  echo 'Server stopped. Press Enter to close.';
  read
"

# Open browser after a short delay
sleep 2 && xdg-open http://localhost:3000 &

echo "Done. Two terminals opened + browser launching."
