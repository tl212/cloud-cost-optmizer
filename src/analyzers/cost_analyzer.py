"""Cost analysis and trend detection."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CostAnalyzer:
    """Analyzes cloud costs and generates insights."""
    
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
    
    def analyze_cost_trends(
        self, 
        billing_data: List[Dict[str, Any]], 
        group_by: str = 'service'
    ) -> Dict[str, Any]:
        """
        Analyze cost trends from billing data.
        
        args:
            billing_data: List of billing records
            group_by: How to group the data (service, project, resource)
        
        returns:
            Dictionary with trend analysis
        """
        if not billing_data:
            return {
                'status': 'no_data',
                'message': 'No billing data available for analysis'
            }
        
        try:
            # Group costs by the specified dimension
            grouped_costs = defaultdict(float)
            total_cost = 0.0
            
            for record in billing_data:
                key = record.get(f'{group_by}_name', 'Unknown')
                cost = float(record.get('cost', 0))
                grouped_costs[key] += cost
                total_cost += cost
            
            # Calculate percentages
            cost_breakdown = []
            for service, cost in sorted(
                grouped_costs.items(), 
                key=lambda x: x[1], 
                reverse=True
            ):
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                cost_breakdown.append({
                    'name': service,
                    'cost': round(cost, 2),
                    'percentage': round(percentage, 2)
                })
            
            return {
                'status': 'success',
                'total_cost': round(total_cost, 2),
                'breakdown': cost_breakdown,
                'top_cost_driver': cost_breakdown[0]['name'] if cost_breakdown else None,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cost trends: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def compare_periods(
        self,
        current_data: List[Dict[str, Any]],
        previous_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare costs between two time periods.
        
        args:
            current_data: Billing data for current period
            previous_data: Billing data for previous period
        
        returns:
            comparison analysis
        """
        try:
            current_total = sum(float(r.get('cost', 0)) for r in current_data)
            previous_total = sum(float(r.get('cost', 0)) for r in previous_data)
            
            if previous_total == 0:
                percentage_change = 100.0 if current_total > 0 else 0.0
            else:
                percentage_change = ((current_total - previous_total) / previous_total) * 100
            
            return {
                'current_period_cost': round(current_total, 2),
                'previous_period_cost': round(previous_total, 2),
                'absolute_change': round(current_total - previous_total, 2),
                'percentage_change': round(percentage_change, 2),
                'trend': 'increasing' if current_total > previous_total else 'decreasing',
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing periods: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def identify_anomalies(
        self,
        billing_data: List[Dict[str, Any]],
        threshold_percentage: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Identify cost anomalies or spikes.
        
        args:
            billing_data: List of billing records with timestamps
            threshold_percentage: Percentage threshold for anomaly detection
        
        returns:
            list of detected anomalies
        """
        anomalies = []
        
        try:
            # Group by date
            daily_costs = defaultdict(float)
            for record in billing_data:
                date_str = record.get('date', record.get('collection_date', 'Unknown'))
                if date_str != 'Unknown':
                    # Extract just the date part
                    date = date_str.split('T')[0]
                    cost = float(record.get('cost', 0))
                    daily_costs[date] += cost
            
            if len(daily_costs) < 2:
                return anomalies
            
            # Calculate average cost
            costs = list(daily_costs.values())
            avg_cost = sum(costs) / len(costs)
            
            # Identify anomalies
            for date, cost in daily_costs.items():
                deviation = ((cost - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
                
                if abs(deviation) > threshold_percentage:
                    anomalies.append({
                        'date': date,
                        'cost': round(cost, 2),
                        'average_cost': round(avg_cost, 2),
                        'deviation_percentage': round(deviation, 2),
                        'severity': 'high' if abs(deviation) > 50 else 'medium'
                    })
            
            self.logger.info(f"Identified {len(anomalies)} cost anomalies")
            
        except Exception as e:
            self.logger.error(f"Error identifying anomalies: {str(e)}")
        
        return anomalies
    
    def generate_budget_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate simple budget forecast based on historical trends.
        
        args:
            historical_data: Historical billing records
            forecast_days: Number of days to forecast
        
        returns:
            forecast information
        """
        try:
            if not historical_data:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need historical data for forecasting'
                }
            
            # Calculate daily average
            total_cost = sum(float(r.get('cost', 0)) for r in historical_data)
            days_in_data = len(set(
                r.get('date', r.get('collection_date', '')).split('T')[0] 
                for r in historical_data
            ))
            
            if days_in_data == 0:
                days_in_data = 1
            
            daily_avg = total_cost / days_in_data
            forecasted_cost = daily_avg * forecast_days
            
            return {
                'status': 'success',
                'historical_daily_average': round(daily_avg, 2),
                'forecast_period_days': forecast_days,
                'forecasted_total': round(forecasted_cost, 2),
                'confidence': 'low',  # Simple average has low confidence
                'method': 'simple_moving_average',
                'generated_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating forecast: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def calculate_resource_efficiency(
        self,
        resources: List[Dict[str, Any]],
        idle_resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate resource efficiency metrics.
        
        args:
            resources: All resources
            idle_resources: Idle or underutilized resources
        
        returns:
            efficiency metrics
        """
        try:
            total_resources = len(resources)
            idle_count = len(idle_resources)
            
            if total_resources == 0:
                utilization_rate = 0
            else:
                utilization_rate = ((total_resources - idle_count) / total_resources) * 100
            
            return {
                'total_resources': total_resources,
                'active_resources': total_resources - idle_count,
                'idle_resources': idle_count,
                'utilization_rate': round(utilization_rate, 2),
                'efficiency_grade': self._get_efficiency_grade(utilization_rate),
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating efficiency: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_efficiency_grade(self, utilization_rate: float) -> str:
        """
        get efficiency grade based on utilization rate.
        
        args:
            utilization_rate: Percentage of resources actively used
        
        returns:
            grade (A-F)
        """
        if utilization_rate >= 90:
            return 'A'
        elif utilization_rate >= 80:
            return 'B'
        elif utilization_rate >= 70:
            return 'C'
        elif utilization_rate >= 60:
            return 'D'
        else:
            return 'F'