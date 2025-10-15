"""
Workflow scraper for n8n.io workflows library.
Scrapes workflows from n8n.io/workflows/ for RAG enhancement.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import hashlib

logger = logging.getLogger(__name__)


class WorkflowScraper:
    """Scrapes n8n workflows from n8n.io for knowledge base."""
    
    BASE_URL = "https://n8n.io"
    CATEGORIES = [
        "it-ops",
        "sales",
        "customer-support", 
        "data-analytics",
        "hr",
        "development",
        "social-media",
        "finance",
        "marketing",
        "productivity"
    ]
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "n8n-flow-generator/1.0 (Educational Purpose)"
            }
        )
    
    async def scrape_category(self, category: str, max_workflows: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape workflows from a specific category.
        
        Args:
            category: Category slug (e.g., 'it-ops')
            max_workflows: Maximum number of workflows to scrape
            
        Returns:
            List of workflow dictionaries with metadata
        """
        workflows = []
        
        try:
            url = f"{self.BASE_URL}/workflows/categories/{category}/"
            logger.info(f"Scraping category: {category}")
            
            response = await self.client.get(url)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {category}: {response.status_code}")
                return workflows
            
            # Parse workflow list page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Note: This is a simplified scraper. n8n.io might require
            # more sophisticated scraping or API access
            workflow_links = self._extract_workflow_links(soup, category)
            
            # Scrape individual workflows
            for i, link in enumerate(workflow_links[:max_workflows]):
                if i >= max_workflows:
                    break
                    
                try:
                    workflow = await self._scrape_workflow_detail(link, category)
                    if workflow:
                        workflows.append(workflow)
                        logger.info(f"Scraped workflow: {workflow.get('title', 'Unknown')}")
                    
                    # Rate limiting
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    logger.error(f"Error scraping workflow {link}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping category {category}: {e}")
        
        return workflows
    
    def _extract_workflow_links(self, soup: BeautifulSoup, category: str) -> List[str]:
        """Extract workflow detail page links from category page."""
        links = []
        
        # Look for workflow cards/links
        # This is a placeholder - actual implementation depends on n8n.io structure
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/workflows/' in href and href != f'/workflows/categories/{category}/':
                full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                if full_url not in links:
                    links.append(full_url)
        
        return links
    
    async def _scrape_workflow_detail(self, url: str, category: str) -> Optional[Dict[str, Any]]:
        """
        Scrape details from a specific workflow page.
        
        Args:
            url: Workflow detail page URL
            category: Category the workflow belongs to
            
        Returns:
            Workflow dictionary with metadata
        """
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract workflow data
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            workflow_json = self._extract_workflow_json(soup)
            
            if not workflow_json:
                logger.warning(f"No workflow JSON found for {url}")
                return None
            
            # Extract metadata from workflow JSON
            nodes_used = self._extract_node_types(workflow_json)
            node_count = len(workflow_json.get('nodes', []))
            complexity_score = self._calculate_complexity(workflow_json)
            patterns = self._extract_patterns(workflow_json)
            
            # Generate unique ID
            workflow_id = hashlib.md5(url.encode()).hexdigest()
            
            return {
                "id": workflow_id,
                "url": url,
                "title": title,
                "description": description,
                "category": category,
                "node_count": node_count,
                "complexity_score": complexity_score,
                "nodes_used": nodes_used,
                "patterns": patterns,
                "workflow_json": workflow_json,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping workflow detail {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract workflow title from page."""
        # Try various common title selectors
        title_tag = soup.find('h1') or soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Untitled Workflow"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract workflow description from page."""
        # Try various description selectors
        desc_tag = (
            soup.find('meta', {'name': 'description'}) or
            soup.find('p', class_='description') or
            soup.find('div', class_='description')
        )
        
        if desc_tag:
            if desc_tag.name == 'meta':
                return desc_tag.get('content', '')
            return desc_tag.get_text(strip=True)
        
        return ""
    
    def _extract_workflow_json(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract workflow JSON from page."""
        # Look for JSON in script tags or data attributes
        script_tags = soup.find_all('script', type='application/json')
        
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if self._is_workflow_json(data):
                    return data
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Try to find JSON in other places
        for script in soup.find_all('script'):
            if script.string and 'workflow' in script.string.lower():
                try:
                    # Extract JSON from JavaScript
                    start = script.string.find('{')
                    end = script.string.rfind('}') + 1
                    if start != -1 and end > start:
                        potential_json = script.string[start:end]
                        data = json.loads(potential_json)
                        if self._is_workflow_json(data):
                            return data
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
    
    def _is_workflow_json(self, data: Any) -> bool:
        """Check if data looks like a valid n8n workflow JSON."""
        if not isinstance(data, dict):
            return False
        
        required_keys = ['nodes', 'connections']
        return all(key in data for key in required_keys)
    
    def _extract_node_types(self, workflow_json: Dict[str, Any]) -> List[str]:
        """Extract list of node types used in workflow."""
        nodes = workflow_json.get('nodes', [])
        node_types = []
        
        for node in nodes:
            node_type = node.get('type', '')
            if node_type and node_type not in node_types:
                # Remove 'n8n-nodes-base.' prefix for cleaner names
                clean_type = node_type.replace('n8n-nodes-base.', '')
                node_types.append(clean_type)
        
        return node_types
    
    def _calculate_complexity(self, workflow_json: Dict[str, Any]) -> float:
        """
        Calculate workflow complexity score (1-10).
        
        Based on:
        - Number of nodes
        - Number of connections
        - Use of conditional logic (IF, Switch)
        - Use of error handling
        - Use of loops
        """
        nodes = workflow_json.get('nodes', [])
        connections = workflow_json.get('connections', {})
        
        score = 1.0
        
        # Node count contribution (max 4 points)
        node_count = len(nodes)
        score += min(node_count / 5, 4)
        
        # Connection complexity (max 2 points)
        total_connections = sum(
            len(conn_types.get('main', [[]])[0])
            for conn_types in connections.values()
        )
        score += min(total_connections / 10, 2)
        
        # Special node types (max 4 points)
        node_types = [node.get('type', '') for node in nodes]
        
        if any('if' in t.lower() or 'switch' in t.lower() for t in node_types):
            score += 1.5  # Conditional logic
        
        if any('error' in t.lower() for t in node_types):
            score += 1.0  # Error handling
        
        if any('loop' in t.lower() or 'split' in t.lower() for t in node_types):
            score += 1.0  # Loops/batching
        
        if any('function' in t.lower() or 'code' in t.lower() for t in node_types):
            score += 0.5  # Custom code
        
        return min(score, 10.0)
    
    def _extract_patterns(self, workflow_json: Dict[str, Any]) -> List[str]:
        """Extract workflow patterns used."""
        patterns = []
        nodes = workflow_json.get('nodes', [])
        node_types = [node.get('type', '').lower() for node in nodes]
        
        # Pattern detection
        if any('if' in t or 'switch' in t for t in node_types):
            patterns.append('conditional_routing')
        
        if any('error' in t for t in node_types):
            patterns.append('error_handling')
        
        if any('function' in t for t in node_types):
            patterns.append('data_transformation')
        
        if any('webhook' in t for t in node_types):
            patterns.append('webhook_trigger')
        
        if any('schedule' in t for t in node_types):
            patterns.append('scheduled_execution')
        
        if any('loop' in t or 'split' in t for t in node_types):
            patterns.append('batch_processing')
        
        if any('http' in t for t in node_types):
            patterns.append('api_integration')
        
        if any('database' in t or 'postgres' in t or 'mysql' in t or 'mongo' in t for t in node_types):
            patterns.append('database_operations')
        
        return patterns
    
    async def scrape_all_categories(
        self,
        max_per_category: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape workflows from all categories.
        
        Args:
            max_per_category: Maximum workflows per category
            
        Returns:
            Dictionary mapping categories to workflows
        """
        results = {}
        
        for category in self.CATEGORIES:
            workflows = await self.scrape_category(category, max_per_category)
            results[category] = workflows
            logger.info(f"Scraped {len(workflows)} workflows from {category}")
            
            # Rate limiting between categories
            await asyncio.sleep(2.0)
        
        return results
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def main():
    """Example usage."""
    async with WorkflowScraper() as scraper:
        # Scrape IT-Ops category
        workflows = await scraper.scrape_category('it-ops', max_workflows=10)
        print(f"Scraped {len(workflows)} workflows")
        
        for wf in workflows:
            print(f"\nTitle: {wf['title']}")
            print(f"Nodes: {wf['node_count']}")
            print(f"Complexity: {wf['complexity_score']:.1f}")
            print(f"Patterns: {', '.join(wf['patterns'])}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

