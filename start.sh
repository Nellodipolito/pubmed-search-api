#!/bin/bash

# Start the backend server
echo "Starting backend server..."
python3 main.py &

# Navigate to frontend directory and install dependencies
echo "Setting up frontend..."
cd frontend
npm install

# Start the frontend development server
echo "Starting frontend server..."
npm start 