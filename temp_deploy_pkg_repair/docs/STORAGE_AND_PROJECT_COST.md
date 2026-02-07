# Storage Management and Project Cost System

## Overview
This document describes the storage quota enforcement and project cost (formerly security deposit) system implemented in Synapse.

## Storage Quota Enforcement

### How It Works

1. **Free Storage Allocation**
   - Each subscription plan includes free storage:
     - **Starter Plan**: 10 GB
     - **Growth Plan**: 25 GB
     - **Scale Plan**: 50 GB
     - **PAYG (Default)**: 5 GB

2. **Upload Validation**
   - When users upload files, the system checks:
     - Current organization storage usage
     - Size of new files being uploaded
     - Available free storage from subscription plan
   - If upload would exceed free tier, overage is calculated

3. **Overage Charges**
   - Storage exceeding free tier is charged at:
     - **Starter Plan**: ₹25/GB
     - **Growth Plan**: ₹18/GB
     - **Scale Plan**: ₹13/GB
   - Charges are deducted from organization credits
   - If insufficient credits, upload is rejected with error message

4. **Error Handling**
   ```
   ValidationError: Insufficient credits for storage overage.
   Uploading these files will use 2.50 GB, bringing total to 12.50 GB.
   Your plan includes 10 GB free.
   Overage: 2.50 GB × ₹25/GB = ₹62.50 credits.
   Available credits: 50.00.
   Please purchase more credits or upgrade your plan.
   ```

### Implementation Details

**File**: `synapse/data_import/uploader.py`

- `check_storage_limit(project, new_files_size)` - Validates storage quota before upload
- `create_file_uploads()` - Charges overage after successful upload

**File**: `synapse/billing/storage_service.py`

- `charge_storage_overage()` - Deducts credits and creates transaction record

### Storage Calculation
```python
current_storage_gb = organization.billing.storage_used_gb
new_files_gb = file_size_bytes / (1024^3)
new_total_gb = current_storage_gb + new_files_gb

free_storage_gb = subscription_plan.storage_gb
overage_gb = max(0, new_total_gb - free_storage_gb)

overage_cost = overage_gb × extra_storage_rate_per_gb
```

---

## Project Cost System (formerly Security Deposit)

### Terminology Update
- **Security Deposit** → **Project Cost**
- **Base Fee** → **Security Fee** (variable based on project size)

### Security Fee Tiers

Security fees now vary based on project size:

| Task Count | Security Fee | Project Size |
|-----------|--------------|--------------|
| 0 - 100 | ₹500 | Small |
| 101 - 500 | ₹700 | Medium |
| 501 - 1,000 | ₹900 | Large |
| 1,001 - 2,500 | ₹1,100 | Very Large |
| 2,501 - 5,000 | ₹1,300 | Enterprise |
| 5,000+ | ₹1,500 | Massive |

### Project Cost Calculation

**Formula:**
```
Project Cost = Security Fee + Storage Fee + Annotation Fee

Where:
- Security Fee = Based on project size (500-1500)
- Storage Fee = Estimated Storage (GB) × ₹10/GB
- Annotation Fee = Task Count × Rate × Complexity × Buffer (1.5x)
```

### Example Calculation

**Project Details:**
- 250 tasks
- Bounding box annotation
- 10 labels
- 2 GB estimated storage

**Calculation:**
1. Security Fee: ₹700 (101-500 tasks tier)
2. Storage Fee: 2 GB × ₹10/GB = ₹20
3. Annotation Rate: ₹5 (bounding box)
4. Complexity: 1.5x (6-15 labels)
5. Buffer: 1.5x
6. Annotation Fee: 250 × ₹5 × 1.5 × 1.5 = ₹2,812.50

**Total Project Cost: ₹700 + ₹20 + ₹2,812.50 = ₹3,532.50**

### Implementation Details

**File**: `synapse/billing/models.py`

New fields in `ProjectBilling`:
- `project_cost_required` - Total project cost calculated
- `project_cost_paid` - Amount paid by client
- `project_cost_refunded` - Amount refunded after project completion

