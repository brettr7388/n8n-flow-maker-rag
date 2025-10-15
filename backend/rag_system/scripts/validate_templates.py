#!/usr/bin/env python3
"""
Validate and clean n8n workflow templates
"""
import json
import jsonschema
from pathlib import Path
from typing import Dict, List
import shutil

# n8n workflow JSON schema
N8N_SCHEMA = {
    "type": "object",
    "required": ["nodes"],
    "properties": {
        "name": {"type": "string"},
        "nodes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "type", "parameters"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "typeVersion": {"type": "number"},
                    "position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "parameters": {"type": "object"}
                }
            }
        },
        "connections": {"type": "object"}
    }
}

class TemplateValidator:
    def __init__(self, input_dir="../raw_templates", output_dir="../processed_templates"):
        self.input_dir = Path(__file__).parent.parent / input_dir.lstrip('../')
        self.output_dir = Path(__file__).parent.parent / output_dir.lstrip('../')
        self.output_dir.mkdir(exist_ok=True)
        
        self.stats = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "errors": []
        }
    
    def validate_workflow(self, filepath: Path) -> bool:
        """Validate a single workflow file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate against schema
            jsonschema.validate(instance=data, schema=N8N_SCHEMA)
            
            # Additional validation rules
            if not data.get('nodes'):
                raise ValueError("No nodes found")
            
            if len(data['nodes']) < 2:
                raise ValueError("Too few nodes (minimum 2)")
            
            # Validate node names are unique
            node_names = [node['name'] for node in data['nodes']]
            if len(node_names) != len(set(node_names)):
                raise ValueError("Duplicate node names found")
            
            # Validate connections reference existing nodes
            for source_node, connections in data.get('connections', {}).items():
                if source_node not in node_names:
                    raise ValueError(f"Connection references non-existent node: {source_node}")
                
                for outputs in connections.get('main', []):
                    for output in outputs:
                        target_node = output.get('node')
                        if target_node not in node_names:
                            raise ValueError(f"Connection references non-existent target: {target_node}")
            
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                "file": str(filepath),
                "error": str(e)
            })
            return False
    
    def clean_workflow(self, data: Dict) -> Dict:
        """Clean and normalize workflow data"""
        # Remove test/example credentials
        for node in data.get('nodes', []):
            if 'credentials' in node:
                for cred_type, cred_data in node['credentials'].items():
                    if isinstance(cred_data, dict):
                        cred_data['id'] = 'PLACEHOLDER_CREDENTIAL_ID'
        
        # Add metadata
        if 'meta' not in data:
            data['meta'] = {}
        
        data['meta']['source'] = 'rag_training_data'
        data['meta']['validated'] = True
        
        return data
    
    def process_all(self):
        """Process all templates"""
        print("Validating and cleaning templates...")
        
        # Find all JSON files recursively
        json_files = list(self.input_dir.rglob("*.json"))
        self.stats['total'] = len(json_files)
        
        print(f"Found {len(json_files)} JSON files to process")
        
        for filepath in json_files:
            if self.validate_workflow(filepath):
                # Valid workflow - clean and copy
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    cleaned_data = self.clean_workflow(data)
                    
                    # Create output path maintaining directory structure
                    rel_path = filepath.relative_to(self.input_dir)
                    output_path = self.output_dir / rel_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_data, f, indent=2)
                    
                    self.stats['valid'] += 1
                except Exception as e:
                    print(f"Error cleaning {filepath}: {e}")
                    self.stats['invalid'] += 1
            else:
                self.stats['invalid'] += 1
        
        print(f"\nValidation Results:")
        print(f"  Total files: {self.stats['total']}")
        print(f"  Valid: {self.stats['valid']}")
        print(f"  Invalid: {self.stats['invalid']}")
        if self.stats['total'] > 0:
            print(f"  Success rate: {self.stats['valid']/self.stats['total']*100:.1f}%")
        
        if self.stats['errors']:
            print(f"\nTop errors:")
            error_counts = {}
            for error in self.stats['errors'][:10]:
                err_msg = error['error']
                error_counts[err_msg] = error_counts.get(err_msg, 0) + 1
            
            for err_msg, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {err_msg}: {count} times")

def main():
    validator = TemplateValidator()
    validator.process_all()

if __name__ == "__main__":
    main()


