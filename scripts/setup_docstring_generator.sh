#!/bin/bash

echo "Setting up AI Docstring Generator for PKScreener"

# Install Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Pull the code model
echo "Pulling CodeLlama model (4GB, may take 5-10 minutes)..."
ollama pull codellama:7b-instruct

echo "Setup complete!"
echo "Run: python scripts/auto_docstring_with_ai.py"

# # Make script executable
# chmod +x scripts/setup_docstring_generator.sh

# # Run setup (one time)
# ./scripts/setup_docstring_generator.sh

# # Run the docstring generator
# python scripts/auto_docstring_with_ai.py