import json
from pathlib import Path
from datetime import datetime


def create_summary():
    """Create execution summary for Bitbucket pipeline"""
    
    report_path = Path("transaction_verification_report.json")
    summary_path = Path("verification_summary.txt")
    
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

🎯 ACTION ITEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if failed > 0:
        summary += "\n⚠️  FAILURES DETECTED - Review Required:\n"
        for result in data['results']:
            if not result['verified']:
                summary += f"  • {result['region']}: {result.get('error', 'Verification failed')}\n"
                summary += f"    Status: {result['status']}\n"
    else:
        summary += "\n✅ ALL REGIONS VERIFIED SUCCESSFULLY\n"
    
    summary += f"""
📝 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review the full HTML report: reports/transaction_verification_report.html
2. Check detailed logs: automation_output.log
3. Download JSON report: transaction_verification_report.json
4. If failures exist, investigate and re-run verification

📂 ARTIFACTS GENERATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ transaction_verification_report.json
✓ transaction_verification_report.html
✓ automation_output.log
✓ verification_summary.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    print(summary)
    
    with open(summary_path, "w") as f:
        f.write(summary)
    
    print(f"✅ Summary saved to: {summary_path}")


if __name__ == "__main__":
    create_summary()