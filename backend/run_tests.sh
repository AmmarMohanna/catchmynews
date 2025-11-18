#!/bin/bash
# Test runner script

echo "Running NewsCatcher Tests..."
echo "=============================="

# Run pytest with coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

echo ""
echo "Tests completed!"
echo "Coverage report generated in htmlcov/index.html"

