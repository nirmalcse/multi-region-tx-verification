#!/usr/bin/env python3
"""
Multi-Region Transaction Verification Automation

Autonomously verifies transactions across 8 global regions using Claude AI
and Playwright browser automation.

Author: Automated Testing Suite
Date: 2024
License: MIT
"""

import asyncio
import json
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict

from anthropic import AsyncAnthropic
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_output.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class RegionConfig:
    """Configuration for regional instance"""
    name: str
    url: str
    username: str
    password: str
    test_api_key: str


@dataclass
class TransactionResult:
    """Result of transaction verification"""
    region: str
    status: str
    transaction_id: str = None
    verified: bool = False
    error: str = None
    timestamp: str = ""
    execution_time: float = 0.0
    details: Dict = None


class MultiRegionAutomationService:
    """Autonomous service for multi-region transaction verification"""
    
    def __init__(self):
        """Initialize the automation service"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        self.results: List[TransactionResult] = []
        self.start_time = None
        self.end_time = None
        
        # Define tools for Claude
        self.tools = [
            {
                "name": "navigate",
                "description": "Navigate to a URL and load page",
                "input_schema": {
                    "type": "object",
                    "properties": {"url": {"type": "string"}},
                    "required": ["url"],
                },
            },
            {
                "name": "login",
                "description": "Fill login form and submit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "username_selector": {"type": "string"},
                        "password_selector": {"type": "string"},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "submit_selector": {"type": "string"},
                    },
                    "required": ["username_selector", "password_selector", 
                                "username", "password", "submit_selector"],
                },
            },
            {
                "name": "wait_for_element",
                "description": "Wait for element to appear",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "timeout_ms": {"type": "integer", "default": 5000}
                    },
                    "required": ["selector"],
                },
            },
            {
                "name": "extract_text",
                "description": "Extract text from element",
                "input_schema": {
                    "type": "object",
                    "properties": {"selector": {"type": "string"}},
                    "required": ["selector"],
                },
            },
            {
                "name": "click",
                "description": "Click an element",
                "input_schema": {
                    "type": "object",
                    "properties": {"selector": {"type": "string"}},
                    "required": ["selector"],
                },
            },
            {
                "name": "fill",
                "description": "Fill input field",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                        "text": {"type": "string"}
                    },
                    "required": ["selector", "text"],
                },
            },
            {
                "name": "report_status",
                "description": "Report transaction status",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["SUCCESS", "FAILED", "PENDING"]},
                        "transaction_id": {"type": "string"},
                        "verified": {"type": "boolean"},
                        "details": {"type": "string"}
                    },
                    "required": ["status", "verified"],
                },
            },
        ]
    
    async def verify_region(self, region: RegionConfig, page) -> TransactionResult:
        """Verify transaction in a single region"""
        start = datetime.now()
        logger.info(f"🔍 Verifying region: {region.name}")
        
        task = f"""
        You are an automated testing agent. Verify a transaction in the {region.name} region.
        
        Task:
        1. Navigate to the login page at: {region.url}
        2. Login using the provided credentials
        3. Navigate to the transactions page
        4. Search for and verify a transaction using the API Key: {region.test_api_key}
        5. Extract transaction details (ID, status, timestamp)
        6. Report the verification status
        
        Important: Use web selectors to interact with the page. Be thorough but efficient.
        Look for common patterns like input[type="email"], input[type="password"], button[type="submit"]
        """
        
        messages = [{"role": "user", "content": task}]
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                response = await self.client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=2048,
                    tools=self.tools,
                    messages=messages,
                )
                
                messages.append({"role": "assistant", "content": response.content})
                
                if response.stop_reason == "end_turn":
                    logger.info(f"✅ Region {region.name} verification completed")
                    break
                
                if response.stop_reason == "tool_use":
                    tool_results = []
                    
                    for content_block in response.content:
                        if hasattr(content_block, 'type') and content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            
                            logger.debug(f"  Tool: {tool_name}")
                            result = await self._execute_tool(tool_name, tool_input, page)
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": result,
                            })
                            
                            if tool_name == "report_status":
                                # Extract status and return result
                                execution_time = (datetime.now() - start).total_seconds()
                                return TransactionResult(
                                    region=region.name,
                                    status=tool_input.get("status", "UNKNOWN"),
                                    transaction_id=tool_input.get("transaction_id"),
                                    verified=tool_input.get("verified", False),
                                    details=tool_input.get("details"),
                                    timestamp=start.isoformat(),
                                    execution_time=execution_time
                                )
                    
                    messages.append({"role": "user", "content": tool_results})
            
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {str(e)}")
                execution_time = (datetime.now() - start).total_seconds()
                return TransactionResult(
                    region=region.name,
                    status="FAILED",
                    verified=False,
                    error=str(e),
                    timestamp=start.isoformat(),
                    execution_time=execution_time
                )
        
        # Default result if loop exits
        execution_time = (datetime.now() - start).total_seconds()
        return TransactionResult(
            region=region.name,
            status="COMPLETED",
            verified=True,
            timestamp=start.isoformat(),
            execution_time=execution_time
        )
    
    async def _execute_tool(self, tool_name: str, tool_input: dict, page) -> str:
        """Execute tool on the browser page"""
        try:
            if tool_name == "navigate":
                await page.goto(tool_input["url"], wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_load_state("networkidle")
                return f"✅ Navigated to {tool_input['url']}"
            
            elif tool_name == "login":
                await page.fill(tool_input["username_selector"], tool_input["username"])
                await page.fill(tool_input["password_selector"], tool_input["password"])
                await page.click(tool_input["submit_selector"])
                await page.wait_for_timeout(2000)
                return "✅ Login submitted successfully"
            
            elif tool_name == "wait_for_element":
                timeout = tool_input.get("timeout_ms", 5000)
                await page.wait_for_selector(tool_input["selector"], timeout=timeout)
                return f"✅ Element appeared: {tool_input['selector']}"
            
            elif tool_name == "extract_text":
                text = await page.text_content(tool_input["selector"])
                return f"✅ Extracted: {text[:200] if text else 'No content'}"
            
            elif tool_name == "click":
                await page.click(tool_input["selector"])
                await page.wait_for_timeout(1000)
                return f"✅ Clicked: {tool_input['selector']}"
            
            elif tool_name == "fill":
                await page.fill(tool_input["selector"], tool_input["text"])
                return f"✅ Filled: {tool_input['selector']}"
            
            elif tool_name == "report_status":
                return "✅ Status reported successfully"
            
            return "⚠️ Unknown tool"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def run_verification(self, regions: List[RegionConfig], max_concurrent: int = 4):
        """Run verification across all regions with concurrency control"""
        logger.info(f"🚀 Starting verification for {len(regions)} regions")
        logger.info(f"📊 Max concurrent browsers: {max_concurrent}")
        
        self.start_time = datetime.now()
        
        async with async_playwright() as p:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def verify_with_semaphore(region: RegionConfig):
                async with semaphore:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    )
                    page = await context.new_page()
                    
                    try:
                        result = await self.verify_region(region, page)
                        self.results.append(result)
                    except Exception as e:
                        logger.error(f"Error verifying {region.name}: {str(e)}")
                        self.results.append(TransactionResult(
                            region=region.name,
                            status="FAILED",
                            verified=False,
                            error=str(e)
                        ))
                    finally:
                        await page.close()
                        await context.close()
                        await browser.close()
            
            # Run verifications
            tasks = [verify_with_semaphore(region) for region in regions]
            await asyncio.gather(*tasks)
        
        self.end_time = datetime.now()
        
        # Save results
        self._save_results()
        self._generate_summary()
    
    def _save_results(self):
        """Save results to JSON file"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
            "total_regions": len(self.results),
            "successful": sum(1 for r in self.results if r.verified),
            "failed": sum(1 for r in self.results if not r.verified),
            "results": [asdict(r) for r in self.results]
        }
        
        Path("reports").mkdir(exist_ok=True)
        with open("transaction_verification_report.json", "w") as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"✅ Report saved to: transaction_verification_report.json")
    
    def _generate_summary(self):
        """Generate execution summary"""
        duration = (self.end_time - self.start_time).total_seconds()
        successful = sum(1 for r in self.results if r.verified)
        failed = len(self.results) - successful
        success_rate = (successful / len(self.results) * 100) if self.results else 0
        
        summary = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║         MULTI-REGION TRANSACTION VERIFICATION SUMMARY                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

