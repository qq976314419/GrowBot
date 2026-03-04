# requires: requests, yaml, beautifulsoup4
# module_name: bing_search

import sys
import os
import time
import random
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config if config else {}

def get_default_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def parse_bing_results(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    for item in soup.find_all('li', class_='b_algo'):
        title_elem = item.find('h2')
        link_elem = item.find('a')
        desc_elem = item.find('p')
        
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = link_elem.get('href')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            results.append({
                'title': title,
                'link': link,
                'description': description
            })
    
    return results

def search_bing(query, num_results=10, headers=None, proxies=None, delay_range=(1, 3)):
    base_url = "https://www.bing.com/search"
    results = []
    page = 0
    
    while len(results) < num_results:
        params = {
            'q': query,
            'first': page * 10 + 1,
            'count': 10
        }
        
        try:
            response = requests.get(
                base_url,
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=30
            )
            response.raise_for_status()
            
            page_results = parse_bing_results(response.text)
            if not page_results:
                break
                
            results.extend(page_results)
            page += 1
            
            if len(results) >= num_results:
                results = results[:num_results]
                break
                
            time.sleep(random.uniform(delay_range[0], delay_range[1]))
            
        except requests.RequestException as e:
            print(f"Error during search: {e}")
            break
    
    return results

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    
    config = load_config()
    
    query = config.get('query', '')
    if not query and args:
        query = ' '.join(args)
    if not query:
        query = input("Enter search query: ")
    
    num_results = config.get('num_results', 10)
    custom_headers = config.get('headers', {})
    proxies = config.get('proxies', None)
    delay_range = tuple(config.get('delay_range', [1, 3]))
    
    headers = get_default_headers()
    headers.update(custom_headers)
    
    print(f"Searching Bing for: {query}")
    results = search_bing(query, num_results, headers, proxies, delay_range)
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['link']}")
        print(f"   {result['description']}\n")
    
    return results
