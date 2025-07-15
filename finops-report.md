# FinOps Report: House Gallery GCP Infrastructure

**Generated**: July 13, 2025  
**Project**: housegallery (591747915969)  
**Billing Account**: 01D7ED-72DC17-5CC38D  
**Primary Region**: us-west2  

---

## Executive Summary

This House Gallery project operates a Django/Wagtail CMS on Google Cloud Platform with a lean, well-architected infrastructure. The current setup includes a single Cloud Run service, PostgreSQL database, and supporting build/storage infrastructure optimized for a gallery website.

### Quick Stats
- **Active Services**: 1 Cloud Run service (dev environment)
- **Database**: 1 Cloud SQL PostgreSQL instance (db-g1-small)
- **Storage**: 2 buckets (~807MB total)
- **Container Images**: ~7.5GB in Artifact Registry
- **Build Infrastructure**: 3 automated triggers

---

## Current Resource Inventory

### Compute Services

#### Cloud Run Services
| Service | Region | CPU | Memory | Concurrency | Max Instances | Status |
|---------|--------|-----|--------|-------------|---------------|--------|
| `housegallery-dev-jrl-service` | us-west2 | 1000m | 2048Mi | 80 | 100 | Active |

**Configuration Details:**
- **Image**: `us-west2-docker.pkg.dev/housegallery/housegallery/housegallery-dev-jrl-service:latest`
- **Service Account**: `housegallerybutler@housegallery.iam.gserviceaccount.com`
- **Timeout**: 300s
- **SQL Connection**: Direct connection to Cloud SQL instance
- **Last Deployed**: 2025-07-13T16:34:12Z

### Database Services

#### Cloud SQL Instances
| Instance | Version | Tier | Location | Storage | Status |
|----------|---------|------|----------|---------|--------|
| `housegallery` | PostgreSQL 13 | db-g1-small | us-west2-c | 10GB SSD | RUNNABLE |

**Configuration Details:**
- **IP Address**: 35.236.20.127 (Public)
- **Backup**: Enabled (7-day retention, daily at 07:00 UTC)
- **Auto-resize**: Enabled
- **Deletion Protection**: Enabled ✅
- **IAM Authentication**: Enabled ✅
- **SSL**: Optional (ALLOW_UNENCRYPTED_AND_ENCRYPTED)

### Storage Services

#### Cloud Storage Buckets
| Bucket | Location | Size | Storage Class | Public Access |
|--------|----------|------|---------------|---------------|
| `housegallery-dev-jrl` | US (Multi-region) | 787.9 MiB | STANDARD | Blocked ✅ |
| `housegallery-cloudbuild-log` | US-WEST1 (Regional) | 18.79 MiB | STANDARD | Blocked ✅ |

**Security Configuration:**
- Both buckets have public access prevention enforced ✅
- Uniform bucket-level access enabled ✅
- Soft delete policy: 7-day retention

#### Artifact Registry
| Repository | Format | Location | Size | Encryption |
|------------|--------|----------|------|------------|
| `housegallery` | Docker | us-west2 | 7.47 GB | Google-managed ✅ |
| `cloud-run-source-deploy` | Docker | us-west2 | <1 MB | Google-managed ✅ |

### CI/CD Infrastructure

#### Cloud Build Triggers
| Trigger | Type | Branch Pattern | Status | Purpose |
|---------|------|----------------|--------|---------|
| `housegallery-dev-jrl` | Automatic | `^jrl/*` | Active | Development builds |
| `housegallery-prod` | Automatic | `^main$` | Active | Production build + backup |
| `housegallery-prod-deploy-manual` | Manual | `main` | Active | Production deployment |

**Recent Build Performance:**
- Average build time: ~5-7 minutes
- Success rate: 83% (5/6 recent builds successful)
- Service account: `housegallerybutler@housegallery.iam.gserviceaccount.com`

---

## Cost Analysis

### Estimated Monthly Costs

