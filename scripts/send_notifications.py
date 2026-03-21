import json
import os
from pathlib import Path
import argparse
from datetime import datetime


def send_slack_notification(summary: dict):
    """Send notification to Slack"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️  SLACK_WEBHOOK_URL not configured")
        return
    
    import requests
    
    color = "good" if summary['failed'] == 0 else "danger"
    
    payload = {
        "attachments": [
            {
                "color": color,
                "title": "🔍 Multi-Region Transaction Verification Report",
                "text": f"Verification completed at {summary['timestamp']}",
                "fields": [
                    {
                        "title": "Total Duration",
                        "value": f"{summary['duration']:.1f}s",
                        "short": True
                    },
                    {
                        "title": "Success Rate",
                        "value": f"{summary['success_rate']:.1f}%",
                        "short": True
                    },
                    {
                        "title": "Successful",
                        "value": str(summary['successful']),
                        "short": True
                    },
                    {
                        "title": "Failed",
                        "value": str(summary['failed']),
                        "short": True
                    }
                ],
                "footer": "Automated Verification Service"
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("✅ Slack notification sent")
    except Exception as e:
        print(f"❌ Failed to send Slack notification: {e}")


def send_email_notification(summary: dict):
    """Send email notification"""
    # Implement email sending if needed
    email = os.getenv("NOTIFICATION_EMAIL")
    if not email:
        return
    
    print(f"📧 Email notification would be sent to: {email}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["immediate", "daily_summary", "weekly_summary"], 
                       default="immediate")
    args = parser.parse_args()
    
    # Load report
    report_path = Path("transaction_verification_report.json")
    if not report_path.exists():
        print("⚠️  No report found")
        return
    
    with open(report_path, "r") as f:
        data = json.load(f)
    
    summary = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "duration": data['total_duration_seconds'],
        "successful": data['successful'],
        "failed": data['failed'],
        "success_rate": (data['successful'] / data['total_regions'] * 100) if data['total_regions'] > 0 else 0
    }
    
    print(f"📤 Sending {args.type} notification...")
    send_slack_notification(summary)
    send_email_notification(summary)
    print("✅ Notifications sent")


if __name__ == "__main__":
    main()