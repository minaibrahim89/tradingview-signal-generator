#!/bin/bash
# Test the extraction process locally

echo "Testing extraction process"

# Create a test directory
mkdir -p test_extraction
cd test_extraction

# Create a sample app
echo "console.log('Hello World');" > app.js
echo "print('Hello from Python')" > app.py
mkdir -p static
echo "<html><body>Test Page</body></html>" > static/index.html

# Create a tar.gz file like Azure would
echo "Creating test tar.gz"
tar -czf output.tar.gz app.js app.py static

# Remove the original files to simulate Azure's environment
rm -rf app.js app.py static

# Copy our extraction script
cp ../extract_and_start.sh .
chmod +x extract_and_start.sh

# Run the extraction script
echo "Running extraction script"
./extract_and_start.sh

# Check results
echo "Files after extraction:"
ls -la

cd ..
echo "Test completed, you can check the test_extraction directory" 