#### Compute Costs
- **Cloud Run**: ~$10-30/month (depending on traffic)
  - Allocated: 1 CPU, 2GB RAM
  - Pay-per-use model benefits low-traffic scenarios
  - 80 concurrent requests supported

#### Database Costs
- **Cloud SQL (db-g1-small)**: ~$25-35/month
  - Includes: 1.7GB RAM, 1 vCPU, 10GB SSD storage
  - Backup storage: ~$1-2/month additional
  - Zonal deployment (no high availability premium)

#### Storage Costs
- **Cloud Storage**: ~$2-5/month
  - Multi-region storage: ~$15/TB/month (787MB = ~$0.75)
  - Regional storage: ~$10/TB/month (19MB = negligible)
  - No egress costs for same-region access

#### Build & Registry Costs
- **Artifact Registry**: ~$5-10/month
  - 7.47GB storage at ~$0.10/GB/month
  - No additional transfer costs for same-region pulls
- **Cloud Build**: ~$2-10/month
  - Based on build minutes (5-7 min/build)
  - Free tier: 120 build-minutes/day

**Estimated Total**: $44-90/month

### Cost Optimization Opportunities

#### High Impact (Potential 20-40% savings)

1. **Cloud SQL Right-sizing Analysis**
   - **Current**: db-g1-small (1.7GB RAM, 1 vCPU)
   - **Recommendation**: Monitor CPU/memory utilization
   - **Potential Action**: Consider db-f1-micro for development (~40% cost reduction)
   - **Savings**: ~$10-15/month

2. **Storage Location Optimization**
   - **Current**: `housegallery-dev-jrl` using multi-region US storage
   - **Recommendation**: Move to regional us-west2 storage for dev environment
   - **Savings**: ~33% storage cost reduction (~$0.25/month for current usage)

3. **Artifact Registry Cleanup**
   - **Current**: 7.47GB of container images
   - **Recommendation**: Implement automated cleanup of old images
   - **Potential Action**: Retain only last 10 versions per image
   - **Savings**: 50-70% reduction possible (~$2-5/month)

#### Medium Impact (Potential 10-20% savings)

4. **Cloud Build Optimization**
   - **Current**: 5-7 minute builds
   - **Recommendation**: Optimize Docker builds with multi-stage builds and caching
   - **Benefit**: Faster builds = lower costs and better developer experience

5. **Cloud Run Auto-scaling Review**
   - **Current**: Max 100 instances
   - **Recommendation**: Review if 100 max instances needed for dev environment
   - **Benefit**: Prevent unexpected scaling costs

#### Low Impact (Operational Excellence)

6. **Build Log Retention**
   - **Current**: Cloud Build logs in dedicated bucket
   - **Recommendation**: Implement lifecycle policy for log cleanup
   - **Benefit**: Prevent long-term log accumulation

---

## Security & Governance Assessment

### ✅ Security Strengths

1. **Storage Security**
   - Public access prevention enforced on all buckets
   - Uniform bucket-level access enabled
   - Google-managed encryption keys

2. **Database Security**
   - Deletion protection enabled
   - IAM authentication enabled
   - Backup retention configured

3. **Service Identity**
   - Dedicated service account (`housegallerybutler@housegallery.iam.gserviceaccount.com`)
   - Proper IAM configuration for Cloud Run → Cloud SQL connectivity

### ⚠️ Security Recommendations

1. **Database SSL Enforcement**
   - **Current**: SSL optional (ALLOW_UNENCRYPTED_AND_ENCRYPTED)
   - **Recommendation**: Enforce SSL connections (ENCRYPTED_ONLY)
   - **Benefit**: Data in transit protection

2. **Private IP for Cloud SQL**
   - **Current**: Public IP enabled (35.236.20.127)
   - **Recommendation**: Consider private IP for production
   - **Benefit**: Network-level isolation

3. **Backup Verification**
   - **Recommendation**: Implement regular backup restore testing
   - **Benefit**: Ensure disaster recovery capabilities

