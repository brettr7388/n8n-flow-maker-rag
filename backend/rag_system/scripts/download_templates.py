#!/usr/bin/env python3
"""
Download n8n workflow templates from multiple sources
"""
import os
import json
import requests
import time
from pathlib import Path
from tqdm import tqdm
import subprocess

class TemplateDownloader:
    def __init__(self, output_dir="../raw_templates"):
        self.output_dir = Path(__file__).parent.parent / output_dir.lstrip('../')
        self.output_dir.mkdir(exist_ok=True)
        
    def download_github_repo(self, repo_url, category_name):
        """Clone and extract JSON files from GitHub repo"""
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        clone_dir = self.output_dir / "github" / repo_name
        
        print(f"Cloning {repo_url}...")
        
        # Create parent directory
        clone_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Clone repository
        try:
            subprocess.run(
                ["git", "clone", repo_url, str(clone_dir)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            return 0
        
        # Find all JSON files
        json_files = list(clone_dir.rglob("*.json"))
        print(f"Found {len(json_files)} JSON files in {repo_name}")
        
        # Copy to organized structure
        output_category = self.output_dir / category_name
        output_category.mkdir(exist_ok=True)
        
        valid_count = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate it's an n8n workflow
                if 'nodes' in data and 'connections' in data:
                    # Create unique filename
                    safe_name = json_file.stem.replace(' ', '_')[:50]
                    output_path = output_category / f"{safe_name}_{valid_count}.json"
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    
                    valid_count += 1
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
        
        print(f"Extracted {valid_count} valid workflows from {repo_name}")
        return valid_count
    
    def download_n8n_official(self, limit=200):
        """Download workflows from n8n.io API"""
        base_url = "https://n8n.io/api/templates"
        output_dir = self.output_dir / "official"
        output_dir.mkdir(exist_ok=True)
        
        print("Fetching n8n.io workflows...")
        
        total_downloaded = 0
        
        # Try to get workflows via search endpoint
        try:
            # Search for various categories
            categories = ['crm', 'sales', 'marketing', 'email', 'automation', 
                         'webhook', 'api', 'database', 'ai', 'slack']
            
            for category in tqdm(categories, desc="Processing categories"):
                try:
                    search_url = f"{base_url}/search?query={category}&limit=20"
                    response = requests.get(search_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        workflows = data.get('workflows', [])
                        
                        for workflow in workflows:
                            workflow_id = workflow.get('id')
                            if not workflow_id:
                                continue
                            
                            # Save workflow
                            safe_name = workflow.get('name', '').replace(' ', '_')[:50]
                            filename = f"{safe_name}_{workflow_id}.json"
                            filepath = output_dir / filename
                            
                            # Check if already downloaded
                            if filepath.exists():
                                continue
                            
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(workflow, f, indent=2)
                            
                            total_downloaded += 1
                            
                            # Rate limiting
                            time.sleep(0.5)
                            
                            if total_downloaded >= limit:
                                break
                                
                except Exception as e:
                    print(f"Error fetching category {category}: {e}")
                    continue
                
                if total_downloaded >= limit:
                    break
                    
        except Exception as e:
            print(f"Error in n8n.io download: {e}")
        
        print(f"\nDownloaded {total_downloaded} workflows from n8n.io")
        return total_downloaded

def main():
    downloader = TemplateDownloader()
    
    print("=" * 70)
    print("N8N TEMPLATE DOWNLOADER")
    print("=" * 70)
    
    total_count = 0
    
    # Download from GitHub sources
    print("\n[1/3] Downloading from enescingoz/awesome-n8n-templates...")
    try:
        count1 = downloader.download_github_repo(
            "https://github.com/enescingoz/awesome-n8n-templates.git",
            "awesome_templates"
        )
        total_count += count1
    except Exception as e:
        print(f"Error downloading from enescingoz: {e}")
        count1 = 0
    
    print("\n[2/3] Downloading from wassupjay/n8n-free-templates...")
    try:
        count2 = downloader.download_github_repo(
            "https://github.com/wassupjay/n8n-free-templates.git",
            "advanced_templates"
        )
        total_count += count2
    except Exception as e:
        print(f"Error downloading from wassupjay: {e}")
        count2 = 0
    
    # Download from n8n.io
    print("\n[3/3] Downloading from n8n.io official library...")
    try:
        count3 = downloader.download_n8n_official(limit=200)
        total_count += count3
    except Exception as e:
        print(f"Error downloading from n8n.io: {e}")
        count3 = 0
    
    print("\n" + "=" * 70)
    print(f"DOWNLOAD COMPLETE!")
    print(f"Total workflows downloaded: {total_count}")
    print(f"  - awesome-n8n-templates: {count1}")
    print(f"  - n8n-free-templates: {count2}")
    print(f"  - n8n.io official: {count3}")
    print("=" * 70)

if __name__ == "__main__":
    main()


