#!/bin/bash
# Run the migration script

echo "Running PKScreener documentation migration..."

# Run the Python migration script
python3 migrate_to_mdbook.py

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Migration successful!"
    echo ""
    echo "To view the documentation locally:"
    echo "  cd docs/book"
    echo "  mdbook serve --open"
else
    echo "Migration failed. Please check the error messages above."
    exit 1
fi