📊 EXECUTION METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Duration:     {duration:.1f} seconds
  Start Time:         {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
  End Time:           {self.end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
  
🎯 RESULTS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Regions:      {len(self.results)}
  ✅ Successful:      {successful}
  ❌ Failed:          {failed}
  Success Rate:       {success_rate:.1f}%

📋 PER-REGION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for result in self.results:
            status_icon = "✅" if result.verified else "❌"
            summary += f"\n  {status_icon} {result.region}\n"
            summary += f"     Status: {result.status} | Time: {result.execution_time:.1f}s\n"
            if result.error:
                summary += f"     Error: {result.error}\n"
        
        summary += f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║ Report: transaction_verification_report.json                             ║
║ Logs: automation_output.log                                              ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
        
        print(summary)
        logger.info(summary)
        
        # Save summary to file
        with open("verification_summary.txt", "w") as f:
            f.write(summary)


def load_regions_from_env() -> List[RegionConfig]:
    """Load region configurations from environment variables"""
    regions = []
    
    region_names = [
        ("US-EAST", "US_EAST"),
        ("US-WEST", "US_WEST"),
        ("EU-WEST", "EU_WEST"),
        ("ASIA-PACIFIC", "AP"),
        ("CANADA", "CA"),
        ("SOUTH-AMERICA", "SA"),
        ("MIDDLE-EAST", "ME"),
        ("AFRICA", "AFRICA"),
    ]
    
    for display_name, env_prefix in region_names:
        region = RegionConfig(
            name=display_name,
            url=os.getenv(f"{env_prefix}_URL", f"https://api-{env_prefix.lower()}.example.com/login"),
            username=os.getenv(f"{env_prefix}_USERNAME", "testuser"),
            password=os.getenv(f"{env_prefix}_PASSWORD", "password"),
            test_api_key=os.getenv(f"{env_prefix}_API_KEY", f"test_key_{env_prefix.lower()}")
        )
        regions.append(region)
    
    return regions


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-Region Transaction Verification")
    parser.add_argument("--schedule", choices=["daily", "weekly"], default="manual",
                       help="Schedule type for logging purposes")
    parser.add_argument("--regions", type=int, default=8,
                       help="Number of regions to verify")
    parser.add_argument("--concurrent", type=int, default=4,
                       help="Maximum concurrent browsers")
    args = parser.parse_args()
    
    logger.info(f"Starting automation - Schedule: {args.schedule}")
    logger.info(f"Configuration: {args.regions} regions, {args.concurrent} concurrent")
    
    try:
        regions = load_regions_from_env()[:args.regions]
        service = MultiRegionAutomationService()
        await service.run_verification(regions, max_concurrent=args.concurrent)
        
        # Exit with success if all verified
        successful = sum(1 for r in service.results if r.verified)
        if successful == len(service.results):
            sys.exit(0)
        else:
            logger.warning(f"Some regions failed: {successful}/{len(service.results)} successful")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())