# Salesforce Community JS Recon

This tool extracts JavaScript-based routes, API endpoints, tokens, and other useful reconnaissance data from the latest **Published** JS file in a Salesforce Community page.

## 💡 Features

- Automatically identifies the JS file from the page.
- Extracts:
  - Routes
  - Full URLs
  - API endpoints
  - Access tokens / bearer values
  - Secrets / keys
  - Custom objects (`__c`)

## 🔧 Prerequisites

Python 3.7+

Install required libraries:

```bash
pip install -r requirements.txt

🚀 Usage

python sf_community_js_recon.py https://your-community-site.force.com/


