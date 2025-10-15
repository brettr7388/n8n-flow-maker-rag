#!/usr/bin/env python3
"""
Validate generated workflows against quality criteria
"""
import json
from pathlib import Path
import jsonschema

class WorkflowValidator:
    def __init__(self):
        self.criteria = {
            "min_nodes": 5,
            "requires_error_handling": True,
            "requires_validation": True,
            "max_simple_nodes": 3
        }
    
    def validate_workflow(self, workflow: dict) -> dict:
        """Validate a workflow and return quality scores"""
        scores = {
            "structure_valid": False,
            "has_error_handling": False,
            "has_data_validation": False,
            "complexity_appropriate": False,
            "connections_valid": False,
            "overall_score": 0
        }
        
        # Check structure
        if all(key in workflow for key in ["name", "nodes", "connections"]):
            scores["structure_valid"] = True
        
        # Check error handling
        nodes = workflow.get("nodes", [])
        node_types = [n.get("type") for n in nodes]
        if "n8n-nodes-base.errorTrigger" in node_types:
            scores["has_error_handling"] = True
        
        # Check data validation
        if any("function" in nt or "code" in nt or "if" in nt for nt in node_types if nt):
            scores["has_data_validation"] = True
        
        # Check complexity
        if len(nodes) >= self.criteria["min_nodes"]:
            scores["complexity_appropriate"] = True
        
        # Validate connections
        try:
            node_names = [n.get("name") for n in nodes]
            connections = workflow.get("connections", {})
            
            valid_connections = True
            for source, targets in connections.items():
                if source not in node_names:
                    valid_connections = False
                    break
                
                for output in targets.get("main", []):
                    for target in output:
                        if target.get("node") not in node_names:
                            valid_connections = False
                            break
            
            scores["connections_valid"] = valid_connections
        except:
            scores["connections_valid"] = False
        
        # Calculate overall score
        scores["overall_score"] = sum(
            1 for k, v in scores.items() if k != "overall_score" and v is True
        ) / (len(scores) - 1) * 100
        
        return scores
    
    def compare_with_templates(self, generated: dict, templates: list) -> dict:
        """Compare generated workflow with real templates"""
        comparison = {
            "node_count_percentile": 0,
            "node_types_overlap": 0,
            "pattern_similarity": 0
        }
        
        gen_node_count = len(generated.get("nodes", []))
        template_counts = [len(t.get("nodes", [])) for t in templates]
        
        if template_counts:
            # Percentile calculation
            below_count = sum(1 for c in template_counts if c < gen_node_count)
            comparison["node_count_percentile"] = below_count / len(template_counts) * 100
            
            # Node type overlap
            gen_types = set(n.get("type") for n in generated.get("nodes", []))
            template_types = set()
            for t in templates:
                template_types.update(n.get("type") for n in t.get("nodes", []))
            
            overlap = len(gen_types & template_types)
            comparison["node_types_overlap"] = overlap / len(gen_types) * 100 if gen_types else 0
        
        return comparison
    
    def validate_file(self, filepath: str) -> None:
        """Validate a workflow file"""
        with open(filepath) as f:
            workflow = json.load(f)
        
        scores = self.validate_workflow(workflow)
        
        print(f"\nValidation Results for: {filepath}")
        print("=" * 70)
        print(f"  Structure Valid: {'✓' if scores['structure_valid'] else '✗'}")
        print(f"  Error Handling: {'✓' if scores['has_error_handling'] else '✗'}")
        print(f"  Data Validation: {'✓' if scores['has_data_validation'] else '✗'}")
        print(f"  Complexity: {'✓' if scores['complexity_appropriate'] else '✗'}")
        print(f"  Connections: {'✓' if scores['connections_valid'] else '✗'}")
        print(f"\n  Overall Score: {scores['overall_score']:.1f}%")
        
        return scores

def main():
    validator = WorkflowValidator()
    
    # Look for generated workflows
    generated_dir = Path(__file__).parent.parent / "generated_workflows"
    
    if generated_dir.exists():
        json_files = list(generated_dir.glob("*.json"))
        
        if json_files:
            print("=" * 70)
            print("VALIDATING GENERATED WORKFLOWS")
            print("=" * 70)
            
            for filepath in json_files:
                validator.validate_file(filepath)
        else:
            print("No generated workflows found to validate.")
            print(f"Run generate_workflow.py first to create workflows in {generated_dir}")
    else:
        print(f"Generated workflows directory not found: {generated_dir}")
        print("Run generate_workflow.py first.")

if __name__ == "__main__":
    main()


