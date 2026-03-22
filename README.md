# 🔍 Multi-Region Transaction Verification Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-1.49+-green.svg)](https://playwright.dev/)
[![Claude AI](https://img.shields.io/badge/Claude-AI--Powered-purple.svg)](https://claude.ai/)

Autonomous multi-region transaction verification system that uses **Claude AI** and **Playwright** to automatically verify transactions across 8 global regions. Fully integrated with GitHub Actions for scheduled and manual execution.

## 🌍 Features

- ✅ **8-Region Support**: Verify transactions across US-EAST, US-WEST, EU-WEST, ASIA-PACIFIC, CANADA, SOUTH-AMERICA, MIDDLE-EAST, and AFRICA
- ✅ **AI-Powered Automation**: Claude AI intelligently navigates web interfaces
- ✅ **Parallel Execution**: 4 concurrent browsers for optimal performance (45-60 seconds total)
- ✅ **Autonomous Operation**: Scheduled daily (2 AM UTC) and weekly (Monday midnight UTC)
- ✅ **Comprehensive Reporting**: Beautiful HTML reports + JSON data + detailed logs
- ✅ **Slack Integration**: Automatic notifications on completion
- ✅ **Failure Detection**: Identifies issues with actionable insights
- ✅ **GitHub Actions Ready**: Works out of the box with GitHub Workflows

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- GitHub account with repository
- Anthropic API key
- Slack webhook (optional, for notifications)

### Setup Instructions

#### 1. **Clone or Create Repository**

```bash
git clone https://github.com/nirmalcse/multi-region-tx-verification.git
cd multi-region-tx-verification

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m playwright install chromium

cp .env.example .env
# Edit .env with your credentials