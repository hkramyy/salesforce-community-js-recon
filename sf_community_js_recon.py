import re
import sys
import json
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
from urllib.parse import unquote, urljoin
from colorama import Fore, Style, init

init(autoreset=True)


def extract_last_published_js_url(html_content, base_url):
    """Find the last script src containing 'Published' marker"""
    soup = BeautifulSoup(html_content, "html.parser")
    scripts = soup.find_all("script", src=True)
    published_scripts = []
    for script in scripts:
        src = script["src"]
        if "Published%22%7D" in src or unquote(src).endswith('Published"}'):
            published_scripts.append(urljoin(base_url, src))
    if published_scripts:
        return published_scripts[-1]
    return None


def extract_routes(js_content):
    """Extract route keys under any 'routes' block"""
    route_keys = []
    try:
        # Extract JSON-like "routes": { ... } object
        routes_match = re.search(r'"routes"\s*:\s*{.*?}\s*}[,}]', js_content, re.DOTALL)
        if routes_match:
            raw_block = routes_match.group(0)
            raw_json = "{" + raw_block.rstrip(',') + "}"
            cleaned_json = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw_json)
            parsed = json.loads(cleaned_json)
            if "routes" in parsed:
                route_keys = list(parsed["routes"].keys())
    except Exception:
        pass
    return route_keys


def extract_information(js_content):
    """Extract endpoints and sensitive info using regex and route structure"""
    return {
        "Community Routes (from routes JSON)": extract_routes(js_content),
        "Endpoints (URLs)": re.findall(r'https?://[^\s"\'<>]+', js_content),
        "API Paths (/services/apexrest, etc.)": re.findall(r'(/[a-zA-Z0-9_\-/.]*api[a-zA-Z0-9_\-/.]*)', js_content),
        "Access Tokens / Bearer": re.findall(r'(?i)(?:bearer|token)[\'"\s:=>]+([A-Za-z0-9\-_.]+)', js_content),
        "Secrets / Keys / Auth Values": re.findall(r'(?i)(?:key|secret|auth)[\'"\s:=>]+([A-Za-z0-9\-_.]{8,})', js_content),
        "Salesforce Custom Objects (__c)": re.findall(r'"([a-zA-Z0-9_]{1,100}__c)"', js_content),
    }


def format_output(findings):
    """Print extracted data in professional colorized format"""
    order = list(findings.keys())

    for category in order:
        print(Fore.CYAN + "\n" + "=" * 80)
        print(Fore.GREEN + f"{category}".center(80))
        print(Fore.CYAN + "=" * 80)
        items = findings[category]

        if items:
            unique_items = sorted(set(items))
            table = [[i + 1, val] for i, val in enumerate(unique_items)]
            print(Fore.WHITE + tabulate(table, headers=["#", "Value"], tablefmt="grid"))
        else:
            print(Fore.RED + "No data found.")


def main(community_url):
    print(Fore.YELLOW + f"[*] Fetching source HTML from: {community_url}")
    try:
        res = requests.get(community_url, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        print(Fore.RED + f"[!] Error fetching community page: {e}")
        sys.exit(1)

    js_url = extract_last_published_js_url(res.text, community_url)
    if not js_url:
        print(Fore.RED + "[!] Could not find any JS file ending with 'Published'}")
        sys.exit(1)

    print(Fore.YELLOW + f"[+] Using last Published JS file: {js_url}")
    try:
        js_res = requests.get(js_url, timeout=10)
        js_res.raise_for_status()
    except requests.RequestException as e:
        print(Fore.RED + f"[!] Error fetching JS file: {e}")
        sys.exit(1)

    print(Fore.YELLOW + "[+] Extracting sensitive information from JS...")
    findings = extract_information(js_res.text)
    format_output(findings)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sf_community_js_recon.py <Salesforce Community URL>")
        sys.exit(1)

    community_url = sys.argv[1]
    main(community_url)
