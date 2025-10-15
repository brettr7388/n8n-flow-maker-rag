#!/usr/bin/env python3
"""
Test script for enhanced workflow generator.
Tests generation with sample workflows and validates quality scores.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add app directory to path
app_path = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_path))

try:
    from services.enhanced_workflow_generator import get_enhanced_workflow_generator
    from services.quality_validator import get_quality_validator
    from services.node_schemas import get_node_schema_validator
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Error importing services: {e}")
    SERVICES_AVAILABLE = False


class WorkflowGeneratorTester:
    """Tests the enhanced workflow generator with various scenarios."""
    
    def __init__(self):
        if not SERVICES_AVAILABLE:
            raise ImportError("Required services not available")
        
        self.generator = get_enhanced_workflow_generator()
        self.validator = get_quality_validator()
        self.node_validator = get_node_schema_validator()
    
    def run_all_tests(self):
        """Run all test scenarios."""
        print("\n" + "="*70)
        print("ENHANCED WORKFLOW GENERATOR TEST SUITE")
        print("="*70)
        
        test_cases = [
            self._test_simple_workflow(),
            self._test_standard_workflow(),
            self._test_complex_workflow(),
            self._test_social_media_workflow(),
            self._test_ai_workflow()
        ]
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for result in test_cases if result.get('passed'))
        total = len(test_cases)
        
        print(f"\nTests Passed: {passed}/{total}")
        
        for i, result in enumerate(test_cases, 1):
            status = "✓ PASS" if result.get('passed') else "✗ FAIL"
            print(f"{status} - Test {i}: {result.get('name')}")
            if result.get('quality_score'):
                print(f"      Quality Score: {result['quality_score']}/100")
        
        return passed == total
    
    def _test_simple_workflow(self) -> Dict[str, Any]:
        """Test simple workflow generation."""
        print("\n" + "-"*70)
        print("TEST 1: Simple Webhook to Email Workflow")
        print("-"*70)
        
        try:
            result = self.generator.generate(
                user_request="Create a simple workflow that sends an email when a webhook receives data",
                complexity='simple',
                integrations=['webhook', 'email']
            )
            
            return self._validate_result(result, 'Simple Webhook to Email', 'simple')
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            return {'passed': False, 'name': 'Simple Workflow', 'error': str(e)}
    
    def _test_standard_workflow(self) -> Dict[str, Any]:
        """Test standard complexity workflow."""
        print("\n" + "-"*70)
        print("TEST 2: Standard Lead Processing Workflow")
        print("-"*70)
        
        try:
            result = self.generator.generate(
                user_request="Create a lead processing workflow that validates data, checks for duplicates, scores leads, and routes them based on priority",
                complexity='standard',
                integrations=['webhook', 'database', 'email', 'slack']
            )
            
            return self._validate_result(result, 'Standard Lead Processing', 'standard')
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            return {'passed': False, 'name': 'Standard Workflow', 'error': str(e)}
    
    def _test_complex_workflow(self) -> Dict[str, Any]:
        """Test complex workflow generation."""
        print("\n" + "-"*70)
        print("TEST 3: Complex AI-Powered Multi-Channel Workflow")
        print("-"*70)
        
        try:
            result = self.generator.generate(
                user_request="Create an advanced workflow that monitors trending topics, generates AI content, creates videos, and posts to multiple social media platforms with error handling",
                complexity='complex',
                integrations=['schedule', 'ai', 'openai', 'http_request', 'social_media']
            )
            
            return self._validate_result(result, 'Complex AI Multi-Channel', 'complex')
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            return {'passed': False, 'name': 'Complex Workflow', 'error': str(e)}
    
    def _test_social_media_workflow(self) -> Dict[str, Any]:
        """Test social media automation workflow."""
        print("\n" + "-"*70)
        print("TEST 4: Social Media Content Distribution")
        print("-"*70)
        
        try:
            result = self.generator.generate(
                user_request="Create a workflow that reads content from Google Sheets and posts to Instagram, TikTok, Twitter, and Facebook",
                use_case='social_media',
                complexity='standard',
                integrations=['google_sheets', 'instagram', 'tiktok', 'twitter', 'facebook']
            )
            
            return self._validate_result(result, 'Social Media Distribution', 'standard')
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            return {'passed': False, 'name': 'Social Media Workflow', 'error': str(e)}
    
    def _test_ai_workflow(self) -> Dict[str, Any]:
        """Test AI-powered workflow."""
        print("\n" + "-"*70)
        print("TEST 5: AI Content Generation and Publishing")
        print("-"*70)
        
        try:
            result = self.generator.generate(
                user_request="Create an AI workflow that generates blog posts, creates social media summaries, and publishes to multiple platforms",
                use_case='ai_content',
                complexity='standard',
                integrations=['openai', 'langchain', 'wordpress', 'social_media']
            )
            
            return self._validate_result(result, 'AI Content Generation', 'standard')
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            return {'passed': False, 'name': 'AI Workflow', 'error': str(e)}
    
    def _validate_result(self, result: Dict[str, Any], name: str, complexity: str) -> Dict[str, Any]:
        """Validate a generation result."""
        
        # Extract workflow
        workflow = result if 'workflow' not in result else result['workflow']
        
        # Basic structure check
        if not workflow or 'nodes' not in workflow:
            print("✗ Invalid workflow structure")
            return {'passed': False, 'name': name, 'error': 'Invalid structure'}
        
        nodes = workflow.get('nodes', [])
        node_count = len(nodes)
        
        print(f"\n✓ Workflow generated successfully")
        print(f"  Name: {workflow.get('name', 'Untitled')}")
        print(f"  Node count: {node_count}")
        
        # Quality validation
        quality_result = self.validator.validate(workflow, complexity)
        
        print(f"\nQuality Assessment:")
        print(f"  Score: {quality_result['score']}/100")
        print(f"  Grade: {quality_result['grade']}")
        print(f"  Valid: {quality_result['valid']}")
        
        # Detailed checks
        details = quality_result.get('details', {})
        
        print(f"\nDetailed Results:")
        for check_name, check_result in details.items():
            status = "✓" if check_result.get('passed', False) else "✗"
            score = check_result.get('score', 0)
            max_score = check_result.get('max_score', 0)
            message = check_result.get('message', '')
            print(f"  {status} {check_name}: {score}/{max_score} - {message}")
        
        # Node validation
        print(f"\nNode Validation:")
        invalid_nodes = 0
        for node in nodes:
            validation = self.node_validator.validate_node(node)
            if not validation['valid']:
                invalid_nodes += 1
                print(f"  ✗ {node.get('name', 'Unknown')}")
                for error in validation['errors']:
                    print(f"      - {error}")
        
        if invalid_nodes == 0:
            print("  ✓ All nodes valid")
        else:
            print(f"  ⚠ {invalid_nodes} nodes have issues")
        
        # Check if test passed
        min_score = 70  # Allow 70+ for tests (80+ is production)
        passed = quality_result['score'] >= min_score and invalid_nodes < node_count * 0.2
        
        if passed:
            print(f"\n✓ Test PASSED (score >= {min_score})")
        else:
            print(f"\n✗ Test FAILED (score < {min_score})")
        
        # Save workflow for inspection
        output_dir = Path(__file__).parent.parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{name.lower().replace(' ', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2)
        
        print(f"\n💾 Saved to: {output_file}")
        
        return {
            'passed': passed,
            'name': name,
            'quality_score': quality_result['score'],
            'node_count': node_count,
            'invalid_nodes': invalid_nodes
        }


def main():
    """Main entry point."""
    
    if not SERVICES_AVAILABLE:
        print("Error: Required services not available")
        print("Make sure you're running from the correct directory")
        return
    
    try:
        tester = WorkflowGeneratorTester()
        all_passed = tester.run_all_tests()
        
        if all_passed:
            print("\n" + "="*70)
            print("✓ ALL TESTS PASSED")
            print("="*70)
            sys.exit(0)
        else:
            print("\n" + "="*70)
            print("✗ SOME TESTS FAILED")
            print("="*70)
            sys.exit(1)
            
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


