#!/bin/bash
# Installation script for mdBook and dependencies

echo "Installing mdBook for PKScreener documentation..."

# Install mdBook
echo "Installing mdBook..."
cargo install mdbook

# Install mdBook plugins (optional but recommended)
echo "Installing mdBook plugins..."
cargo install mdbook-index
cargo install mdbook-footnote

echo "Installation complete!"
echo ""
echo "To build the documentation:"
echo "  cd docs/book"
echo "  mdbook build"
echo ""
echo "To serve locally:"
echo "  mdbook serve --open"