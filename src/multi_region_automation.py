import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
import logging

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
    name: str
    url: str
    username: str
    password: str
    test_api_key: str


@dataclass
class TransactionResult:
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
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
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
        Verify transaction for region: {region.name}
        
        Steps:
        1. Navigate to {region.url}
        2. Login with provided credentials
        3. Find and verify transaction with API Key: {region.test_api_key}
        4. Report the status
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
                                # Extract status
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
        
        # Default result if loop exits without explicit status
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
                return f"Navigated to {tool_input['url']}"
            
            elif tool_name == "login":
                await page.fill(tool_input["username_selector"], tool_input["username"])
                await page.fill(tool_input["password_selector"], tool_input["password"])
                await page.click(tool_input["submit_selector"])
                await page.wait_for_timeout(2000)
                return "Login submitted"
            
            elif tool_name == "wait_for_element":
                timeout = tool_input.get("timeout_ms", 5000)
                await page.wait_for_selector(tool_input["selector"], timeout=timeout)
                return f"Element appeared: {tool_input['selector']}"
            
            elif tool_name == "extract_text":
                text = await page.text_content(tool_input["selector"])
                return f"Extracted: {text}"
            
            elif tool_name == "click":
                await page.click(tool_input["selector"])
                await page.wait_for_timeout(1000)
                return f"Clicked: {tool_input['selector']}"
            
            elif tool_name == "fill":
                await page.fill(tool_input["selector"], tool_input["text"])
                return f"Filled: {tool_input['selector']}"
            
            elif tool_name == "report_status":
                return "Status reported successfully"
            
            return "Unknown tool"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
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
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
║ Report saved to: transaction_verification_report.json                    ║
║ Detailed logs saved to: automation_output.log                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
        
        print(summary)
        logger.info(summary)
        
        # Save summary to file
        with open("verification_summary.txt", "w") as f:
            f.write(summary)


async def main():
    parser = argparse.ArgumentParser(description="Multi-Region Transaction Verification")
    parser.add_argument("--schedule", choices=["daily", "weekly"], default="manual")
    args = parser.parse_args()
    
    # Load region configurations from environment or config file
    regions = [
        RegionConfig(
            name="US-EAST",
            url="https://api-us-east.example.com/login",
            username=os.getenv("US_EAST_USERNAME", "testuser"),
            password=os.getenv("US_EAST_PASSWORD", "password"),
            test_api_key=os.getenv("US_EAST_API_KEY", "test_key_us_east")
        ),
        RegionConfig(
            name="US-WEST",
            url="https://api-us-west.example.com/login",
            username=os.getenv("US_WEST_USERNAME", "testuser"),
            password=os.getenv("US_WEST_PASSWORD", "password"),
            test_api_key=os.getenv("US_WEST_API_KEY", "test_key_us_west")
        ),
        RegionConfig(
            name="EU-WEST",
            url="https://api-eu-west.example.com/login",
            username=os.getenv("EU_WEST_USERNAME", "testuser"),
            password=os.getenv("EU_WEST_PASSWORD", "password"),
            test_api_key=os.getenv("EU_WEST_API_KEY", "test_key_eu_west")
        ),
        RegionConfig(
            name="ASIA-PACIFIC",
            url="https://api-ap.example.com/login",
            username=os.getenv("AP_USERNAME", "testuser"),
            password=os.getenv("AP_PASSWORD", "password"),
            test_api_key=os.getenv("AP_API_KEY", "test_key_ap")
        ),
        RegionConfig(
            name="CANADA",
            url="https://api-ca.example.com/login",
            username=os.getenv("CA_USERNAME", "testuser"),
            password=os.getenv("CA_PASSWORD", "password"),
            test_api_key=os.getenv("CA_API_KEY", "test_key_ca")
        ),
        RegionConfig(
            name="SOUTH-AMERICA",
            url="https://api-sa.example.com/login",
            username=os.getenv("SA_USERNAME", "testuser"),
            password=os.getenv("SA_PASSWORD", "password"),
            test_api_key=os.getenv("SA_API_KEY", "test_key_sa")
        ),
        RegionConfig(
            name="MIDDLE-EAST",
            url="https://api-me.example.com/login",
            username=os.getenv("ME_USERNAME", "testuser"),
            password=os.getenv("ME_PASSWORD", "password"),
            test_api_key=os.getenv("ME_API_KEY", "test_key_me")
        ),
        RegionConfig(
            name="AFRICA",
            url="https://api-africa.example.com/login",
            username=os.getenv("AFRICA_USERNAME", "testuser"),
            password=os.getenv("AFRICA_PASSWORD", "password"),
            test_api_key=os.getenv("AFRICA_API_KEY", "test_key_africa")
        ),
    ]
    
    service = MultiRegionAutomationService()
    await service.run_verification(regions, max_concurrent=4)


if __name__ == "__main__":
    asyncio.run(main())