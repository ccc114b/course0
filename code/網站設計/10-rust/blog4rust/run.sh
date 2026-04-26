#!/bin/bash

# Kill previous rustblog process if exists
pkill -f rustblog 2>/dev/null || true

sleep 1

# Run the server
cargo run
