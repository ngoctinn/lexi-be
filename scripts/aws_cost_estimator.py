#!/usr/bin/env python3
"""
AWS Cost Estimator for Lexi-BE Project

This script provides cost estimates for AWS services used in the Lexi-BE project.
It uses current AWS pricing data and allows customization of usage parameters.

Usage:
    python aws_cost_estimator.py [--region REGION] [--usage LOW|MEDIUM|HIGH]

Example:
    python aws_cost_estimator.py --region ap-southeast-1 --usage MEDIUM
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Pricing data for ap-southeast-1 (Singapore) - Updated May 2026
PRICING_DATA = {
    "ap-southeast-1": {
        "aws_lambda": {
            "requests_per_million": 0.20,  # USD
            "compute_per_gb_second": 0.0000166667,  # USD
            "free_tier": {
                "requests_per_month": 1000000,
                "duration_months": 12
            }
        },
        "amazon_dynamodb": {
            "storage_per_gb_month": 0.285,  # USD
            "read_requests_per_million": 0.1425,  # USD
            "write_requests_per_million": 0.71,  # USD
            "free_tier": {
                "storage_gb": 25,
                "duration_months": None  # Permanent
            }
        },
        "amazon_s3": {
            "storage_per_gb_month": 0.025,  # USD
            "put_requests_per_thousand": 0.0055,  # USD
            "get_requests_per_thousand": 0.00044,  # USD
            "free_tier": {
                "storage_gb": 5,
                "get_requests": 20000,
                "put_requests": 2000
            }
        },
        "amazon_api_gateway": {
            "rest_requests_per_million": 3.50,  # USD
            "websocket_per_million_minutes": 1.00,  # USD
            "free_tier": {
                "rest_requests": 1000000,
                "websocket_minutes": 750000
            }
        },
        "amazon_translate": {
            "characters_per_million": 15.00,  # USD
            "free_tier": None
        },
        "amazon_comprehend": {
            "units_per_million": 100.00,  # USD (0.0001 per unit)
            "free_tier": None
        },
        "amazon_polly": {
            "characters_per_million": 4.00,  # USD
            "free_tier": None
        },
        "amazon_bedrock": {
            "estimated_monthly": 5.00,  # USD (varies by model)
            "free_tier": None
        },
        "amazon_transcribe": {
            "minutes_per_hour": 0.024,  # USD per minute
            "free_tier": None
        }
    }
}

# Usage profiles
USAGE_PROFILES = {
    "LOW": {
        "aws_lambda": {"requests": 100000, "avg_memory_gb": 0.25, "avg_duration_seconds": 1},
        "amazon_dynamodb": {"storage_gb": 10, "read_requests": 50000, "write_requests": 20000},
        "amazon_s3": {"storage_gb": 50, "put_requests": 5000, "get_requests": 5000},
        "amazon_api_gateway": {"rest_requests": 50000, "websocket_minutes": 6000},
        "amazon_translate": {"characters": 100000},
        "amazon_comprehend": {"units": 10000},
        "amazon_polly": {"characters": 50000},
        "amazon_bedrock": {"usage_factor": 1.0},
        "amazon_transcribe": {"minutes": 100}
    },
    "MEDIUM": {
        "aws_lambda": {"requests": 500000, "avg_memory_gb": 0.25, "avg_duration_seconds": 1},
        "amazon_dynamodb": {"storage_gb": 50, "read_requests": 250000, "write_requests": 100000},
        "amazon_s3": {"storage_gb": 200, "put_requests": 25000, "get_requests": 25000},
        "amazon_api_gateway": {"rest_requests": 250000, "websocket_minutes": 30000},
        "amazon_translate": {"characters": 500000},
        "amazon_comprehend": {"units": 50000},
        "amazon_polly": {"characters": 250000},
        "amazon_bedrock": {"usage_factor": 5.0},
        "amazon_transcribe": {"minutes": 500}
    },
    "HIGH": {
        "aws_lambda": {"requests": 1000000, "avg_memory_gb": 0.25, "avg_duration_seconds": 1},
        "amazon_dynamodb": {"storage_gb": 100, "read_requests": 500000, "write_requests": 200000},
        "amazon_s3": {"storage_gb": 500, "put_requests": 50000, "get_requests": 50000},
        "amazon_api_gateway": {"rest_requests": 500000, "websocket_minutes": 60000},
        "amazon_translate": {"characters": 1000000},
        "amazon_comprehend": {"units": 100000},
        "amazon_polly": {"characters": 500000},
        "amazon_bedrock": {"usage_factor": 10.0},
        "amazon_transcribe": {"minutes": 1000}
    }
}

def calculate_service_cost(service: str, usage: Dict[str, Any], pricing: Dict[str, Any], 
                          free_tier_applied: bool = True) -> Dict[str, Any]:
    """Calculate cost for a specific service."""
    cost_details = {
        "service": service,
        "usage": usage,
        "cost_breakdown": {},
        "free_tier_applied": free_tier_applied,
        "total_cost": 0.0
    }
    
    if service == "aws_lambda":
        # Lambda cost calculation
        requests = usage["requests"]
        compute_gb_seconds = requests * usage["avg_memory_gb"] * usage["avg_duration_seconds"]
        
        # Apply free tier if applicable
        free_requests = 0
        if free_tier_applied and pricing.get("free_tier") and pricing["free_tier"].get("requests_per_month"):
            free_requests = min(requests, pricing["free_tier"]["requests_per_month"])
        
        billed_requests = max(0, requests - free_requests)
        request_cost = (billed_requests / 1000000) * pricing["requests_per_million"]
        compute_cost = compute_gb_seconds * pricing["compute_per_gb_second"]
        
        cost_details["cost_breakdown"] = {
            "requests": request_cost,
            "compute": compute_cost
        }
        cost_details["total_cost"] = request_cost + compute_cost
        
    elif service == "amazon_dynamodb":
        # DynamoDB cost calculation
        storage_gb = usage["storage_gb"]
        read_requests = usage["read_requests"]
        write_requests = usage["write_requests"]
        
        # Apply free tier for storage
        free_storage = 0
        if free_tier_applied and pricing.get("free_tier") and pricing["free_tier"].get("storage_gb"):
            free_storage = min(storage_gb, pricing["free_tier"]["storage_gb"])
        
        billed_storage = max(0, storage_gb - free_storage)
        storage_cost = billed_storage * pricing["storage_per_gb_month"]
        read_cost = (read_requests / 1000000) * pricing["read_requests_per_million"]
        write_cost = (write_requests / 1000000) * pricing["write_requests_per_million"]
        
        cost_details["cost_breakdown"] = {
            "storage": storage_cost,
            "read_requests": read_cost,
            "write_requests": write_cost
        }
        cost_details["total_cost"] = storage_cost + read_cost + write_cost
        
    elif service == "amazon_s3":
        # S3 cost calculation
        storage_gb = usage["storage_gb"]
        put_requests = usage["put_requests"]
        get_requests = usage["get_requests"]
        
        # Apply free tier
        free_storage = 0
        free_put_requests = 0
        free_get_requests = 0
        
        if free_tier_applied and pricing.get("free_tier"):
            free_storage = min(storage_gb, pricing["free_tier"]["storage_gb"])
            free_put_requests = min(put_requests, pricing["free_tier"]["put_requests"])
            free_get_requests = min(get_requests, pricing["free_tier"]["get_requests"])
        
        billed_storage = max(0, storage_gb - free_storage)
        billed_put_requests = max(0, put_requests - free_put_requests)
        billed_get_requests = max(0, get_requests - free_get_requests)
        
        storage_cost = billed_storage * pricing["storage_per_gb_month"]
        put_cost = (billed_put_requests / 1000) * pricing["put_requests_per_thousand"]
        get_cost = (billed_get_requests / 1000) * pricing["get_requests_per_thousand"]
        
        cost_details["cost_breakdown"] = {
            "storage": storage_cost,
            "put_requests": put_cost,
            "get_requests": get_cost
        }
        cost_details["total_cost"] = storage_cost + put_cost + get_cost
        
    elif service == "amazon_api_gateway":
        # API Gateway cost calculation
        rest_requests = usage["rest_requests"]
        websocket_minutes = usage["websocket_minutes"]
        
        # Apply free tier
        free_rest_requests = 0
        free_websocket_minutes = 0
        
        if free_tier_applied and pricing.get("free_tier"):
            free_rest_requests = min(rest_requests, pricing["free_tier"]["rest_requests"])
            free_websocket_minutes = min(websocket_minutes, pricing["free_tier"]["websocket_minutes"])
        
        billed_rest_requests = max(0, rest_requests - free_rest_requests)
        billed_websocket_minutes = max(0, websocket_minutes - free_websocket_minutes)
        
        rest_cost = (billed_rest_requests / 1000000) * pricing["rest_requests_per_million"]
        websocket_cost = (billed_websocket_minutes / 1000000) * pricing["websocket_per_million_minutes"]
        
        cost_details["cost_breakdown"] = {
            "rest_api": rest_cost,
            "websocket": websocket_cost
        }
        cost_details["total_cost"] = rest_cost + websocket_cost
        
    elif service == "amazon_translate":
        # Translate cost calculation
        characters = usage["characters"]
        cost = (characters / 1000000) * pricing["characters_per_million"]
        cost_details["cost_breakdown"] = {"translation": cost}
        cost_details["total_cost"] = cost
        
    elif service == "amazon_comprehend":
        # Comprehend cost calculation
        units = usage["units"]
        cost = (units / 1000000) * pricing["units_per_million"]
        cost_details["cost_breakdown"] = {"nlp_processing": cost}
        cost_details["total_cost"] = cost
        
    elif service == "amazon_polly":
        # Polly cost calculation
        characters = usage["characters"]
        cost = (characters / 1000000) * pricing["characters_per_million"]
        cost_details["cost_breakdown"] = {"speech_synthesis": cost}
        cost_details["total_cost"] = cost
        
    elif service == "amazon_bedrock":
        # Bedrock cost calculation (estimated)
        usage_factor = usage["usage_factor"]
        cost = pricing["estimated_monthly"] * usage_factor
        cost_details["cost_breakdown"] = {"ai_model_inference": cost}
        cost_details["total_cost"] = cost
        
    elif service == "amazon_transcribe":
        # Transcribe cost calculation
        minutes = usage["minutes"]
        cost = minutes * pricing["minutes_per_hour"]
        cost_details["cost_breakdown"] = {"speech_to_text": cost}
        cost_details["total_cost"] = cost
    
    return cost_details

def generate_report(region: str, usage_profile: str, free_tier: bool = True) -> Dict[str, Any]:
    """Generate a comprehensive cost estimate report."""
    if region not in PRICING_DATA:
        raise ValueError(f"Region {region} not supported. Available regions: {list(PRICING_DATA.keys())}")
    
    if usage_profile not in USAGE_PROFILES:
        raise ValueError(f"Usage profile {usage_profile} not supported. Available profiles: {list(USAGE_PROFILES.keys())}")
    
    pricing = PRICING_DATA[region]
    usage = USAGE_PROFILES[usage_profile]
    
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "region": region,
            "usage_profile": usage_profile,
            "free_tier_applied": free_tier,
            "account_id": "826229823693",
            "project": "Lexi-BE"
        },
        "services": {},
        "summary": {
            "total_monthly_cost": 0.0,
            "service_count": 0,
            "free_tier_savings": 0.0
        }
    }
    
    total_cost = 0.0
    
    # Calculate costs for all services
    for service in pricing.keys():
        if service in usage:
            service_cost = calculate_service_cost(
                service, 
                usage[service], 
                pricing[service],
                free_tier
            )
            report["services"][service] = service_cost
            total_cost += service_cost["total_cost"]
    
    report["summary"]["total_monthly_cost"] = round(total_cost, 2)
    report["summary"]["service_count"] = len(report["services"])
    
    return report

def print_report(report: Dict[str, Any], output_format: str = "text"):
    """Print the report in the specified format."""
    if output_format == "json":
        print(json.dumps(report, indent=2))
        return
    
    # Text format output
    metadata = report["metadata"]
    summary = report["summary"]
    
    print("=" * 80)
    print("AWS COST ESTIMATE REPORT - Lexi-BE Project")
    print("=" * 80)
    print(f"Generated: {metadata['generated_at']}")
    print(f"Region: {metadata['region']}")
    print(f"Usage Profile: {metadata['usage_profile']}")
    print(f"Free Tier Applied: {metadata['free_tier_applied']}")
    print(f"Account ID: {metadata['account_id']}")
    print("-" * 80)
    
    print("\nSERVICE COST BREAKDOWN:")
    print("-" * 80)
    
    for service_name, service_data in report["services"].items():
        service_display = service_name.replace("_", " ").title()
        total_cost = service_data["total_cost"]
        
        print(f"\n{service_display}: ${total_cost:.2f}/month")
        
        if service_data["cost_breakdown"]:
            for cost_type, cost_amount in service_data["cost_breakdown"].items():
                if cost_amount > 0:
                    cost_type_display = cost_type.replace("_", " ").title()
                    print(f"  • {cost_type_display}: ${cost_amount:.4f}")
    
    print("\n" + "-" * 80)
    print(f"TOTAL MONTHLY COST: ${summary['total_monthly_cost']:.2f}")
    print(f"Number of Services: {summary['service_count']}")
    print("=" * 80)
    
    # Recommendations
    print("\nRECOMMENDATIONS:")
    print("-" * 80)
    print("1. Monitor actual usage with AWS Cost Explorer")
    print("2. Set up AWS Budgets with alerts")
    print("3. Implement cost allocation tags")
    print("4. Review and optimize resource sizing monthly")
    print("5. Consider Reserved Instances/Savings Plans for predictable workloads")
    
    print("\nNOTES:")
    print("-" * 80)
    print("• Prices are estimates based on current AWS pricing")
    print("• Actual costs may vary based on usage patterns")
    print("• Free tiers may expire for new accounts after 12 months")
    print("• Data transfer costs between regions/services not included")
    print("• Taxes are not included in these estimates")

def main():
    parser = argparse.ArgumentParser(description="AWS Cost Estimator for Lexi-BE Project")
    parser.add_argument("--region", default="ap-southeast-1", 
                       help="AWS region (default: ap-southeast-1)")
    parser.add_argument("--usage", default="MEDIUM", 
                       choices=["LOW", "MEDIUM", "HIGH"],
                       help="Usage profile (default: MEDIUM)")
    parser.add_argument("--no-free-tier", action="store_true",
                       help="Disable free tier calculations")
    parser.add_argument("--format", default="text",
                       choices=["text", "json"],
                       help="Output format (default: text)")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        report = generate_report(
            region=args.region,
            usage_profile=args.usage,
            free_tier=not args.no_free_tier
        )
        
        if args.output:
            with open(args.output, 'w') as f:
                if args.format == "json":
                    json.dump(report, f, indent=2)
                else:
                    # For text format, we need to format it differently
                    import io
                    output = io.StringIO()
                    sys.stdout = output
                    print_report(report, args.format)
                    sys.stdout = sys.__stdout__
                    f.write(output.getvalue())
            print(f"Report saved to {args.output}")
        else:
            print_report(report, args.format)
            
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()