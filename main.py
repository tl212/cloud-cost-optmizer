import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.gcp_collector import GCPCollector
from src.analyzers.cost_analyzer import CostAnalyzer
from src.config_loader import load_config, expand_env_vars

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cost_optimizer.log')
    ]
)

logger = logging.getLogger(__name__)


def print_header(text: str):
    """print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_section(text: str):
    """print a formatted section header."""
    print(f"\n{'-'*70}")
    print(f"  {text}")
    print(f"{'-'*70}\n")


def main():
    """main execution function."""
    print_header("☁️  Cloud Cost Optimizer")
    
    # load configuration
    config_path = os.path.join('config', 'config.yaml')
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        print("❌ Error: config/config.yaml not found")
        print("\nPlease create a configuration file at config/config.yaml with:")
        print("  - project_id")
        print("  - billing_account_id")
        print("  - service_account_path")
        return 1
    
    try:
        config = load_config(config_path)
        config = expand_env_vars(config)
        logger.info("Configuration loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        print(f"❌ Error loading configuration: {str(e)}")
        return 1
    
    # initialize GCP collector
    print_section("🔐 Authentication")
    print(f"Project ID: {config.get('project_id', 'Not specified')}")
    print("Authenticating with GCP...")
    
    try:
        collector = GCPCollector(config)
        
        if not collector.authenticate():
            print("❌ Authentication failed")
            return 1
        
        print("✅ Successfully authenticated with GCP")
        
    except Exception as e:
        logger.error(f"Failed to initialize collector: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    # collect billing data
    print_section("💰 Collecting Billing Data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    
    try:
        billing_data = collector.collect_billing_data(start_date, end_date)
        print(f"✅ Collected {len(billing_data)} billing records")
        
    except Exception as e:
        logger.error(f"Failed to collect billing data: {str(e)}")
        print(f"❌ Error: {str(e)}")
        billing_data = []
    
    # discover resources
    print_section("🔍 Discovering Resources")
    print("Scanning project for resources...")
    
    try:
        resources = collector.collect_resource_data()
        print(f"✅ Found {len(resources)} resources in the project")
        
        # show resource type breakdown
        resource_types = {}
        for resource in resources:
            asset_type = resource.get('asset_type', 'Unknown')
            resource_types[asset_type] = resource_types.get(asset_type, 0) + 1
        
        print("\nResource type breakdown:")
        for rtype, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            short_type = rtype.split('/')[-1]
            print(f"  • {short_type}: {count}")
        
        if len(resource_types) > 10:
            print(f"  ... and {len(resource_types) - 10} more types")
        
    except Exception as e:
        logger.error(f"Failed to collect resources: {str(e)}")
        print(f"❌ Error: {str(e)}")
        resources = []
    
    # identify idle instances
    print_section("⚠️  Identifying Idle Resources")
    print("Checking for idle compute instances...")
    
    try:
        idle_instances = collector.get_idle_compute_instances()
        print(f"✅ Found {len(idle_instances)} idle compute instances")
        
        if idle_instances:
            print("\nIdle instances:")
            for instance in idle_instances:
                print(f"  • {instance['name']} ({instance['zone']})")
                print(f"    Status: {instance['status']}")
                print(f"    Recommendation: {instance['recommendation']}\n")
        else:
            print("  All instances are actively running - no idle resources detected")
        
    except Exception as e:
        logger.error(f"Failed to identify idle instances: {str(e)}")
        print(f"❌ Error: {str(e)}")
        idle_instances = []
    
    # generate recommendations
    print_section("💡 Cost Optimization Recommendations")
    
    try:
        recommendations = collector.get_cost_optimization_recommendations()
        
        if recommendations:
            print(f"Generated {len(recommendations)} recommendations:\n")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. Resource: {rec['resource_name']}")
                print(f"   Type: {rec['type']}")
                print(f"   Recommendation: {rec['recommendation']}")
                print(f"   Action: {rec['action']}\n")
        else:
            print("✅ No optimization opportunities found - your resources are efficiently utilized!")
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        print(f"❌ Error: {str(e)}")
    
    # analyze resource efficiency
    print_section("📊 Resource Efficiency Analysis")
    
    try:
        analyzer = CostAnalyzer()
        efficiency = analyzer.calculate_resource_efficiency(resources, idle_instances)
        
        print(f"Total Resources: {efficiency['total_resources']}")
        print(f"Active Resources: {efficiency['active_resources']}")
        print(f"Idle Resources: {efficiency['idle_resources']}")
        print(f"Utilization Rate: {efficiency['utilization_rate']}%")
        print(f"Efficiency Grade: {efficiency['efficiency_grade']}")
        
    except Exception as e:
        logger.error(f"Failed to analyze efficiency: {str(e)}")
        print(f"❌ Error: {str(e)}")
    
    # summary
    print_header("✨ Analysis Complete")
    print("Results saved to: cost_optimizer.log")
    print("\nNext steps:")
    print("  • Review idle resources and consider deletion")
    print("  • Implement cost alerts for budget monitoring")
    print("  • Schedule regular optimization scans")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
