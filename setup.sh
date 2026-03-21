# Create all directories
mkdir -p .github/workflows
mkdir -p src
mkdir -p scripts
mkdir -p reports
mkdir -p tests
mkdir -p docs

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Reports
reports/
artifacts/

# Playwright
.cache/ms-playwright/

# OS
.DS_Store
Thumbs.db
EOF