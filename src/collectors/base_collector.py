from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for cloud billing data collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger.getChild(self.__class__.__name__)
    
    @abstractmethod
    def authenticate(self) -> bool:
        pass
    
    @abstractmethod
    def collect_billing_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def collect_resource_data(self) -> List[Dict[str, Any]]:
        pass
    
    def validate_config(self) -> bool:
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"Missing required configuration field: {field}")
                return False
        return True
    
    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """
        Get list of required configuration fields.
        Returns:
            List of required field names
        """
        pass
    
    def get_cost_by_service(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        billing_data = self.collect_billing_data(start_date, end_date)
        cost_by_service = {}
        
        for record in billing_data:
            service = record.get('service_name', 'Unknown')
            cost = float(record.get('cost', 0))
            cost_by_service[service] = cost_by_service.get(service, 0) + cost
            
        return cost_by_service