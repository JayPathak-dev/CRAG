#!/bin/bash

echo "Starting CRAG Enterprise Backend and React Frontend..."

# Activate virtual environment
source .venv/bin/activate

# Start FastAPI backend on port 8000
echo "Starting FastAPI Server on port 8000..."
uvicorn server:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Vite React App on port 5173
echo "Starting React Frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "Both services are running."
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "Press Ctrl+C to stop both."

# Wait for any process to exit
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
