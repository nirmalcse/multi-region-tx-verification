#!/usr/bin/env python3
"""Create execution summary for CI/CD pipeline"""

import json
from pathlib import Path
from datetime import datetime


def create_summary():
    """Create execution summary for pipeline"""
    
    report_path = Path("transaction_verification_report.json")
    
    if not report_path.exists():
        print("❌ No report found")
        return
    
    with open(report_path, "r") as f:
        data = json.load(f)
    
    successful = data['successful']
    failed = data['failed']
    total = data['total_regions']
    success_rate = (successful / total * 100) if total > 0 else 0
    duration = data['total_duration_seconds']
    
    summary = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                  VERIFICATION EXECUTION SUMMARY                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 EXECUTION RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Execution Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
  Total Duration:     {duration:.1f} seconds
  Total Regions:      {total}
  ✅ Successful:      {successful}
  ❌ Failed:          {failed}
  Success Rate:       {success_rate:.1f}%

🎯 STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if failed > 0:
        summary += "⚠️  FAILURES DETECTED - Review Required:\n\n"
        for result in data['results']:
            if not result['verified']:
                summary += f"  • {result['region']}\n"
                summary += f"    Status: {result['status']}\n"
                if result.get('error'):
                    summary += f"    Error: {result['error']}\n"
    else:
        summary += "✅ ALL REGIONS VERIFIED SUCCESSFULLY\n\n"
    
    summary += f"""
📝 GENERATED ARTIFACTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ transaction_verification_report.json
✓ reports/transaction_verification_report.html
✓ automation_output.log
✓ verification_summary.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    print(summary)
    
    with open("verification_summary.txt", "w") as f:
        f.write(summary)
    
    print(f"✅ Summary saved")


if __name__ == "__main__":
    create_summary()