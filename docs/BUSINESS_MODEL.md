# Synapse Business Model

> Last Updated: February 7, 2026

## Executive Summary

Synapse operates a **credits-based marketplace model** that connects enterprise clients needing data annotation with a trained workforce of annotators. The platform generates revenue through credit sales and subscriptions, while paying annotators a revenue share for completed work.

---

## Table of Contents

1. [Business Model Overview](#business-model-overview)
2. [Client Billing System](#client-billing-system)
3. [Credits System](#credits-system)
4. [Annotator Earnings](#annotator-earnings)
5. [Payment Flows](#payment-flows)
6. [Quality Assurance Economics](#quality-assurance-economics)
7. [Pricing Structure](#pricing-structure)
8. [Revenue Model](#revenue-model)

---

## Business Model Overview

### Three-Sided Marketplace

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SYNAPSE MARKETPLACE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐       │
│   │   CLIENTS    │         │   SYNAPSE    │         │  ANNOTATORS  │       │
│   │  (Enterprises)│         │  (Platform)  │         │  (Workforce) │       │
│   ├──────────────┤         ├──────────────┤         ├──────────────┤       │
│   │              │  ₹₹₹    │              │   ₹₹    │              │       │
│   │ Buy Credits ─┼────────▶│ Takes 50-60% │────────▶│ Earn 40-50%  │       │
│   │              │         │              │         │              │       │
│   │ Get Quality  │◀────────│ Quality      │◀────────│ Complete     │       │
│   │ Annotations  │  Data   │ Assurance    │  Work   │ Tasks        │       │
│   │              │         │              │         │              │       │
│   └──────────────┘         └──────────────┘         └──────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Value Proposition

| Stakeholder | Value Received |
|-------------|----------------|
| **Clients** | High-quality labeled data, no hiring/training costs, scalable workforce |
| **Annotators** | Flexible work, fair pay, skill development, gamified rewards |
| **Platform** | Revenue from margin, data on annotation patterns, ML model training data |

---

## Client Billing System

### Billing Types

Clients can choose between two billing models:

#### 1. Pay-As-You-Go (PAYG)

```python
class OrganizationBilling:
    billing_type = "payg"  # Pay As You Go
    
    # Credits purchased directly
    available_credits = Decimal('5000')
    
    # No subscription, no recurring charges
    active_subscription = None
```

**Characteristics:**
- No commitment
- Higher per-credit cost
- Credits never expire
- Good for occasional projects

#### 2. Subscription

```python
class Subscription:
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('paused', 'Paused'),
    ]
    
    plan = ForeignKey(SubscriptionPlan)
    start_date = DateTimeField()
    end_date = DateTimeField()
    next_billing_date = DateTimeField()
    auto_renew = BooleanField(default=True)
```

**Characteristics:**
- Monthly or annual billing
- Lower effective rate per credit
- Credits allocated monthly
- Credit rollover (1 month max)

### Subscription Plans

| Plan | Monthly Price | Credits/Month | Effective Rate | Storage | Users |
|------|---------------|---------------|----------------|---------|-------|
| **Starter** | ₹2,999 | 2,000 | ₹1.50/credit | 5 GB | 2 |
| **Growth** | ₹7,499 | 6,000 | ₹1.25/credit | 25 GB | 5 |
| **Scale** | ₹14,999 | 15,000 | ₹1.00/credit | 100 GB | 10 |
| **Enterprise** | Custom | Unlimited | Custom | Unlimited | Unlimited |

**Annual Discount:** 2 months free (17% savings)

### Credit Packages (PAYG)

| Package | Credits | Price (INR) | Rate/Credit |
|---------|---------|-------------|-------------|
| Starter | 500 | ₹999 | ₹2.00 |
| Standard | 2,000 | ₹3,499 | ₹1.75 |
| Professional | 5,000 | ₹7,999 | ₹1.60 |
| Enterprise | 15,000 | ₹21,999 | ₹1.47 |

---

## Credits System

### How Credits Work

Credits are the universal currency in Synapse:

```python
# 1 Credit ≈ ₹1 (approximately)

# Example: Client has 1000 credits
# - Simple classification: 2 credits/task → 500 tasks
# - Bounding box: 5 credits/task → 200 tasks  
# - Segmentation: 15 credits/task → ~66 tasks
```

### Credit Consumption

Credits are consumed based on:

1. **Data Type** - Image, video, audio, text
2. **Annotation Type** - Classification, segmentation, etc.
3. **Modality** - General, medical (X-ray, CT), specialized
4. **Complexity** - Number of labels, nested structures

### Annotation Pricing Table

```python
class AnnotationPricing:
    DATA_TYPE_CHOICES = [
        ('2d_image', '2D Image'),
        ('3d_volume', '3D Volume'),
        ('time_series', 'Time Series'),
        ('video', 'Video'),
        ('signal_data', 'Signal Data'),
        ('document', 'Document'),
    ]
    
    # Example pricing for medical imaging
    data_type = '2d_image'
    modality = 'X-ray (Chest)'
    base_credit = Decimal('3.0')  # Per image
    
    # Additional costs by annotation type
    classification_credit = Decimal('2.0')
    bounding_box_credit = Decimal('5.0')
    segmentation_credit = Decimal('12.0')
    keypoint_credit = Decimal('8.0')
```

**Sample Pricing Matrix (Credits):**

| Data Type | Modality | Base | Classification | Bounding Box | Segmentation |
|-----------|----------|------|----------------|--------------|--------------|
| 2D Image | General | 1.0 | +1.0 | +3.0 | +10.0 |
| 2D Image | X-ray | 3.0 | +2.0 | +5.0 | +12.0 |
| 2D Image | CT Scan | 5.0 | +3.0 | +7.0 | +15.0 |
| Video | General | 8.0/min | +3.0 | +10.0 | +25.0 |
| Audio | Transcription | 5.0/min | +2.0 | N/A | N/A |
| Text | NER | 0.5 | +1.0 | N/A | N/A |

### Complexity Multipliers

```python
class ProjectBillingService:
    # Multipliers based on label count
    LABEL_COUNT_MULTIPLIERS = {
        (1, 5): Decimal('1.0'),      # 1-5 labels: standard
        (6, 15): Decimal('1.2'),     # 6-15 labels: +20%
        (16, 30): Decimal('1.5'),    # 16-30 labels: +50%
        (31, 100): Decimal('2.0'),   # 31-100 labels: +100%
        (101, float('inf')): Decimal('2.5'),  # 100+: +150%
    }
```

### Security Deposits

Before starting a project, clients pay a security deposit:

```python
class ProjectBillingService:
    BASE_DEPOSIT_FEE = Decimal('500')        # Minimum ₹500
    STORAGE_RATE_PER_GB = Decimal('10')      # ₹10/GB
    ANNOTATION_BUFFER = Decimal('1.5')       # 1.5x buffer
    
    @classmethod
    def calculate_security_deposit(cls, project, estimated_tasks, storage_gb):
        """
        Deposit = Base Fee + Storage Fee + (Annotation Cost × Buffer)
        """
        base_fee = cls.BASE_DEPOSIT_FEE
        storage_fee = storage_gb * cls.STORAGE_RATE_PER_GB
        
        # Calculate annotation cost based on label config
        annotation_rate = cls._calculate_annotation_rate(project.label_config)
        annotation_fee = estimated_tasks * annotation_rate * cls.ANNOTATION_BUFFER
        
        return base_fee + storage_fee + annotation_fee
```

**Example Deposit Calculation:**

```
Project: Medical Image Classification
- Estimated tasks: 1,000 images
- Storage: 10 GB
- Annotation type: Classification with 8 labels

Calculation:
- Base fee: ₹500
- Storage fee: 10 GB × ₹10 = ₹100
- Annotation: 1,000 × 5 credits × 1.2 (complexity) × 1.5 (buffer) = ₹9,000

Total Deposit: ₹9,600
```

### Credit Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CREDIT LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. PURCHASE              2. ALLOCATION           3. CONSUMPTION            │
│  ┌─────────────┐          ┌─────────────┐         ┌─────────────┐          │
│  │ Client buys │─────────▶│ Credits in  │────────▶│ Deducted on │          │
│  │ credits/sub │          │ org wallet  │         │ annotation  │          │
│  └─────────────┘          └─────────────┘         └──────┬──────┘          │
│                                                          │                  │
│  ┌────────────────────────────────────────────────────────┤                  │
│  │                                                        │                  │
│  │  4. DISTRIBUTION                    5. SETTLEMENT      ▼                  │
│  │  ┌─────────────┐                    ┌─────────────┐   ┌─────────────┐   │
│  │  │ 50-60% to   │◀───────────────────│ Credits to  │◀──│ Annotation  │   │
│  │  │ platform    │                    │ annotator   │   │ completed   │   │
│  │  └─────────────┘                    └─────────────┘   └─────────────┘   │
│  │                                           │                              │
│  │                                           ▼                              │
│  │                                     ┌─────────────┐                      │
│  │                                     │ Paid to     │                      │
│  │                                     │ annotator   │                      │
│  │                                     │ bank/UPI    │                      │
│  │                                     └─────────────┘                      │
│  │                                                                          │
│  └──────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Annotator Earnings

### Revenue Share Model

Annotators receive 40-50% of the credits charged to clients:

```python
class AnnotatorEarnings:
    # Default 45% revenue share
    revenue_share_percentage = Decimal('45.00')
    
    # Example: 5 credit task
    # Client pays: 5 credits (₹5)
    # Annotator receives: 5 × 0.45 = 2.25 credits (₹2.25)
    # Platform keeps: 5 × 0.55 = 2.75 credits (₹2.75)
```

### Payment Structure

Annotator payment has multiple components:

```python
class PaymentService:
    # Base rates per annotation type (INR)
    BASE_RATES = {
        'classification': Decimal('2.0'),
        'bounding_box': Decimal('5.0'),
        'polygon': Decimal('8.0'),
        'segmentation': Decimal('15.0'),
        'keypoint': Decimal('10.0'),
        'ner': Decimal('3.0'),
    }
```

### Payment Multipliers

#### 1. Trust Level Multiplier

```python
class TrustLevel:
    LEVEL_MULTIPLIERS = {
        'new': Decimal('0.8'),      # 80% of base (probation)
        'junior': Decimal('1.0'),   # 100% of base
        'regular': Decimal('1.1'),  # 110% of base
        'senior': Decimal('1.3'),   # 130% of base
        'expert': Decimal('1.5'),   # 150% of base
    }
    
    # Promotion requirements
    LEVEL_THRESHOLDS = {
        'junior': {'tasks': 50, 'accuracy': 70, 'honeypot_rate': 80},
        'regular': {'tasks': 200, 'accuracy': 80, 'honeypot_rate': 90},
        'senior': {'tasks': 500, 'accuracy': 90, 'honeypot_rate': 95},
        'expert': {'tasks': 1000, 'accuracy': 95, 'honeypot_rate': 98},
    }
```

#### 2. Quality Multiplier

```python
# Quality score (0-100) affects payment
quality_multiplier = quality_score / 100

# Example:
# - Quality score: 85%
# - Quality multiplier: 0.85
```

#### 3. Streak Multiplier

```python
class AnnotatorStreak:
    def get_streak_multiplier(self):
        if self.current_streak >= 30:
            return Decimal('1.25')  # +25% for 30+ day streak
        elif self.current_streak >= 14:
            return Decimal('1.15')  # +15% for 14+ day streak
        elif self.current_streak >= 7:
            return Decimal('1.10')  # +10% for 7+ day streak
        elif self.current_streak >= 3:
            return Decimal('1.05')  # +5% for 3+ day streak
        return Decimal('1.0')
```

### Payment Calculation Example

```
Task: Bounding Box on Medical Image
Base Rate: ₹5.00

Annotator Profile:
- Trust Level: Senior (1.3x)
- Quality Score: 90% (0.9x)
- Streak: 10 days (1.1x)

Final Payment = ₹5.00 × 1.3 × 0.9 × 1.1 = ₹6.44
```

### Escrow Payment System

Payments are released in three stages to ensure quality:

```python
class TaskAssignment:
    # Payment split
    immediate_payment = base_payment * Decimal('0.4')   # 40%
    consensus_payment = base_payment * Decimal('0.4')   # 40%
    review_payment = base_payment * Decimal('0.2')      # 20%
    
    # Release flags
    immediate_released = BooleanField(default=False)
    consensus_released = BooleanField(default=False)
    review_released = BooleanField(default=False)
```

**Payment Release Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ESCROW PAYMENT RELEASE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGE 1: IMMEDIATE (40%)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Triggered: When annotator submits annotation                         │   │
│  │ Amount: 40% of base payment                                          │   │
│  │ Status: Goes to "pending_approval"                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  STAGE 2: CONSENSUS (40%)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Triggered: When consensus is reached (3+ annotators agree)          │   │
│  │ Amount: 40% of base payment                                          │   │
│  │ Status: Moves to "available_balance"                                 │   │
│  │ Note: Stage 1 also moves from pending to available                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  STAGE 3: EXPERT REVIEW (20%)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Triggered: After expert review (for flagged/disputed tasks)         │   │
│  │ Amount: 20% of base payment                                          │   │
│  │ Status: Added to "available_balance"                                 │   │
│  │ Note: May include accuracy bonus/penalty                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Accuracy-Based Bonuses/Penalties

```python
# Ground truth accuracy affects final payment
ACCURACY_MULTIPLIERS = {
    'excellent': Decimal('1.25'),  # 95%+ accuracy: +25% bonus
    'good': Decimal('1.10'),       # 90-94%: +10% bonus
    'acceptable': Decimal('1.0'),  # 80-89%: standard
    'poor': Decimal('0.8'),        # 70-79%: -20% penalty
    'very_poor': Decimal('0.5'),   # <70%: -50% penalty
}
```

### Payout Process

```python
class PayoutRequest:
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYOUT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
    ]
    
    annotator = ForeignKey(AnnotatorProfile)
    amount = DecimalField()  # Amount to withdraw
    payout_method = CharField(choices=PAYOUT_METHOD_CHOICES)
    
    # Bank details snapshot (frozen at request time)
    bank_details = JSONField()
```

**Payout Rules:**
- Minimum payout: ₹100
- Processing time: 3-5 business days
- Methods: Bank transfer (NEFT/IMPS) or UPI
- Fees: Platform absorbs transaction fees

---

## Payment Flows

### Flow 1: Client → Platform (Credit Purchase)

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐
│  Client  │───▶│ Razorpay  │───▶│ Platform │───▶│ Org Wallet │
│          │    │ Gateway   │    │ Backend  │    │ (Credits)  │
└──────────┘    └───────────┘    └──────────┘    └────────────┘
     │                │                │                │
     │  1. Select     │                │                │
     │  credit pkg    │                │                │
     │────────────────│                │                │
     │                │                │                │
     │  2. Redirect   │                │                │
     │  to Razorpay   │                │                │
     │────────────────▶│                │                │
     │                │                │                │
     │  3. Payment    │                │                │
     │  (Card/UPI)    │                │                │
     │────────────────▶│                │                │
     │                │                │                │
     │                │  4. Webhook    │                │
     │                │  payment.captured               │
     │                │────────────────▶│                │
     │                │                │                │
     │                │                │  5. Add        │
     │                │                │  credits       │
     │                │                │────────────────▶│
     │                │                │                │
     │  6. Confirmation               │                │
     │◀────────────────────────────────│                │
```

### Flow 2: Platform → Annotator (Task Payment)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Annotation   │───▶│   Payment    │───▶│  Annotator   │
│ Submitted    │    │   Service    │    │   Wallet     │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       │ 1. Task completed │                   │
       │──────────────────▶│                   │
       │                   │                   │
       │                   │ 2. Calculate      │
       │                   │ payment           │
       │                   │ (base × quality   │
       │                   │  × trust)         │
       │                   │                   │
       │                   │ 3. Release        │
       │                   │ immediate (40%)   │
       │                   │──────────────────▶│
       │                   │                   │ pending_approval += amount
       │                   │                   │
       │                   │                   │
   [Later: Consensus]      │                   │
       │                   │                   │
       │                   │ 4. Release        │
       │                   │ consensus (40%)   │
       │                   │──────────────────▶│
       │                   │                   │ available_balance += amount
       │                   │                   │
   [Later: Expert Review]  │                   │
       │                   │                   │
       │                   │ 5. Release        │
       │                   │ review (20%)      │
       │                   │──────────────────▶│
       │                   │                   │ available_balance += amount
```

### Flow 3: Annotator → Bank (Payout)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│  Annotator   │───▶│   Platform   │───▶│  RazorpayX   │───▶│   Bank   │
│   Request    │    │   Backend    │    │   Payout     │    │ Account  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────┘
       │                   │                   │                  │
       │ 1. Request payout │                   │                  │
       │ (₹500)            │                   │                  │
       │──────────────────▶│                   │                  │
       │                   │                   │                  │
       │                   │ 2. Validate       │                  │
       │                   │ - balance check   │                  │
       │                   │ - min amount      │                  │
       │                   │ - bank details    │                  │
       │                   │                   │                  │
       │                   │ 3. Create payout  │                  │
       │                   │──────────────────▶│                  │
       │                   │                   │                  │
       │                   │                   │ 4. Process       │
       │                   │                   │ transfer         │
       │                   │                   │─────────────────▶│
       │                   │                   │                  │
       │                   │ 5. Webhook        │                  │
       │                   │ payout.processed  │                  │
       │                   │◀──────────────────│                  │
       │                   │                   │                  │
       │ 6. Confirmation   │                   │                  │
       │◀──────────────────│                   │                  │
       │   (status update) │                   │                  │
```

---

## Quality Assurance Economics

### Multi-Annotator Cost

```
Task Cost = (Base Price) × (Number of Annotators)

Example:
- Classification task: 5 credits
- Required annotators: 3
- Total cost: 15 credits

This provides:
- 3 independent annotations
- Consensus calculation
- Higher confidence output
```

### Honeypot Economics

```python
# Honeypots are tasks with known ground truth
# Mixed into regular task flow (10% of tasks)

# No additional cost to client (included in pricing)
# Annotators are paid for honeypots
# Failed honeypots affect trust level (no payment)
```

### Expert Review Cost

```python
class ExpertPaymentConfig:
    # Experts are paid higher rates for review work
    BASE_REVIEW_RATES = {
        'classification': Decimal('5.0'),   # 2.5x annotator rate
        'bounding_box': Decimal('10.0'),    # 2x annotator rate
        'segmentation': Decimal('25.0'),    # 1.67x annotator rate
    }
    
    # Expert levels
    LEVEL_MULTIPLIERS = {
        'junior_expert': Decimal('1.0'),
        'senior_expert': Decimal('1.3'),
        'lead_expert': Decimal('1.5'),
    }
```

---

## Pricing Structure

### Complete Pricing Example

**Project: E-commerce Product Images**
- 10,000 product images
- Bounding boxes for product detection
- 5 object classes

```
COST BREAKDOWN:

1. Security Deposit:
   - Base fee: ₹500
   - Storage (5 GB): ₹50
   - Annotation estimate: 10,000 × 8 credits × 1.5 = ₹120,000
   - Total deposit: ₹120,550

2. Annotation Cost:
   - Base: 3 credits/image
   - Bounding box: 5 credits/annotation
   - Average 2 annotations/image
   - Total: 10,000 × (3 + 5×2) = 130,000 credits

3. Multi-annotator:
   - 3 annotators per task
   - Total: 130,000 × 3 = 390,000 credits

4. Final Cost:
   - 390,000 credits × ₹1.25 (Scale plan) = ₹487,500
   - Security deposit refunded after completion

DISTRIBUTION:
- Platform revenue: ~₹268,125 (55%)
- Annotator payments: ~₹219,375 (45%)
  - Per annotator avg: ₹2.19/image
```

### API Usage Billing

```python
class APIUsageTracking:
    # Free tier limits (per day)
    free_read_limit = 10000    # GET requests
    free_write_limit = 1000    # POST/PUT/PATCH
    free_export_limit = 100    # Export operations
    
    # Overage rates
    # Read: 1 credit per 1000 requests over limit
    # Write: 5 credits per 1000 requests over limit  
    # Export: 10 credits per export over limit
```

### Storage Billing

```python
class StorageBilling:
    # First 5 GB free (or subscription amount)
    free_storage_gb = 5
    
    # Overage: 1 credit per GB per month
    storage_rate = Decimal('1.0')
    
    # Tiered rates for large storage
    STORAGE_TIER_RATES = {
        'standard': {'min': 5, 'max': 50, 'rate': Decimal('5')},   # ₹5/GB
        'large': {'min': 50, 'max': 500, 'rate': Decimal('3')},    # ₹3/GB
        'enterprise': {'min': 500, 'rate': Decimal('2')},          # ₹2/GB
    }
```

---

## Revenue Model

### Revenue Streams

| Stream | Description | Margin |
|--------|-------------|--------|
| **Credit Sales** | PAYG credit packages | 50-60% |
| **Subscriptions** | Monthly/annual plans | 55-65% |
| **API Overage** | Usage beyond limits | 80% |
| **Storage Overage** | Storage beyond limits | 70% |
| **Enterprise Services** | Custom solutions | Variable |

### Unit Economics

```
Per Annotation Unit Economics:

Client pays: ₹10 (example)
├── Platform keeps: ₹5.50 (55%)
│   ├── Infrastructure: ₹1.00
│   ├── Quality systems: ₹1.50
│   ├── Support/operations: ₹1.00
│   └── Margin: ₹2.00
│
└── Annotator receives: ₹4.50 (45%)
    ├── Base payment: ₹3.50
    ├── Quality bonus: ₹0.50
    └── Trust bonus: ₹0.50
```

### Annotator Economics

**Sample Annotator Earnings (Monthly):**

| Level | Tasks/Day | Rate/Task | Daily | Monthly |
|-------|-----------|-----------|-------|---------|
| New | 50 | ₹2.40 | ₹120 | ₹3,600 |
| Junior | 80 | ₹3.00 | ₹240 | ₹7,200 |
| Regular | 100 | ₹3.30 | ₹330 | ₹9,900 |
| Senior | 120 | ₹3.90 | ₹468 | ₹14,040 |
| Expert | 150 | ₹4.50 | ₹675 | ₹20,250 |

*Assumes classification tasks averaging 3 credits*

---

## Gamification & Incentives

### Bonus Pools

```python
class BonusPool:
    POOL_TYPES = [
        ('daily_top', 'Daily Top Performers'),
        ('weekly_top', 'Weekly Top Performers'),
        ('quality_bonus', 'Quality Bonus Pool'),
        ('referral', 'Referral Bonus'),
        ('special_event', 'Special Event'),
    ]
    
    total_amount = DecimalField()  # e.g., ₹10,000
    distribution_rules = JSONField()  # e.g., top 10 get share
```

### Achievement Rewards

```python
# Example achievements
ACHIEVEMENTS = [
    # Volume achievements
    {'code': 'first_100', 'name': 'Century', 'tasks': 100, 'bonus': 100},
    {'code': 'first_1000', 'name': 'Millennial', 'tasks': 1000, 'bonus': 500},
    
    # Quality achievements
    {'code': 'perfectionist', 'name': 'Perfectionist', 'accuracy': 98, 'bonus': 200},
    
    # Streak achievements
    {'code': 'week_warrior', 'name': 'Week Warrior', 'streak': 7, 'bonus': 50},
    {'code': 'month_master', 'name': 'Month Master', 'streak': 30, 'bonus': 300},
]
```

### Leaderboard Bonuses

```python
# Daily leaderboard (top 10 performers)
DAILY_LEADERBOARD_BONUSES = {
    1: Decimal('500'),   # 1st place
    2: Decimal('300'),   # 2nd place
    3: Decimal('200'),   # 3rd place
    4-10: Decimal('50'), # 4th-10th place
}
```

---

## Summary

### Key Business Metrics

| Metric | Description |
|--------|-------------|
| **GMV** | Total credits consumed |
| **Take Rate** | Platform margin (50-60%) |
| **Annotator Payout** | Total paid to annotators |
| **CAC** | Cost to acquire client |
| **LTV** | Lifetime value of client |
| **Annotator Retention** | % active after 90 days |
| **Quality Score** | Average annotation accuracy |

### Competitive Advantages

1. **Quality Assurance**: Multi-annotator consensus + expert review
2. **Fair Pricing**: Transparent credit-based system
3. **Annotator Incentives**: Gamification drives quality
4. **Flexible Billing**: PAYG and subscription options
5. **Medical Specialization**: Domain-specific pricing and expertise

---

## Next Steps

- [Backend Architecture →](./BACKEND_ARCHITECTURE.md)
- [Frontend Architecture →](./FRONTEND_ARCHITECTURE.md)
- [Annotator Workflow →](./ANNOTATOR_WORKFLOW.md)
