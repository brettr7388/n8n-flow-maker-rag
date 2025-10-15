#!/usr/bin/env python3
"""
Analyze n8n templates to extract patterns and metadata
"""
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List
import pandas as pd

class TemplateAnalyzer:
    def __init__(self, templates_dir="../processed_templates"):
        self.templates_dir = Path(__file__).parent.parent / templates_dir.lstrip('../')
        self.workflows = []
        self.analysis = {
            "node_types": Counter(),
            "node_combinations": Counter(),
            "complexity_distribution": defaultdict(int),
            "patterns": defaultdict(list),
            "use_cases": defaultdict(list)
        }
    
    def load_workflows(self):
        """Load all validated workflows"""
        json_files = list(self.templates_dir.rglob("*.json"))
        
        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['filepath'] = str(filepath)
                    self.workflows.append(data)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        print(f"Loaded {len(self.workflows)} workflows")
    
    def analyze_node_usage(self):
        """Analyze which nodes are most commonly used"""
        for workflow in self.workflows:
            for node in workflow.get('nodes', []):
                node_type = node.get('type', 'unknown')
                self.analysis['node_types'][node_type] += 1
        
        print("\nTop 20 Most Used Nodes:")
        for node_type, count in self.analysis['node_types'].most_common(20):
            print(f"  {node_type}: {count}")
    
    def analyze_complexity(self):
        """Categorize workflows by complexity"""
        for workflow in self.workflows:
            node_count = len(workflow.get('nodes', []))
            
            if node_count <= 5:
                complexity = "simple"
            elif node_count <= 15:
                complexity = "medium"
            else:
                complexity = "complex"
            
            self.analysis['complexity_distribution'][complexity] += 1
            
            # Add complexity metadata
            workflow['complexity'] = complexity
            workflow['node_count'] = node_count
        
        print("\nComplexity Distribution:")
        for complexity, count in self.analysis['complexity_distribution'].items():
            print(f"  {complexity}: {count}")
    
    def detect_patterns(self):
        """Detect common workflow patterns"""
        for workflow in self.workflows:
            nodes = workflow.get('nodes', [])
            node_types = [n.get('type', '') for n in nodes]
            
            # Detect webhook + processing + action pattern
            if 'n8n-nodes-base.webhook' in node_types:
                if any('function' in nt or 'code' in nt for nt in node_types):
                    self.analysis['patterns']['webhook_processing_action'].append(workflow.get('name', 'Untitled'))
            
            # Detect error handling
            if 'n8n-nodes-base.errorTrigger' in node_types:
                self.analysis['patterns']['error_handling'].append(workflow.get('name', 'Untitled'))
            
            # Detect API polling
            if 'n8n-nodes-base.cron' in node_types and 'n8n-nodes-base.httpRequest' in node_types:
                self.analysis['patterns']['api_polling'].append(workflow.get('name', 'Untitled'))
            
            # Detect database workflows
            if any('postgres' in nt or 'mysql' in nt or 'mongodb' in nt for nt in node_types):
                self.analysis['patterns']['database_operations'].append(workflow.get('name', 'Untitled'))
            
            # Detect AI/ML workflows
            if any('openai' in nt.lower() or 'pinecone' in nt.lower() for nt in node_types):
                self.analysis['patterns']['ai_ml'].append(workflow.get('name', 'Untitled'))
        
        print("\nDetected Patterns:")
        for pattern, workflows in self.analysis['patterns'].items():
            print(f"  {pattern}: {len(workflows)} workflows")
    
    def generate_metadata(self):
        """Generate metadata file for all workflows"""
        metadata = []
        
        for workflow in self.workflows:
            nodes = workflow.get('nodes', [])
            node_types = [n.get('type', '') for n in nodes]
            
            meta = {
                "name": workflow.get('name', 'Untitled'),
                "filepath": workflow.get('filepath', ''),
                "node_count": len(nodes),
                "complexity": workflow.get('complexity', 'unknown'),
                "node_types": list(set(node_types)),
                "has_error_handling": 'n8n-nodes-base.errorTrigger' in node_types,
                "has_webhook": 'n8n-nodes-base.webhook' in node_types,
                "has_database": any('postgres' in nt or 'mysql' in nt for nt in node_types),
                "has_ai": any('openai' in nt.lower() for nt in node_types),
                "connection_count": sum(len(conns.get('main', [])) for conns in workflow.get('connections', {}).values())
            }
            
            metadata.append(meta)
        
        # Save to CSV
        df = pd.DataFrame(metadata)
        csv_path = self.templates_dir.parent / "workflow_metadata.csv"
        df.to_csv(csv_path, index=False)
        
        # Save to JSON
        json_path = self.templates_dir.parent / "workflow_metadata.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nMetadata saved for {len(metadata)} workflows")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("=" * 70)
        print("TEMPLATE ANALYSIS")
        print("=" * 70)
        
        self.load_workflows()
        self.analyze_node_usage()
        self.analyze_complexity()
        self.detect_patterns()
        self.generate_metadata()
        
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)

def main():
    analyzer = TemplateAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()


