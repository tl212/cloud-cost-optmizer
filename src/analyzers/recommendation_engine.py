from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RecommendationPriority(Enum):
    CRITICAL = 1  # immediate action needed
    HIGH = 2      # significant savings opportunity
    MEDIUM = 3    # moderate savings opportunity
    LOW = 4       # minor optimization


class RecommendationEngine:
    """consolidates and prioritizes cost optimization recommendations"""
    
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
        self.recommendations = []
    
    def add_idle_instance_recommendations(
        self,
        idle_instances: List[Dict[str, Any]]
    ) -> None:
        
        for instance in idle_instances:
            # estimate monthly cost based on instance type
            estimated_monthly_cost = self._estimate_instance_cost(instance)
            
            rec = {
                'type': 'idle_instance',
                'resource_type': 'compute_instance',
                'resource_name': instance.get('name'),
                'resource_id': instance.get('id'),
                'status': instance.get('status', 'UNKNOWN'),
                'recommendation': f"Instance is {instance.get('status', 'idle').lower()} - consider deletion",
                'action': 'Delete instance if no longer needed',
                'estimated_monthly_savings': estimated_monthly_cost,
                'priority': RecommendationPriority.HIGH if estimated_monthly_cost > 100 else RecommendationPriority.MEDIUM,
                'confidence': 'high',
                'risk_level': 'low',
                'implementation_effort': 'easy',
                'automation_possible': True
            }
            self.recommendations.append(rec)
    
    def add_rightsizing_recommendations(
        self,
        rightsizing_recs: List[Dict[str, Any]]
    ) -> None:
        for rec in rightsizing_recs:
            priority = self._calculate_priority(
                rec.get('estimated_monthly_savings', 0),
                rec.get('confidence', 'low')
            )
            
            formatted_rec = {
                'type': 'rightsizing',
                'resource_type': 'compute_instance',
                'resource_name': rec.get('instance_name'),
                'resource_id': rec.get('instance_id'),
                'current_type': rec.get('current_type'),
                'recommended_type': rec.get('recommended_type'),
                'recommendation': rec.get('reason'),
                'action': f"Change instance type from {rec.get('current_type')} to {rec.get('recommended_type')}",
                'estimated_monthly_savings': rec.get('estimated_monthly_savings', 0),
                'estimated_monthly_increase': rec.get('estimated_monthly_increase', 0),
                'priority': priority,
                'confidence': rec.get('confidence', 'low'),
                'risk_level': 'medium' if rec.get('recommendation_type') == 'downsize' else 'low',
                'implementation_effort': 'moderate',
                'automation_possible': True,
                'utilization_metrics': rec.get('utilization_metrics', {})
            }
            self.recommendations.append(formatted_rec)
    
    def add_unused_resource_recommendations(
        self,
        unused_resources: List[Dict[str, Any]]
    ) -> None:
        for resource in unused_resources:
            resource_type = resource.get('type', 'unknown')
            estimated_cost = self._estimate_resource_cost(resource)
            
            rec = {
                'type': 'unused_resource',
                'resource_type': resource_type,
                'resource_name': resource.get('name'),
                'resource_id': resource.get('id'),
                'recommendation': f"Unused {resource_type} detected",
                'action': f"Delete unused {resource_type}",
                'estimated_monthly_savings': estimated_cost,
                'priority': RecommendationPriority.MEDIUM if estimated_cost > 50 else RecommendationPriority.LOW,
                'confidence': 'high',
                'risk_level': 'low' if 'snapshot' in resource_type else 'medium',
                'implementation_effort': 'easy',
                'automation_possible': True
            }
            self.recommendations.append(rec)
    
    def add_cost_anomaly_recommendations(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> None:
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'medium')
            priority = (RecommendationPriority.CRITICAL if severity == 'high' 
                       else RecommendationPriority.HIGH)
            
            rec = {
                'type': 'cost_anomaly',
                'resource_type': 'billing',
                'date': anomaly.get('date'),
                'recommendation': f"Cost spike detected on {anomaly.get('date')}",
                'action': f"Investigate {anomaly.get('deviation_percentage', 0):.1f}% cost increase",
                'anomaly_details': {
                    'actual_cost': anomaly.get('cost'),
                    'expected_cost': anomaly.get('average_cost'),
                    'deviation_percentage': anomaly.get('deviation_percentage')
                },
                'priority': priority,
                'confidence': 'medium',
                'risk_level': 'none',
                'implementation_effort': 'investigation_required',
                'automation_possible': False
            }
            self.recommendations.append(rec)
    
    def get_prioritized_recommendations(
        self,
        max_recommendations: Optional[int] = None,
        min_savings: float = 0
    ) -> List[Dict[str, Any]]:
        # filter by minimum savings
        filtered = [
            rec for rec in self.recommendations
            if rec.get('estimated_monthly_savings', 0) >= min_savings
        ]
        
        # sort by priority (ascending) and savings (descending)
        sorted_recs = sorted(
            filtered,
            key=lambda x: (
                x.get('priority', RecommendationPriority.LOW).value,
                -x.get('estimated_monthly_savings', 0)
            )
        )
        
        # apply max limit if specified
        if max_recommendations:
            sorted_recs = sorted_recs[:max_recommendations]
        
        # add ranking
        for i, rec in enumerate(sorted_recs, 1):
            rec['rank'] = i
            rec['priority_label'] = rec.get('priority', RecommendationPriority.LOW).name
        
        return sorted_recs
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        total_savings = sum(
            rec.get('estimated_monthly_savings', 0) 
            for rec in self.recommendations
        )
        
        total_increases = sum(
            rec.get('estimated_monthly_increase', 0)
            for rec in self.recommendations
        )
        
        by_type = {}
        for rec in self.recommendations:
            rec_type = rec.get('type', 'unknown')
            if rec_type not in by_type:
                by_type[rec_type] = {
                    'count': 0,
                    'total_savings': 0,
                    'total_increase': 0
                }
            by_type[rec_type]['count'] += 1
            by_type[rec_type]['total_savings'] += rec.get('estimated_monthly_savings', 0)
            by_type[rec_type]['total_increase'] += rec.get('estimated_monthly_increase', 0)
        
        # count by priority
        by_priority = {}
        for priority in RecommendationPriority:
            count = sum(1 for rec in self.recommendations 
                       if rec.get('priority') == priority)
            if count > 0:
                by_priority[priority.name] = count
        
        # count automatable recommendations
        automatable = sum(1 for rec in self.recommendations 
                         if rec.get('automation_possible', False))
        
        return {
            'total_recommendations': len(self.recommendations),
            'total_monthly_savings': round(total_savings, 2),
            'total_annual_savings': round(total_savings * 12, 2),
            'total_monthly_increases': round(total_increases, 2),
            'net_monthly_impact': round(total_savings - total_increases, 2),
            'net_annual_impact': round((total_savings - total_increases) * 12, 2),
            'recommendations_by_type': by_type,
            'recommendations_by_priority': by_priority,
            'automatable_recommendations': automatable,
            'automation_percentage': round(automatable / len(self.recommendations) * 100, 1) if self.recommendations else 0,
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_priority(
        self,
        monthly_savings: float,
        confidence: str
    ) -> RecommendationPriority:
        if monthly_savings > 500 and confidence in ['high', 'medium']:
            return RecommendationPriority.CRITICAL
        elif monthly_savings > 100:
            return RecommendationPriority.HIGH
        elif monthly_savings > 20:
            return RecommendationPriority.MEDIUM
        else:
            return RecommendationPriority.LOW
    
    def _estimate_instance_cost(self, instance: Dict[str, Any]) -> float:
        # simplified cost estimation based on machine type
        machine_type = instance.get('machine_type', '').split('/')[-1]
        
        # basic cost mapping (simplified)
        cost_map = {
            'e2-micro': 5.76,
            'e2-small': 11.52,
            'e2-medium': 23.76,
            'e2-standard-2': 48.24,
            'e2-standard-4': 96.48,
            'n2-standard-2': 69.84,
            'n2-standard-4': 139.68
        }
        
        return cost_map.get(machine_type, 50.0)  # default estimate

    def _estimate_resource_cost(self, resource: Dict[str, Any]) -> float:
        resource_type = resource.get('type', '')
        
        if 'disk' in resource_type.lower():
            # estimate based on disk size (simplified)
            size_gb = resource.get('size_gb', 100)
            return size_gb * 0.04  # ~$0.04 per GB per month
        elif 'ip' in resource_type.lower():
            return 7.0  # static IP ~$7/month
        elif 'snapshot' in resource_type.lower():
            size_gb = resource.get('size_gb', 50)
            return size_gb * 0.026  # snapshot storage cost
        else:
            return 10.0  # default estimate
    
    def clear_recommendations(self) -> None:
        self.recommendations = []
        self.logger.info("Cleared all recommendations")
