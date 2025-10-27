#!/bin/bash
# Check Node.js version

echo "Checking Node.js installation..."
echo ""

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo ""
    echo "Install Node.js 18+ using one of these methods:"
    echo ""
    echo "Option 1: Using NodeSource repository (recommended)"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    echo ""
    echo "Option 2: Using nvm (Node Version Manager)"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  source ~/.bashrc"
    echo "  nvm install 20"
    echo "  nvm use 20"
    echo ""
    exit 1
fi

# Get versions
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)

echo "Node.js version: $NODE_VERSION"
echo "npm version: $NPM_VERSION"
echo ""

# Extract major version
NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')

if [ "$NODE_MAJOR" -lt 18 ]; then
    echo "❌ Node.js version $NODE_VERSION is too old"
    echo "   Vite requires Node.js 18 or higher"
    echo ""
    echo "Current: Node.js $NODE_VERSION"
    echo "Required: Node.js 18+"
    echo ""
    echo "Upgrade using one of these methods:"
    echo ""
    echo "Option 1: Using NodeSource repository (recommended)"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    echo ""
    echo "Option 2: Using nvm (Node Version Manager)"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "  source ~/.bashrc"
    echo "  nvm install 20"
    echo "  nvm use 20"
    echo ""
    exit 1
else
    echo "✓ Node.js version is compatible"
    echo ""
    echo "You can now install frontend dependencies:"
    echo "  cd frontend"
    echo "  npm install"
    echo ""
    echo "Or run the frontend:"
    echo "  ./start_frontend.sh"
fi
