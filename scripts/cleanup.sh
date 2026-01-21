#!/bin/bash
# Cleanup script for IoT Project
# Removes temporary files, cache directories, and unwanted artifacts

echo "🧹 Cleaning up IoT Project..."

# Remove Python cache directories (except venv)
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" ! -path "./venv/*" -exec rm -rf {} + 2>/dev/null

# Remove Python compiled files
echo "Removing .pyc and .pyo files..."
find . -name "*.pyc" ! -path "./venv/*" -delete 2>/dev/null
find . -name "*.pyo" ! -path "./venv/*" -delete 2>/dev/null

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" ! -path "./venv/*" -delete 2>/dev/null

# Remove test certificate files
echo "Removing test certificate files..."
rm -f test_certs test_certs2 2>/dev/null

# Clean up old log files (optional - uncomment if needed)
# echo "Cleaning old log files..."
# find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null

echo "✅ Cleanup complete!"
echo ""
echo "Remaining __pycache__ directories (should only be in venv):"
find . -type d -name "__pycache__" ! -path "./venv/*" 2>/dev/null | wc -l