---

## Performance & Reliability

### Current Configuration Assessment

#### Cloud Run Performance
- **CPU**: 1000m (adequate for Django/Wagtail)
- **Memory**: 2048Mi (good for Django with media processing)
- **Concurrency**: 80 (well-balanced for I/O bound workloads)
- **Startup Probe**: TCP probe configured ✅

#### Database Performance
- **Tier**: db-g1-small suitable for development/small production
- **Storage**: 10GB SSD with auto-resize ✅
- **Maintenance Window**: Configured for Sunday 8AM UTC ✅

### Reliability Features
- **Cloud SQL**: Automated backups with 7-day retention
- **Storage**: Multi-region redundancy for main bucket
- **Build**: Multiple deployment strategies (auto + manual)

---

## Future Planning & Scalability

### Growth Scenarios

#### Scenario 1: Light Production Load (100-500 monthly users)
- **Current setup adequate**
- **Estimated cost**: $60-120/month
- **Recommendations**: 
  - Monitor Cloud SQL performance
  - Consider moving to regional storage

#### Scenario 2: Medium Production Load (1K-5K monthly users)
- **Cloud SQL**: Upgrade to db-custom-1-3840 (~$50/month)
- **Cloud Run**: Current config should handle load
- **Storage**: May need CDN for media files
- **Estimated cost**: $100-200/month

#### Scenario 3: High Production Load (10K+ monthly users)
- **Cloud SQL**: Consider high availability setup
- **Cloud Run**: May need multiple regions
- **Storage**: Implement CDN (Cloud CDN)
- **Monitoring**: Add comprehensive monitoring/alerting
- **Estimated cost**: $300-600/month

### Budget Planning Recommendations

1. **Set up Billing Alerts**
   - $50, $100, $200 monthly thresholds
   - Email notifications to project stakeholders

2. **Regular Cost Reviews**
   - Monthly cost analysis
   - Quarterly resource optimization review

3. **Resource Monitoring**
   - Enable detailed monitoring for Cloud SQL
   - Set up Cloud Run request/latency monitoring

---

## Immediate Action Items

### Priority 1 (This Week)
1. **Set up billing alerts** for $50 and $100 monthly spend
2. **Review Cloud SQL utilization** to determine if db-g1-small is right-sized
3. **Implement Artifact Registry cleanup policy** to prevent unbounded growth

### Priority 2 (This Month)
1. **Enforce SSL** for Cloud SQL connections
2. **Optimize Docker builds** to reduce build time and costs
3. **Evaluate storage location** for development bucket

### Priority 3 (Next Quarter)
1. **Plan production environment** deployment strategy
2. **Implement comprehensive monitoring** and alerting
3. **Consider private networking** for production database

---

## Cost Monitoring Setup

### Recommended Billing Alerts
```bash
# Set up billing alerts (example commands)
gcloud alpha billing budgets create \
  --billing-account=01D7ED-72DC17-5CC38D \
  --display-name="House Gallery Monthly Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=50,basis=CURRENT_SPEND \
  --threshold-rule=percent=90,basis=CURRENT_SPEND \
  --threshold-rule=percent=100,basis=CURRENT_SPEND
```

### Key Metrics to Monitor
- **Cloud Run**: Request count, latency, memory utilization
- **Cloud SQL**: CPU utilization, memory usage, connection count
- **Storage**: Bucket size growth, request patterns
- **Build**: Build frequency, duration, success rate

---

## Conclusion

The House Gallery infrastructure is well-designed with appropriate security measures and cost-conscious resource allocation. The current setup efficiently serves a development environment while providing a clear path to production scaling.

**Total Optimization Potential**: 20-40% cost reduction (~$15-35/month savings) through right-sizing and cleanup activities, while maintaining security and performance standards.

**Next Steps**: Focus on the Priority 1 action items to establish proper cost monitoring and optimize the most impactful resources (Cloud SQL sizing and Artifact Registry cleanup).