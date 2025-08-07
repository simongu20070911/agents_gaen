#!/bin/bash

# Define the output file
OUTPUT_FILE="/home/gaen/agents_gaen/dmoi.txt"

# Clear the output file if it exists
> "$OUTPUT_FILE"

# Base directory
BASE_DIR="/home/gaen/agents_gaen/department_of_market_intelligence"

# Function to add file content with header
add_file_content() {
    local file_path="$1"
    if [ -f "$file_path" ]; then
        echo "################################################################################" >> "$OUTPUT_FILE"
        echo "# FILE: $file_path" >> "$OUTPUT_FILE"
        echo "################################################################################" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        cat "$file_path" >> "$OUTPUT_FILE"
        echo -e "\n\n" >> "$OUTPUT_FILE"
    fi
}

# Copy Python files from agents directory
echo "Processing agents directory..." 
for py_file in "$BASE_DIR/agents"/*.py; do
    [ -f "$py_file" ] && add_file_content "$py_file"
done

# Copy Python files from prompts directory
echo "Processing prompts directory..."
for py_file in "$BASE_DIR/prompts"/*.py; do
    [ -f "$py_file" ] && add_file_content "$py_file"
done

# Copy Python files from tools directory
echo "Processing tools directory..."
for py_file in "$BASE_DIR/tools"/*.py; do
    [ -f "$py_file" ] && add_file_content "$py_file"
done

# Copy Python files from utils directory
echo "Processing utils directory..."
for py_file in "$BASE_DIR/utils"/*.py; do
    [ -f "$py_file" ] && add_file_content "$py_file"
done

# Copy Python files from workflows directory
echo "Processing workflows directory..."
for py_file in "$BASE_DIR/workflows"/*.py; do
    [ -f "$py_file" ] && add_file_content "$py_file"
done

# Copy specific files
echo "Processing individual files..."
add_file_content "$BASE_DIR/__init__.py"
add_file_content "$BASE_DIR/.env"
add_file_content "$BASE_DIR/config.py"
add_file_content "$BASE_DIR/main.py"

# Copy dmoivision.txt from parent directory
add_file_content "/home/gaen/agents_gaen/dmoivision.txt"

echo "All files have been copied to $OUTPUT_FILE"
echo "Total files processed: $(grep -c "^# FILE:" "$OUTPUT_FILE")"