New fields in `SecurityDeposit`:
- `security_fee` - Variable fee based on project size

**File**: `synapse/billing/services.py`

- `calculate_security_fee(task_count)` - Determines tier and returns fee
- `calculate_security_deposit()` - Updated to use variable security fees

**File**: `synapse/billing/cost_estimation.py`

- `calculate_security_fee()` - Static method for cost estimation
- `SECURITY_FEE_TIERS` - Tier definitions

### Backward Compatibility

Old fields are retained for backward compatibility:
- `security_deposit_required` → Use `project_cost_required`
- `security_deposit_paid` → Use `project_cost_paid`
- `security_deposit_refunded` → Use `project_cost_refunded`
- `base_fee` → Use `security_fee`

Migration `0010_rename_security_deposit_to_project_cost.py` copies existing data to new fields.

---

## Database Migration

Run the migration to apply changes:

```bash
python manage.py migrate billing
```

This will:
1. Add new `project_cost_*` fields to `ProjectBilling`
2. Add `security_fee` field to `SecurityDeposit`
3. Mark old fields as deprecated
4. Copy existing data to new fields

---

## API Changes

### Storage Upload Response

When storage overage occurs, the API deducts credits automatically and includes details in logs:

```python
logger.info(
    f"Charged storage overage: 2.50 GB = ₹62.50"
)
```

### Project Cost Calculation

Cost estimation endpoint now returns:

```json
{
  "success": true,
  "base_fee": 700.00,
  "storage_fee": 20.00,
  "annotation_fee": 2812.50,
  "total_deposit": 3532.50,
  "breakdown": {
    "security_fee": 700.00,
    "estimated_tasks": 250,
    "annotation_rate": 5.00,
    "complexity_multiplier": 1.5,
    "task_count_tier": "101-500 tasks"
  }
}
```

---

## Testing

### Test Storage Overage

1. Create organization with Starter plan (10 GB free)
2. Upload 8 GB of files (within limit) ✓
3. Upload 5 GB more files (total 13 GB, overage 3 GB)
4. Verify:
   - Overage charge: 3 × ₹25 = ₹75
   - Credits deducted: ₹75
   - Transaction created: "Storage overage charge: 3.00 GB"

### Test Security Fee Tiers

1. Create project with 50 tasks → Security fee: ₹500
2. Create project with 200 tasks → Security fee: ₹700
3. Create project with 750 tasks → Security fee: ₹900
4. Create project with 1,500 tasks → Security fee: ₹1,100
5. Create project with 3,000 tasks → Security fee: ₹1,300
6. Create project with 6,000 tasks → Security fee: ₹1,500

---

## Configuration

### Storage Rates

Update in subscription plan:
- `storage_gb` - Free storage allocation
- `extra_storage_rate_per_gb` - Overage rate per GB

### Security Fee Tiers

Update in `billing/cost_estimation.py`:

```python
SECURITY_FEE_TIERS = [
    (100, Decimal("500")),    # 0-100 tasks
    (500, Decimal("700")),    # 101-500 tasks
    (1000, Decimal("900")),   # 501-1000 tasks
    (2500, Decimal("1100")),  # 1001-2500 tasks
    (5000, Decimal("1300")),  # 2501-5000 tasks
    (float('inf'), Decimal("1500")),  # 5000+ tasks
]
```

---

## Monitoring

### Storage Usage

Track organization storage:
```python
from billing.storage_service import StorageCalculationService

storage_info = StorageCalculationService.calculate_organization_storage(org)
# Returns: total_bytes, total_gb, formatted, project_breakdown
```

### Overage Charges

Query storage overage transactions:
```python
from billing.models import CreditTransaction

overages = CreditTransaction.objects.filter(
    organization=org,
    transaction_type='storage_overage'
)
```

---

## Future Enhancements

1. **Storage Alerts**: Notify clients when approaching storage limit
2. **Storage Analytics**: Dashboard showing storage trends
3. **Automatic Upgrades**: Suggest plan upgrades for frequent overages
4. **Bulk Upload Optimization**: Compress files before upload
5. **Storage Cleanup**: Delete unused files to free space
