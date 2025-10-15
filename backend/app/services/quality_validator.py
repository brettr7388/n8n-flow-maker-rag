"""
Workflow quality validation system.
Implements comprehensive quality scoring based on flowfix.txt requirements.
"""

from typing import Dict, List, Any, Optional
from .node_schemas import get_node_schema_validator


class QualityValidator:
    """Validates n8n workflow quality against production standards."""
    
    def __init__(self):
        self.node_validator = get_node_schema_validator()
        self.min_node_count = {
            'simple': 15,
            'standard': 25,
            'complex': 35
        }
        self.min_error_handling_percentage = 0.3
        self.min_sticky_notes = 5
        self.min_quality_score = 80
    
    def validate(self, workflow: Dict[str, Any], complexity: str = 'standard') -> Dict[str, Any]:
        """
        Run comprehensive validation checks on a workflow.
        
        Args:
            workflow: n8n workflow JSON
            complexity: 'simple', 'standard', or 'complex'
        
        Returns:
            Dict with validation results and quality score
        """
        results = {
            'node_count': self._check_node_count(workflow, complexity),
            'credentials': self._check_credentials(workflow),
            'parameters': self._check_parameters(workflow),
            'error_handling': self._check_error_handling(workflow),
            'connections': self._check_connections(workflow),
            'documentation': self._check_documentation(workflow),
            'flow_complexity': self._check_flow_complexity(workflow, complexity)
        }
        
        overall_score = self._calculate_score(results)
        
        return {
            'valid': overall_score >= self.min_quality_score,
            'score': overall_score,
            'details': results,
            'required_score': self.min_quality_score,
            'grade': self._get_grade(overall_score)
        }
    
    def _check_node_count(self, workflow: Dict[str, Any], complexity: str) -> Dict[str, Any]:
        """Check if workflow has sufficient nodes (20 points)."""
        nodes = workflow.get('nodes', [])
        node_count = len(nodes)
        required = self.min_node_count.get(complexity, 25)
        
        if node_count >= 35:
            score = 20
        elif node_count >= 25:
            score = 15
        elif node_count >= 15:
            score = 10
        elif node_count >= 10:
            score = 5
        else:
            score = 0
        
        return {
            'score': score,
            'max_score': 20,
            'node_count': node_count,
            'required': required,
            'passed': node_count >= required,
            'message': f"Node count: {node_count} (required: {required})"
        }
    
    def _check_credentials(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Check credentials configuration (15 points)."""
        nodes = workflow.get('nodes', [])
        
        # Find service nodes that require credentials
        service_nodes = []
        for node in nodes:
            if self.node_validator.requires_credentials(node.get('type', '')):
                service_nodes.append(node)
        
        if not service_nodes:
            return {
                'score': 15,
                'max_score': 15,
                'passed': True,
                'message': 'No service nodes requiring credentials'
            }
        
        # Check how many have proper credentials
        nodes_with_creds = 0
        for node in service_nodes:
            if 'credentials' in node:
                cred_type = self.node_validator.get_credential_type(node.get('type', ''))
                if cred_type and cred_type in node['credentials']:
                    nodes_with_creds += 1
        
        percentage = nodes_with_creds / len(service_nodes)
        
        if percentage >= 1.0:
            score = 15
        elif percentage >= 0.8:
            score = 12
        elif percentage >= 0.6:
            score = 9
        elif percentage >= 0.4:
            score = 6
        else:
            score = 0
        
        return {
            'score': score,
            'max_score': 15,
            'service_nodes': len(service_nodes),
            'with_credentials': nodes_with_creds,
            'percentage': percentage,
            'passed': percentage >= 0.9,
            'message': f"{nodes_with_creds}/{len(service_nodes)} service nodes have credentials"
        }
    
    def _check_parameters(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Check parameter completeness (15 points)."""
        nodes = workflow.get('nodes', [])
        
        total_nodes = len([n for n in nodes if n.get('type') != 'n8n-nodes-base.stickyNote'])
        complete_params = 0
        
        for node in nodes:
            if node.get('type') == 'n8n-nodes-base.stickyNote':
                continue
                
            validation = self.node_validator.validate_node(node)
            if validation['valid']:
                complete_params += 1
        
        if total_nodes == 0:
            percentage = 1.0
        else:
            percentage = complete_params / total_nodes
        
        if percentage >= 1.0:
            score = 15
        elif percentage >= 0.9:
            score = 12
        elif percentage >= 0.8:
            score = 9
        else:
            score = 0
        
        return {
            'score': score,
            'max_score': 15,
            'complete_nodes': complete_params,
            'total_nodes': total_nodes,
            'percentage': percentage,
            'passed': percentage >= 0.8,
            'message': f"{complete_params}/{total_nodes} nodes have complete parameters"
        }
    
    def _check_error_handling(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Check error handling coverage (20 points)."""
        nodes = workflow.get('nodes', [])
        
        # Exclude triggers and sticky notes
        processable_nodes = [
            n for n in nodes 
            if not n.get('type', '').endswith('Trigger') 
            and n.get('type') != 'n8n-nodes-base.stickyNote'
        ]
        
        if not processable_nodes:
            return {
                'score': 0,
                'max_score': 20,
                'passed': False,
                'message': 'No processable nodes found'
            }
        
        nodes_with_errors = 0
        for node in processable_nodes:
            if 'onError' in node or 'retryOnFail' in node or 'continueOnFail' in node:
                nodes_with_errors += 1
        
        percentage = nodes_with_errors / len(processable_nodes)
        
        if percentage >= 0.5:
            score = 20
        elif percentage >= 0.4:
            score = 16
        elif percentage >= 0.3:
            score = 12
        elif percentage >= 0.2:
            score = 8
        else:
            score = 0
        
        return {
            'score': score,
            'max_score': 20,
            'nodes_with_error_handling': nodes_with_errors,
            'total_nodes': len(processable_nodes),
            'percentage': percentage,
            'passed': percentage >= self.min_error_handling_percentage,
            'message': f"{nodes_with_errors}/{len(processable_nodes)} nodes have error handling ({percentage:.0%})"
        }
    
    def _check_connections(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Check if all nodes are properly connected (5 points)."""
        nodes = workflow.get('nodes', [])
        connections = workflow.get('connections', {})
        
        # Get all node names
        node_names = {n['name'] for n in nodes}
        
        # Find trigger nodes (should not have incoming connections)
        trigger_nodes = {
            n['name'] for n in nodes 
            if n.get('type', '').endswith('Trigger')
        }
        
        # Find sticky notes (don't need connections)
        sticky_notes = {
            n['name'] for n in nodes
            if n.get('type') == 'n8n-nodes-base.stickyNote'
        }
        
        # Nodes that should have incoming connections
        nodes_needing_input = node_names - trigger_nodes - sticky_notes
        
        # Find nodes with incoming connections
        nodes_with_input = set()
        for source_node, conn_data in connections.items():
            for conn_type, conn_lists in conn_data.items():
                for conn_list in conn_lists:
                    for conn in conn_list:
                        nodes_with_input.add(conn['node'])
        
        # Check if all required nodes have connections
        unconnected = nodes_needing_input - nodes_with_input
        
        if len(unconnected) == 0:
            score = 5
            passed = True
        else:
            score = 0
            passed = False
        
        return {
            'score': score,
            'max_score': 5,
            'passed': passed,
            'unconnected_nodes': list(unconnected),
            'message': f"{len(nodes_with_input)}/{len(nodes_needing_input)} required nodes connected"
        }
    
    def _check_documentation(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Check documentation via sticky notes (10 points)."""
        nodes = workflow.get('nodes', [])
        
        sticky_notes = [
            n for n in nodes 
            if n.get('type') == 'n8n-nodes-base.stickyNote'
        ]
        
        count = len(sticky_notes)
        
        if count >= 8:
            score = 10
        elif count >= 5:
            score = 7
        elif count >= 3:
            score = 4
        else:
            score = 0
        
        return {
            'score': score,
            'max_score': 10,
            'sticky_note_count': count,
            'required': self.min_sticky_notes,
            'passed': count >= self.min_sticky_notes,
            'message': f"{count} sticky notes (minimum: {self.min_sticky_notes})"
        }
    
    def _check_flow_complexity(self, workflow: Dict[str, Any], complexity: str) -> Dict[str, Any]:
        """Check flow orchestration complexity (15 points)."""
        nodes = workflow.get('nodes', [])
        
        has_if_nodes = any(n['type'] == 'n8n-nodes-base.if' for n in nodes)
        has_switch_nodes = any(n['type'] == 'n8n-nodes-base.switch' for n in nodes)
        has_merge_nodes = any(n['type'] == 'n8n-nodes-base.merge' for n in nodes)
        has_set_nodes = any(n['type'] == 'n8n-nodes-base.set' for n in nodes)
        has_code_nodes = any(n.get('type') in ['n8n-nodes-base.code', 'n8n-nodes-base.function'] for n in nodes)
        
        features = []
        if has_if_nodes or has_switch_nodes:
            features.append('conditional logic')
        if has_merge_nodes:
            features.append('merging')
        if has_set_nodes:
            features.append('data transformation')
        if has_code_nodes:
            features.append('custom logic')
        
        feature_count = len(features)
        
        # For simple workflows, less complexity is OK
        if complexity == 'simple':
            if feature_count >= 2:
                score = 15
            elif feature_count >= 1:
                score = 10
            else:
                score = 5
        # For standard/complex workflows, require more
        else:
            if feature_count >= 3:
                score = 15
            elif feature_count >= 2:
                score = 10
            elif feature_count >= 1:
                score = 5
            else:
                score = 0
        
        return {
            'score': score,
            'max_score': 15,
            'features': features,
            'feature_count': feature_count,
            'passed': feature_count >= (1 if complexity == 'simple' else 2),
            'message': f"Flow features: {', '.join(features) if features else 'none'}"
        }
    
    def _calculate_score(self, results: Dict[str, Dict]) -> int:
        """Calculate overall quality score (0-100)."""
        total = sum(result['score'] for result in results.values())
        return total
    
    def _get_grade(self, score: int) -> str:
        """Get letter grade for score."""
        if score >= 90:
            return 'A (Excellent)'
        elif score >= 80:
            return 'B (Good)'
        elif score >= 70:
            return 'C (Acceptable)'
        elif score >= 60:
            return 'D (Needs Improvement)'
        else:
            return 'F (Poor)'
    
    def generate_feedback(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate actionable feedback for improvement."""
        feedback = []
        details = validation_result['details']
        
        # Node count feedback
        if not details['node_count']['passed']:
            feedback.append(
                f"CRITICAL: Workflow has only {details['node_count']['node_count']} nodes. "
                f"Add more nodes to reach {details['node_count']['required']} nodes minimum."
            )
        
        # Credentials feedback
        if not details['credentials']['passed']:
            feedback.append(
                f"CRITICAL: {details['credentials']['service_nodes'] - details['credentials']['with_credentials']} "
                f"service nodes missing credentials configuration."
            )
        
        # Parameters feedback
        if not details['parameters']['passed']:
            feedback.append(
                f"CRITICAL: {details['parameters']['total_nodes'] - details['parameters']['complete_nodes']} "
                f"nodes have incomplete or missing parameters."
            )
        
        # Error handling feedback
        if not details['error_handling']['passed']:
            feedback.append(
                f"WARNING: Only {details['error_handling']['percentage']:.0%} of nodes have error handling. "
                f"Add onError, retryOnFail, or continueOnFail to critical nodes."
            )
        
        # Connections feedback
        if not details['connections']['passed']:
            unconnected = details['connections']['unconnected_nodes']
            feedback.append(
                f"CRITICAL: {len(unconnected)} nodes are not connected: {', '.join(unconnected[:3])}"
            )
        
        # Documentation feedback
        if not details['documentation']['passed']:
            needed = details['documentation']['required'] - details['documentation']['sticky_note_count']
            feedback.append(
                f"WARNING: Add {needed} more sticky notes to document workflow sections."
            )
        
        # Flow complexity feedback
        if not details['flow_complexity']['passed']:
            feedback.append(
                f"WARNING: Workflow lacks complexity features. Add IF/Switch nodes for branching, "
                f"Merge nodes for parallel paths, or Set nodes for data transformation."
            )
        
        return feedback


# Global instance
_quality_validator_instance = None


def get_quality_validator() -> QualityValidator:
    """Get singleton instance of quality validator."""
    global _quality_validator_instance
    if _quality_validator_instance is None:
        _quality_validator_instance = QualityValidator()
    return _quality_validator_instance


