# Cloud Cost Optimizer

A comprehensive platform for monitoring and optimizing Google Cloud Platform (GCP) spending through automated resource discovery, cost analysis, and actionable optimization recommendations.

## 🎯 Overview

Cloud Cost Optimizer helps organizations reduce cloud spending by:
- **Collecting billing data** from GCP Cloud Billing API
- **Discovering resources** across your GCP projects using Cloud Asset Inventory
- **Identifying optimization opportunities** such as idle compute instances
- **Generating actionable recommendations** for cost reduction
- **Automating resource management** (coming soon)
- **Providing visual dashboards** for cost trend analysis (coming soon)

## ✨ Features

### Current Capabilities
- ✅ **Secure Authentication**: Service account-based GCP authentication
- ✅ **Billing Data Collection**: Integration with Cloud Billing API
- ✅ **Resource Discovery**: Comprehensive asset inventory using Cloud Asset Inventory API
- ✅ **Idle Resource Detection**: Identify stopped, suspended, or terminated compute instances
- ✅ **Cost Optimization Recommendations**: Automated suggestions for reducing spending
- ✅ **Extensible Architecture**: Abstract base collector pattern for future multi-cloud support

### Planned Features
- 🔄 **Dashboard Interface**: Web-based visualization of cost trends and recommendations
- 🔄 **Automation Scheduler**: Automated shutdown of non-production resources
- 🔄 **Alerting System**: Notifications when spending exceeds configured thresholds
- 🔄 **BigQuery Integration**: Detailed cost analysis from billing export data
- 🔄 **Rightsizing Recommendations**: Identify over-provisioned resources

## 🛠️ Technology Stack

- **Language**: Python 3.8+
- **Cloud Platform**: Google Cloud Platform (GCP)
- **APIs**: Cloud Billing API, Cloud Asset Inventory API, Compute Engine API
- **Authentication**: OAuth2 Service Account credentials
- **Architecture**: Object-oriented design with abstract base classes

## 📋 Prerequisites

1. **Python 3.8 or higher** installed
2. **A GCP account** with an active billing account
3. **A GCP project** with the following APIs enabled:
   - Cloud Billing API
   - Cloud Asset Inventory API
   - Compute Engine API
4. **Appropriate IAM permissions**:
   - `roles/billing.viewer` or `roles/billing.admin`
   - `roles/cloudasset.viewer`
   - `roles/compute.viewer`

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/cloud-cost-optimizer.git
cd cloud-cost-optimizer
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up GCP Service Account

#### Via GCP Console:
1. Navigate to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Provide a name (e.g., `cost-optimizer-sa`)
4. Grant the following roles:
   - Billing Account Viewer
   - Cloud Asset Viewer
   - Compute Viewer
5. Click **Create Key** → Choose **JSON** format
6. Save the JSON file securely (e.g., `~/gcp-credentials/cost-optimizer-key.json`)

#### Via gcloud CLI:
```bash
# Create service account
gcloud iam service-accounts create cost-optimizer-sa \
    --display-name="Cost Optimizer Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:cost-optimizer-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/billing.viewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:cost-optimizer-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudasset.viewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:cost-optimizer-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/compute.viewer"

# Create and download key
gcloud iam service-accounts keys create ~/gcp-credentials/cost-optimizer-key.json \
    --iam-account=cost-optimizer-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## ⚙️ Configuration

Create a configuration file `config/config.yaml`:

```yaml
project_id: "your-gcp-project-id"
billing_account_id: "your-billing-account-id"
service_account_path: "/path/to/your/service-account-key.json"
```

**Security Note**: Never commit your service account JSON file or hardcode credentials. Use environment variables for sensitive data:

```yaml
project_id: "$GCP_PROJECT_ID"
billing_account_id: "$GCP_BILLING_ACCOUNT_ID"
service_account_path: "$GCP_SERVICE_ACCOUNT_PATH"
```

Then set environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_BILLING_ACCOUNT_ID="your-billing-account-id"
export GCP_SERVICE_ACCOUNT_PATH="/path/to/key.json"
```

## 💻 Usage

### Basic Example

```python
from datetime import datetime, timedelta
from src.collectors.gcp_collector import GCPCollector

# Initialize collector with configuration
config = {
    'project_id': 'your-project-id',
    'billing_account_id': 'your-billing-account-id',
    'service_account_path': '/path/to/service-account-key.json'
}

collector = GCPCollector(config)

# Authenticate
if collector.authenticate():
    print("✓ Successfully authenticated with GCP")
    
    # Collect billing data for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    billing_data = collector.collect_billing_data(start_date, end_date)
    print(f"Collected {len(billing_data)} billing records")
    
    # Discover all resources in the project
    resources = collector.collect_resource_data()
    print(f"Found {len(resources)} resources")
    
    # Identify idle compute instances
    idle_instances = collector.get_idle_compute_instances()
    print(f"Found {len(idle_instances)} idle instances")
    
    # Get optimization recommendations
    recommendations = collector.get_cost_optimization_recommendations()
    for rec in recommendations:
        print(f"💡 {rec['recommendation']}")
        print(f"   Resource: {rec['resource_name']}")
        print(f"   Action: {rec['action']}\n")
else:
    print("✗ Authentication failed")
```

### Sample Output

```
✓ Successfully authenticated with GCP
Collected 1 billing records
Found 47 resources
Found 3 idle instances
💡 Instance is stopped - consider deletion if no longer needed
   Resource: dev-test-instance-1
   Action: Review and delete if no longer needed

💡 Instance is suspended - consider deletion if no longer needed
   Resource: staging-db-instance
   Action: Review and delete if no longer needed
```

## 📁 Project Structure

```
cloud-cost-optimizer/
├── src/
│   ├── collectors/           # Data collection modules
│   │   ├── base_collector.py    # Abstract base class
│   │   └── gcp_collector.py     # GCP-specific implementation
│   ├── analyzers/            # Cost analysis algorithms
│   ├── scheduler/            # Resource automation
│   └── alerts/               # Notification systems
├── tests/
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── dashboard/
│   ├── frontend/             # Web UI (React/Vue)
│   └── backend/              # API server
├── config/                   # Configuration files
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── .gitignore
├── README.md
└── requirements.txt
```

## 🔒 Security Best Practices

1. **Never commit credentials**: Service account keys are in `.gitignore`
2. **Use environment variables**: Reference sensitive values with `$VAR_NAME` syntax
3. **Restrict service account permissions**: Grant only necessary IAM roles
4. **Rotate keys regularly**: Create new service account keys periodically
5. **Store keys securely**: Use secret management tools in production

## 🗺️ Roadmap

### Phase 1: Data Collection ✅ (Complete)
- [x] GCP authentication
- [x] Billing data collection
- [x] Resource discovery
- [x] Idle resource detection

### Phase 2: Analysis & Recommendations (In Progress)
- [ ] Cost analysis algorithms
- [ ] Rightsizing recommendations
- [ ] Trend analysis
- [ ] Budget forecasting

### Phase 3: Automation
- [ ] Scheduled resource shutdown
- [ ] Automated snapshot cleanup
- [ ] Policy-based resource management

### Phase 4: Dashboard & Alerts
- [ ] Web-based dashboard
- [ ] Cost trend visualization
- [ ] Threshold-based alerts
- [ ] Email/Slack notifications

### Phase 5: Advanced Features
- [ ] BigQuery billing export integration
- [ ] Machine learning cost predictions
- [ ] Multi-project support
- [ ] Custom optimization policies

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ for cloud cost optimization**
