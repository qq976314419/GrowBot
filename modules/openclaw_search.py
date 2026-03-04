# module_name: openclaw_search
# requires: requests

import requests
import json
from typing import Optional, Dict, Any

def search_openclaw(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for information about the OpenClaw project.
    This function uses a public API (like GitHub API) to search for repositories.
    """
    # Using GitHub API to search for repositories related to OpenClaw
    url = "https://api.github.com/search/repositories"
    params = {"q": f"{query} in:name,description,readme", "sort": "stars", "order": "desc"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Filter for items that are likely related to OpenClaw
        openclaw_items = []
        for item in data.get("items", []):
            if "openclaw" in item["name"].lower() or "openclaw" in item.get("description", "").lower():
                openclaw_items.append(item)
        
        if openclaw_items:
            # Return the first (most starred) result
            result = openclaw_items[0]
            return {
                "name": result["name"],
                "full_name": result["full_name"],
                "description": result.get("description", ""),
                "html_url": result["html_url"],
                "stargazers_count": result["stargazers_count"],
                "forks_count": result["forks_count"],
                "language": result.get("language", ""),
                "updated_at": result["updated_at"]
            }
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def display_info(info: Dict[str, Any]) -> None:
    """Display the information about the OpenClaw project."""
    if info:
        print("OpenClaw Project Information:")
        print(f"Name: {info['name']}")
        print(f"Full Name: {info['full_name']}")
        print(f"Description: {info['description']}")
        print(f"URL: {info['html_url']}")
        print(f"Stars: {info['stargazers_count']}")
        print(f"Forks: {info['forks_count']}")
        print(f"Language: {info['language']}")
        print(f"Last Updated: {info['updated_at']}")
    else:
        print("No information found for OpenClaw project.")

def main(args=None):
    """Main function to search and display OpenClaw project information."""
    if args is None:
        # If no arguments provided, prompt for search query
        query = input("Enter search query for OpenClaw (default: 'openclaw'): ").strip()
        if not query:
            query = "openclaw"
    else:
        # Use the first argument as query, or default to 'openclaw'
        query = args[0] if args else "openclaw"
    
    print(f"Searching for '{query}'...")
    info = search_openclaw(query)
    display_info(info)
