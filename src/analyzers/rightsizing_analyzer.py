from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import random  # For simulated metrics in MVP

logger = logging.getLogger(__name__)


class RightsizingAnalyzer:
    """analyzes resource utilization and provides rightsizing recommendations"""
    
    # GCP machine type specifications (simplified subset)
    MACHINE_TYPES = {
        'e2-micro': {'vcpus': 0.25, 'memory_gb': 1, 'cost_per_hour': 0.008},
        'e2-small': {'vcpus': 0.5, 'memory_gb': 2, 'cost_per_hour': 0.016},
        'e2-medium': {'vcpus': 1, 'memory_gb': 4, 'cost_per_hour': 0.033},
        'e2-standard-2': {'vcpus': 2, 'memory_gb': 8, 'cost_per_hour': 0.067},
        'e2-standard-4': {'vcpus': 4, 'memory_gb': 16, 'cost_per_hour': 0.134},
        'e2-standard-8': {'vcpus': 8, 'memory_gb': 32, 'cost_per_hour': 0.268},
        'n2-standard-2': {'vcpus': 2, 'memory_gb': 8, 'cost_per_hour': 0.097},
        'n2-standard-4': {'vcpus': 4, 'memory_gb': 16, 'cost_per_hour': 0.194},
        'n2-standard-8': {'vcpus': 8, 'memory_gb': 32, 'cost_per_hour': 0.388},
        'n2-highmem-2': {'vcpus': 2, 'memory_gb': 16, 'cost_per_hour': 0.131},
        'n2-highmem-4': {'vcpus': 4, 'memory_gb': 32, 'cost_per_hour': 0.262},
        'n2-highcpu-2': {'vcpus': 2, 'memory_gb': 2, 'cost_per_hour': 0.072},
        'n2-highcpu-4': {'vcpus': 4, 'memory_gb': 4, 'cost_per_hour': 0.144},
    }
    
    def __init__(self, use_simulated_metrics: bool = True):
        self.logger = logger.getChild(self.__class__.__name__)
        self.use_simulated_metrics = use_simulated_metrics
    
    def simulate_utilization_metrics(self, instance_name: str) -> Dict[str, float]:
        """
        generate simulated utilization metrics for MVP testing
    
        args:
        - instance_name: Name of the instance (used for consistent randomization)
        
        returns:
        - simulated utilization metrics
        """
        # use instance name as seed for consistent results
        random.seed(hash(instance_name) % 10000)
        
        # generate different utilization patterns
        pattern = random.choice(['underutilized', 'optimal', 'constrained', 'variable'])
        
        if pattern == 'underutilized':
            avg_cpu = random.uniform(5, 15)
            avg_memory = random.uniform(10, 25)
            peak_cpu = avg_cpu * random.uniform(1.5, 2.5)
            peak_memory = avg_memory * random.uniform(1.3, 2.0)
        elif pattern == 'optimal':
            avg_cpu = random.uniform(40, 60)
            avg_memory = random.uniform(45, 65)
            peak_cpu = avg_cpu * random.uniform(1.2, 1.4)
            peak_memory = avg_memory * random.uniform(1.2, 1.3)
        elif pattern == 'constrained':
            avg_cpu = random.uniform(70, 85)
            avg_memory = random.uniform(75, 88)
            peak_cpu = min(avg_cpu * random.uniform(1.1, 1.3), 95)
            peak_memory = min(avg_memory * random.uniform(1.1, 1.2), 98)
        else:  # variable
            avg_cpu = random.uniform(20, 70)
            avg_memory = random.uniform(30, 60)
            peak_cpu = avg_cpu * random.uniform(1.5, 2.0)
            peak_memory = avg_memory * random.uniform(1.4, 1.8)
        
        return {
            'avg_cpu_utilization': round(avg_cpu, 1),
            'avg_memory_utilization': round(avg_memory, 1),
            'peak_cpu_utilization': round(min(peak_cpu, 100), 1),
            'peak_memory_utilization': round(min(peak_memory, 100), 1),
            'data_points': 168,  # simulated 7 days of hourly data
            'data_quality': 'simulated'
        }
    
    def analyze_instance(
        self,
        instance: Dict[str, Any],
        utilization_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        analyze a single instance for rightsizing opportunities
        args:
        - instance: instance metadata including type, zone, etc.
        - utilization_data: CPU and memory utilization metrics (optional for MVP)
        
        returns:
        - rightsizing recommendation if applicable
        """
        try:
            # Extract machine type from full path
            machine_type_full = instance.get('machine_type', '')
            if '/' in machine_type_full:
                current_type = machine_type_full.split('/')[-1]
            else:
                current_type = machine_type_full
            
            if current_type not in self.MACHINE_TYPES:
                self.logger.debug(f"Unknown machine type: {current_type}")
                return None
            
            # Get or simulate utilization metrics
            if utilization_data is None and self.use_simulated_metrics:
                utilization_data = self.simulate_utilization_metrics(
                    instance.get('name', 'unknown')
                )
            elif utilization_data is None:
                # No metrics available and not simulating
                return None
            
            current_spec = self.MACHINE_TYPES[current_type]
            
            # Get utilization metrics
            avg_cpu_util = utilization_data.get('avg_cpu_utilization', 50)
            avg_memory_util = utilization_data.get('avg_memory_utilization', 50)
            peak_cpu_util = utilization_data.get('peak_cpu_utilization', avg_cpu_util * 1.5)
            peak_memory_util = utilization_data.get('peak_memory_utilization', avg_memory_util * 1.5)
            
            # Determine if rightsizing is needed
            recommendation = self._get_rightsizing_recommendation(
                current_type,
                avg_cpu_util,
                avg_memory_util,
                peak_cpu_util,
                peak_memory_util
            )
            
            if recommendation:
                recommendation.update({
                    'instance_name': instance.get('name'),
                    'instance_id': instance.get('id'),
                    'zone': instance.get('zone', 'unknown'),
                    'current_type': current_type,
                    'analysis_date': datetime.now().isoformat(),
                    'data_source': utilization_data.get('data_quality', 'unknown')
                })
                
                return recommendation
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing instance: {str(e)}")
            return None
    
    def _get_rightsizing_recommendation(
        self,
        current_type: str,
        avg_cpu: float,
        avg_memory: float,
        peak_cpu: float,
        peak_memory: float
    ) -> Optional[Dict[str, Any]]:
        """
        generate rightsizing recommendation based on utilization
        
        args:
        - current_type: current machine type
        - avg_cpu: average CPU utilization percentage
        - avg_memory: average memory utilization percentage
        - peak_cpu: peak CPU utilization percentage
        - peak_memory: peak memory utilization percentage
        
        returns:
        - recommendation dictionary or None
        """
        current_spec = self.MACHINE_TYPES[current_type]
        
        # check if instance is underutilized
        if avg_cpu < 20 and avg_memory < 30 and peak_cpu < 40:
            # find smaller instance type
            recommended_type = self._find_smaller_instance(
                current_spec,
                peak_cpu,
                peak_memory
            )
            
            if recommended_type and recommended_type != current_type:
                new_spec = self.MACHINE_TYPES[recommended_type]
                monthly_current = current_spec['cost_per_hour'] * 24 * 30
                monthly_new = new_spec['cost_per_hour'] * 24 * 30
                monthly_savings = monthly_current - monthly_new
                
                return {
                    'recommendation_type': 'downsize',
                    'recommended_type': recommended_type,
                    'reason': f"Instance is underutilized (avg CPU: {avg_cpu:.1f}%, avg memory: {avg_memory:.1f}%)",
                    'current_monthly_cost': round(monthly_current, 2),
                    'recommended_monthly_cost': round(monthly_new, 2),
                    'estimated_monthly_savings': round(monthly_savings, 2),
                    'savings_percentage': round((monthly_savings / monthly_current) * 100, 1),
                    'confidence': 'medium' if avg_cpu < 10 else 'low',  # lower confidence for simulated
                    'utilization_metrics': {
                        'avg_cpu': round(avg_cpu, 1),
                        'avg_memory': round(avg_memory, 1),
                        'peak_cpu': round(peak_cpu, 1),
                        'peak_memory': round(peak_memory, 1)
                    }
                }
        
        # check if instance needs more resources
        elif peak_cpu > 90 or peak_memory > 90:
            recommended_type = self._find_larger_instance(
                current_spec,
                peak_cpu,
                peak_memory
            )
            
            if recommended_type and recommended_type != current_type:
                new_spec = self.MACHINE_TYPES[recommended_type]
                monthly_current = current_spec['cost_per_hour'] * 24 * 30
                monthly_new = new_spec['cost_per_hour'] * 24 * 30
                monthly_increase = monthly_new - monthly_current
                
                return {
                    'recommendation_type': 'upsize',
                    'recommended_type': recommended_type,
                    'reason': f"Instance is resource-constrained (peak CPU: {peak_cpu:.1f}%, peak memory: {peak_memory:.1f}%)",
                    'current_monthly_cost': round(monthly_current, 2),
                    'recommended_monthly_cost': round(monthly_new, 2),
                    'estimated_monthly_increase': round(monthly_increase, 2),
                    'increase_percentage': round((monthly_increase / monthly_current) * 100, 1),
                    'confidence': 'medium',  # lower confidence for simulated
                    'utilization_metrics': {
                        'avg_cpu': round(avg_cpu, 1),
                        'avg_memory': round(avg_memory, 1),
                        'peak_cpu': round(peak_cpu, 1),
                        'peak_memory': round(peak_memory, 1)
                    }
                }
        
        return None
    
    def _find_smaller_instance(
        self,
        current_spec: Dict[str, float],
        peak_cpu: float,
        peak_memory: float
    ) -> Optional[str]:
        """
        find a smaller instance that can still handle peak load
        """
        # calculate required resources based on peak with 20% buffer
        required_vcpus = (current_spec['vcpus'] * peak_cpu / 100) * 1.2
        required_memory = (current_spec['memory_gb'] * peak_memory / 100) * 1.2
        
        # find the smallest instance that meets requirements
        candidates = []
        for machine_type, spec in self.MACHINE_TYPES.items():
            if (spec['vcpus'] >= required_vcpus and 
                spec['memory_gb'] >= required_memory and
                spec['cost_per_hour'] < current_spec['cost_per_hour']):
                candidates.append((machine_type, spec['cost_per_hour']))
        
        if candidates:
            # return the cheapest option that meets requirements
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]
        
        return None
    
    def _find_larger_instance(
        self,
        current_spec: Dict[str, float],
        peak_cpu: float,
        peak_memory: float
    ) -> Optional[str]:
        """
        find a larger instance to handle resource constraints
        """
        # determine which resource is constrained
        cpu_multiplier = 1.5 if peak_cpu > 90 else 1.0
        memory_multiplier = 1.5 if peak_memory > 90 else 1.0
        
        required_vcpus = current_spec['vcpus'] * cpu_multiplier
        required_memory = current_spec['memory_gb'] * memory_multiplier
        
        # find the cheapest instance that provides more resources
        candidates = []
        for machine_type, spec in self.MACHINE_TYPES.items():
            if (spec['vcpus'] >= required_vcpus and 
                spec['memory_gb'] >= required_memory and
                spec['cost_per_hour'] > current_spec['cost_per_hour']):
                candidates.append((machine_type, spec['cost_per_hour']))
        
        if candidates:
            # return the cheapest option that provides needed resources
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]
        
        return None