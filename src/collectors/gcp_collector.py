import os
from typing import Dict, List, Any
from datetime import datetime
from google.cloud import billing, asset, compute
from google.oauth2 import service_account
import google.auth
import logging

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class GCPCollector(BaseCollector):
    """Google Cloud Platform data collector with service account authentication."""
    
    def __init__(self, config: Dict[str, Any]):

        super().__init__(config)
    
        self.project_id = self._get_config_value('project_id')
        self.billing_account_id = self._get_config_value('billing_account_id', required=False)
        self.service_account_path = self._get_config_value('service_account_path', required=False)
        
        self.billing_client = None
        self.asset_client = None
        self.compute_client = None
        self.credentials = None
        
    def _get_config_value(self, key: str, required: bool = True) -> str:
        """
        raises:
            ValueError: if configuration key is missing and required=True
        """
        value = self.config.get(key)
        if not value:
            if required:
                raise ValueError(f"Missing required configuration: {key}")
            return None
            
        if isinstance(value, str) and value.startswith('$'):
            env_name = value[1:]  # remove $ prefix
            env_value = os.getenv(env_name)
            if not env_value:
                if required:
                    raise ValueError(f"Environment variable {env_name} not found (referenced by {key})")
                return None
            return env_value
            
        return value
    
    def authenticate(self) -> bool:

        try:
            if self.service_account_path and self.service_account_path != 'null':
                if not os.path.exists(self.service_account_path):
                    self.logger.error(f"Service account file not found: {self.service_account_path}")
                    return False
                    
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=[
                        'https://www.googleapis.com/auth/cloud-billing.readonly',
                        'https://www.googleapis.com/auth/cloud-platform'
                    ]
                )
                self.logger.info("Using service account credentials")
            else:
                self.credentials, project = google.auth.default(
                    scopes=[
                        'https://www.googleapis.com/auth/cloud-billing.readonly',
                        'https://www.googleapis.com/auth/cloud-platform.read-only'
                    ]
                )
                self.logger.info(f"Using Application Default Credentials (detected project: {project})")
            
            self.billing_client = billing.CloudBillingClient(credentials=self.credentials)
            self.asset_client = asset.AssetServiceClient(credentials=self.credentials)
            self.compute_client = compute.InstancesClient(credentials=self.credentials)
            
            # test authentication with a simple API call
            try:
                project_name = f"projects/{self.project_id}"
                project_billing_info = self.billing_client.get_project_billing_info(name=project_name)
                self.logger.info(f"Successfully authenticated for project: {self.project_id}")
                return True
                
            except Exception as test_error:
                self.logger.error(f"Authentication test failed: {str(test_error)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def collect_billing_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        args:
            start_date: Start date for billing data collection
            end_date: End date for billing data collection
        """
        if not self.billing_client:
            raise RuntimeError("Not authenticated - call authenticate() first")
            
        billing_data = []
        
        try:
            project_name = f"projects/{self.project_id}"
            project_billing_info = self.billing_client.get_project_billing_info(name=project_name)
            
            billing_record = {
                'project_id': self.project_id,
                'billing_account_name': project_billing_info.billing_account_name,
                'billing_enabled': project_billing_info.billing_enabled,
                'collection_date': datetime.now().isoformat(),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'data_source': 'gcp_billing_api'
            }
            
            billing_data.append(billing_record)
            
            self.logger.info(f"Collected billing data for project {self.project_id}")
            
        except Exception as e:
            self.logger.error(f"Error collecting billing data: {str(e)}")
            
        return billing_data
    
    def collect_resource_data(self) -> List[Dict[str, Any]]:
        """
        returns:
            list of resource records
        """
        if not self.asset_client:
            raise RuntimeError("Not authenticated - call authenticate() first")
            
        resources = []
        
        try:
            parent = f"projects/{self.project_id}"
            
            # list all assets in the project
            request = asset.ListAssetsRequest(parent=parent)
            page_result = self.asset_client.list_assets(request=request)
            
            for asset_item in page_result:
                resource_data = {
                    'name': asset_item.name,
                    'asset_type': asset_item.asset_type,
                    'project_id': self.project_id,
                    'collection_date': datetime.now().isoformat()
                }
                
                # add resource-specific data if available
                if asset_item.resource and asset_item.resource.data:
                    # convert protobuf to dict safely
                    try:
                        resource_data['resource_data'] = dict(asset_item.resource.data)
                    except Exception:
                        # if conversion fails, just note that data exists
                        resource_data['has_resource_data'] = True
                        
                resources.append(resource_data)
                
            self.logger.info(f"Collected {len(resources)} resources from project {self.project_id}")
            
        except Exception as e:
            self.logger.error(f"Error collecting resource data: {str(e)}")
            
        return resources
    
    def get_required_config_fields(self) -> List[str]:
        """
        returns:
            list of required field names
        """
        return [
            'project_id'
        ]
    
    def get_idle_compute_instances(self) -> List[Dict[str, Any]]:
        """
        identify potentially idle Compute Engine instances
        returns:
            list of instances that might be candidates for shutdown
        """
        if not self.compute_client:
            raise RuntimeError("Not authenticated - call authenticate() first")
            
        idle_instances = []
        
        try:
            # get all zones in the project
            zones_client = compute.ZonesClient(credentials=self.credentials)
            zones_list = zones_client.list(project=self.project_id)
            
            for zone in zones_list:
                try:
                    # List instances in each zone
                    instances = self.compute_client.list(
                        project=self.project_id,
                        zone=zone.name
                    )
                    
                    for instance in instances:
                        # Check for potentially idle instances
                        if instance.status in ['STOPPED', 'SUSPENDED', 'TERMINATED']:
                            idle_instances.append({
                                'name': instance.name,
                                'zone': zone.name,
                                'status': instance.status,
                                'machine_type': instance.machine_type,
                                'creation_timestamp': instance.creation_timestamp,
                                'project_id': self.project_id,
                                'recommendation': f'Instance is {instance.status.lower()} - consider deletion if no longer needed',
                                'potential_savings': 'Exact savings require pricing API integration'
                            })
                            
                except Exception as zone_error:
                    self.logger.warning(f"Could not list instances in zone {zone.name}: {str(zone_error)}")
                    
            self.logger.info(f"Found {len(idle_instances)} potentially idle instances")
            
        except Exception as e:
            self.logger.error(f"Error identifying idle instances: {str(e)}")
            
        return idle_instances
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        returns:
            list of optimization recommendations
        """
        recommendations = []
        
        try:
            idle_instances = self.get_idle_compute_instances()
            
            for instance in idle_instances:
                recommendations.append({
                    'type': 'compute_optimization',
                    'resource_name': instance['name'],
                    'recommendation': instance['recommendation'],
                    'potential_impact': 'Cost savings from stopping unused compute resources',
                    'action': 'Review and delete if no longer needed'
                })

            
            self.logger.info(f"Generated {len(recommendations)} optimization recommendations")
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            
        return recommendations