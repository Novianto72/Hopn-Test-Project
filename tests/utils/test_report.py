import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class TestReporter:
    """Utility class for generating formatted test reports."""
    
    def __init__(self, test_name: str, report_dir: str = "test_reports"):
        self.test_name = test_name
        self.results = []
        self.start_time = datetime.now()
        
        # Create reports directory if it doesn't exist
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True, parents=True)
        
        # Create a sanitized filename from test name
        safe_test_name = "".join(c if c.isalnum() else "_" for c in test_name)
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.report_file = self.report_dir / f"{safe_test_name}_{timestamp}.txt"
        
        # Initialize the report file
        with open(self.report_file, 'w') as f:
            f.write(f"{'='*80}\n")
            f.write(f"TEST: {test_name.upper()}\n")
            f.write(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-" * 80 + "\n\n")
        
        # Also print to console
        print(f"\n{'='*80}")
        print(f"TEST: {test_name.upper()}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Report will be saved to: {self.report_file}")
        print("-" * 80)
    
    def add_result(
        self,
        case_name: str,
        success: bool,
        details: str,
        security_concern: bool = False,
        expected_behavior: str = "",
        actual_behavior: str = ""
    ) -> None:
        """Add a test case result to the report.
        
        Args:
            case_name: Name of the test case
            success: Whether the test case passed
            details: Detailed description of the result
            security_concern: Whether this indicates a security concern
            expected_behavior: What was expected to happen
            actual_behavior: What actually happened
        """
        result = {
            'case_name': case_name,
            'success': success,
            'details': details,
            'security_concern': security_concern,
            'expected_behavior': expected_behavior,
            'actual_behavior': actual_behavior,
            'timestamp': datetime.now()
        }
        self.results.append(result)
        
        # Format the result
        status = "✅ PASS" if success else "❌ FAIL"
        security_note = " (Security Issue)" if security_concern and not success else ""
        
        # Prepare the output
        output_lines = [
            f"\n{case_name}:",
            f"Result: {status}{security_note}",
            f"Details: {details}"
        ]
        
        if expected_behavior:
            output_lines.append(f"Expected: {expected_behavior}")
        if actual_behavior:
            output_lines.append(f"Actual: {actual_behavior}")
        if security_concern and not success:
            output_lines.append("SECURITY CONCERN: This could indicate a potential security vulnerability.")
        
        output_lines.append("-" * 40)
        output = "\n".join(output_lines)
        
        # Print to console
        print(output)
        
        # Append to report file
        with open(self.report_file, 'a') as f:
            f.write(output + "\n")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of all test results."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed
        security_issues = sum(1 for r in self.results if r['security_concern'] and not r['success'])
        
        # Prepare summary lines
        summary_lines = [
            "\n" + "="*80,
            "TEST SUMMARY",
            "-" * 80,
            f"Test: {self.test_name}",
            f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {duration.total_seconds():.2f} seconds",
            f"Total Cases: {len(self.results)}",
            f"✅ Passed: {passed}",
            f"❌ Failed: {failed}"
        ]
        
        if security_issues > 0:
            summary_lines.append(f"⚠️  Security Issues: {security_issues}")
        
        if failed > 0:
            summary_lines.extend(["", "FAILED CASES:"])
            for result in [r for r in self.results if not r['success']]:
                summary_lines.append(f"- {result['case_name']}")
        
        if security_issues > 0:
            summary_lines.extend(["", "SECURITY CONCERNS:"])
            for result in [r for r in self.results if r['security_concern'] and not r['success']]:
                summary_lines.append(f"- {result['case_name']}: {result['details']}")
        
        summary_lines.append("="*80 + "\n")
        summary = "\n".join(summary_lines)
        
        # Print to console
        print(summary)
        
        # Append to report file
        with open(self.report_file, 'a') as f:
            f.write(summary + "\n")
            f.write(f"Report saved to: {os.path.abspath(self.report_file)}\n")
        
        print(f"Report saved to: {os.path.abspath(self.report_file)}")
        
        return {
            'test_name': self.test_name,
            'start_time': self.start_time,
            'end_time': end_time,
            'duration_seconds': duration.total_seconds(),
            'total_cases': len(self.results),
            'passed': passed,
            'failed': failed,
            'security_issues': security_issues,
            'results': self.results
        }
