# Multi-Region Transaction Verification Automation

Autonomous Bitbucket Pipeline for verifying transactions across 8 global regions using Claude AI and Playwright.

## Features

- ✅ **Autonomous Operation**: Runs on schedule without manual intervention
- ✅ **Multi-Region Verification**: Tests 8 regional instances in parallel
- ✅ **AI-Powered**: Uses Claude to intelligently navigate and verify transactions
- ✅ **Automated Reporting**: Generates detailed HTML and JSON reports
- ✅ **Slack Integration**: Sends notifications on completion
- ✅ **Failure Detection**: Identifies issues and provides actionable insights

## Setup Instructions

### 1. Configure Bitbucket Pipelines

Add the `bitbucket-pipelines.yml` file to your repository root.

### 2. Set Environment Variables

In Bitbucket Cloud Repository Settings → Pipelines → Repository variables, add:

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium

python src/multi_region_automation.py

### Test Locally

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Create .env from .env.example
cp .env.example .env
# Edit .env with your credentials

# Run automation
python src/multi_region_automation.py
