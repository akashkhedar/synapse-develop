# Synapse Platform - Comprehensive Testing Plan

## Overview
This document outlines a full end-to-end testing plan for the Synapse annotation platform, covering all major features and edge cases.

---

## Phase 1: User Account Setup

### 1.1 Admin/Client Account
- [ ] Create superuser account (admin)
- [ ] Create organization
- [ ] Verify admin dashboard access

### 1.2 Annotator Accounts
- [ ] Register 5 annotator accounts (annotator1-5@test.com)
- [ ] Verify email verification flow
- [ ] Complete annotator profiles
- [ ] Apply for expertise (Computer Vision, NLP categories)
- [ ] Verify expertise is in "pending" status

### 1.3 Expert Accounts
- [ ] Register 2 expert accounts (expert1-2@test.com)
- [ ] Assign expert roles
- [ ] Assign expertise to experts (matching annotator categories)
- [ ] Verify expert dashboard access

---

## Phase 2: Project Creation & Configuration

### 2.1 Basic Project Creation
- [ ] Create Project A: "Image Classification" 
  - Annotation type: Computer Vision
  - Expertise type: Image Classification
  - Task price: $0.10
  - Required overlap: 2 (for consensus)
- [ ] Create Project B: "Text Sentiment Analysis"
  - Annotation type: NLP
  - Expertise type: Sentiment Analysis
  - Task price: $0.15
  - Required overlap: 1 (single annotator)
- [ ] Create Project C: "Audio Transcription" (no matching annotators)
  - Annotation type: Audio/Speech
  - Expertise: Transcription
  - Task price: $0.20

### 2.2 Project Configuration
- [ ] Configure labeling interfaces for each project
- [ ] Set honeypot configuration (5% injection rate)
- [ ] Upload ground truth tasks for honeypots
- [ ] Set quality thresholds (70% accuracy, 80% honeypot pass rate)

### 2.3 Data Import
- [ ] Import 50 tasks to Project A
- [ ] Import 30 tasks to Project B
- [ ] Import 20 tasks to Project C
- [ ] Verify task counts in dashboard

---

## Phase 3: Annotator Management & Expertise

### 3.1 Expertise Verification
- [ ] Admin approves expertise for annotator1-3 (Computer Vision)
- [ ] Admin approves expertise for annotator4-5 (NLP)
- [ ] Verify expertise status changes to "verified"
- [ ] Verify annotators with Audio expertise are NOT approved (none exist)

### 3.2 Trust Level Initialization
- [ ] Verify all new annotators start at "NEW" trust level
- [ ] Verify 0.8x earnings multiplier for NEW level
- [ ] Confirm task/accuracy requirements displayed correctly

### 3.3 Project Eligibility
- [ ] Verify annotator1-3 are eligible for Project A
- [ ] Verify annotator4-5 are eligible for Project B
- [ ] Verify NO annotators are eligible for Project C (Audio)
- [ ] Test filtering on project member page

---

## Phase 4: Task Assignment System

### 4.1 Assignment When Annotators Available
- [ ] Trigger assignment for Project A
- [ ] Verify tasks assigned to annotator1-3 based on expertise match
- [ ] Verify assignment round-robin or load balancing
- [ ] Check TaskAssignment records created with status="assigned"

### 4.2 Assignment Queue (No Available Annotators)
- [ ] Trigger assignment for Project C
- [ ] Verify tasks go to pending queue (no matching annotators)
- [ ] Log message indicates waiting for annotators
- [ ] Tasks remain unassigned

### 4.3 Assignment Limits
- [ ] Verify max concurrent tasks per annotator enforced
- [ ] Test when annotator has too many pending tasks
- [ ] Verify queue rebalancing when annotator completes tasks

### 4.4 Annotator Availability
- [ ] Set annotator1 as inactive
- [ ] Trigger reassignment
- [ ] Verify tasks NOT assigned to inactive annotator
- [ ] Reactivate annotator1 and verify they receive new tasks

---

## Phase 5: Annotation Workflow

### 5.1 Annotator Submits Annotation
- [ ] Login as annotator1
- [ ] Open assigned task from Project A
- [ ] Submit annotation
- [ ] Verify TaskAssignment status → "completed"
- [ ] Verify Annotation record created

### 5.2 Streak System
- [ ] Verify AnnotatorStreak record created/updated
- [ ] Confirm current_streak incremented
- [ ] Confirm last_activity_date updated
- [ ] Submit annotation next day - verify streak continues
- [ ] Skip a day - verify streak resets to 1

### 5.3 Multiple Annotations (Overlap)
- [ ] For Project A (overlap=2), have annotator1 complete task
- [ ] Have annotator2 complete same task
- [ ] Verify TaskConsensus updated (current_annotations=2)
- [ ] Verify consolidation triggered

### 5.4 Skip Task
- [ ] Test skipping a task (was_cancelled=true)
- [ ] Verify task reassigned to another annotator
- [ ] Verify skip counted in annotator stats

---

## Phase 6: Honeypot System

### 6.1 Honeypot Injection
- [ ] Verify honeypots injected during assignment (5% rate)
- [ ] Honeypot tasks marked with is_honeypot=True
- [ ] Ground truth stored in expected_result

### 6.2 Honeypot Evaluation - Pass
- [ ] Annotator submits correct answer on honeypot
- [ ] Verify HoneypotResult created with passed=True
- [ ] Trust level honeypot_pass_rate updated
- [ ] No fraud flags added

### 6.3 Honeypot Evaluation - Fail
- [ ] Annotator submits incorrect answer on honeypot
- [ ] Verify HoneypotResult created with passed=False
- [ ] Trust level updated, fraud_flags potentially incremented
- [ ] Multiple failures → suspension check

### 6.4 Honeypot Skip Consolidation
- [ ] Confirm honeypot tasks skip consolidation workflow
- [ ] Honeypots do not create expert review tasks

---

## Phase 7: Consolidation Algorithm

### 7.1 Perfect Agreement
- [ ] Both annotators submit identical annotations
- [ ] Verify consensus score = 1.0
- [ ] Task marked as consolidated
- [ ] No expert review needed

### 7.2 High Agreement (Above Threshold)
- [ ] Annotators submit similar but not identical results
- [ ] Verify consensus score calculated
- [ ] If score > threshold → auto-consolidated
- [ ] Final annotation created from merged results

### 7.3 Low Agreement (Below Threshold)
- [ ] Annotators submit conflicting annotations
- [ ] Verify consensus score < threshold
- [ ] Task flagged for expert review
- [ ] ExpertReviewTask created

### 7.4 Partial Completion
- [ ] Only 1 of 2 required annotations submitted
- [ ] Verify consolidation NOT triggered yet
- [ ] Task waits for remaining annotation

---

## Phase 8: Expert Review System

### 8.1 Expert Assignment
- [ ] Verify ExpertReviewTask assigned to expert with matching expertise
- [ ] Expert receives notification/sees task in queue
- [ ] Assignment respects expert availability

### 8.2 Expert Review Workflow
- [ ] Login as expert1
- [ ] View pending review tasks
- [ ] See both annotator submissions
- [ ] Select correct annotation OR create merged result
- [ ] Submit expert decision

### 8.3 Expert Review Completion
- [ ] Verify final annotation created from expert decision
- [ ] Task marked as reviewed
- [ ] Annotator accuracy scores updated based on expert decision
- [ ] Expert earnings recorded

### 8.4 No Available Experts
- [ ] Create review task for category with no experts
- [ ] Verify task queued, not assigned
- [ ] Add expert with matching expertise
- [ ] Verify task now assigned to new expert

---

## Phase 9: Payment & Earnings System

### 9.1 Earnings Calculation
- [ ] Verify earnings recorded per completed annotation
- [ ] Base rate = task price × trust level multiplier
- [ ] Streak bonus applied if applicable
- [ ] EarningsTransaction created

### 9.2 Earnings Stages
- [ ] Annotation submitted → "pending" stage
- [ ] After consolidation/review → "approved" stage
- [ ] Available for withdrawal

### 9.3 Trust Level Progression
- [ ] Complete 45 tasks with 70%+ accuracy
- [ ] Verify trust level upgrades: NEW → JUNIOR
- [ ] Multiplier increases from 0.8x to 1.0x
- [ ] Continue progression through REGULAR, SENIOR, EXPERT

### 9.4 Dashboard Display
- [ ] Verify earnings summary shows correct totals
- [ ] Daily earnings chart displays data
- [ ] Activity calendar shows completed days
- [ ] Streak count accurate

---

## Phase 10: Edge Cases & Error Handling

### 10.1 Concurrent Assignments
- [ ] Multiple users try to claim same task
- [ ] Verify only one succeeds (task locking)
- [ ] Others receive different tasks

### 10.2 Annotator Mid-Task Suspension
- [ ] Annotator gets suspended while task assigned
- [ ] Verify pending tasks reassigned
- [ ] Completed work preserved

### 10.3 Project Deletion/Deactivation
- [ ] Deactivate project with pending tasks
- [ ] Verify assignments cancelled
- [ ] Annotators notified

### 10.4 Expert Unavailable During Review
- [ ] All experts for category become unavailable
- [ ] Verify review tasks remain in queue
- [ ] Tasks assigned when expert becomes available

### 10.5 Data Import Errors
- [ ] Import malformed data
- [ ] Verify graceful error handling
- [ ] Partial import doesn't corrupt existing data

---

## Phase 11: API & Integration Testing

### 11.1 REST API Endpoints
- [ ] Test all annotation CRUD endpoints
- [ ] Test project management endpoints
- [ ] Test user/profile endpoints
- [ ] Verify authentication/authorization

### 11.2 Webhook Events
- [ ] ANNOTATION_CREATED webhook fires
- [ ] PROJECT_UPDATED webhook fires
- [ ] Verify payload format correct

### 11.3 SDK Integration
- [ ] Test synapse-sdk project operations
- [ ] Test task import via SDK
- [ ] Test annotation retrieval

---

## Test Execution Checklist

### Pre-requisites
- [ ] Fresh database (users deleted)
- [ ] Redis running
- [ ] Frontend built
- [ ] Backend server running

### Test Data
- Sample images for Computer Vision (50 files)
- Sample text for NLP (30 files)
- Sample audio for Audio tasks (20 files)
- Ground truth for honeypots (5 per project)

### Test Accounts
| Email | Role | Expertise |
|-------|------|-----------|
| admin@test.com | Admin/Client | - |
| annotator1@test.com | Annotator | Computer Vision |
| annotator2@test.com | Annotator | Computer Vision |
| annotator3@test.com | Annotator | Computer Vision |
| annotator4@test.com | Annotator | NLP |
| annotator5@test.com | Annotator | NLP |
| expert1@test.com | Expert | Computer Vision |
| expert2@test.com | Expert | NLP |

---

## Automated Test Scripts

Create the following test scripts:
1. `test_user_setup.py` - Create all test accounts
2. `test_project_setup.py` - Create projects and import tasks
3. `test_assignment_flow.py` - Test task assignment scenarios
4. `test_honeypot_system.py` - Test honeypot injection/evaluation
5. `test_consolidation.py` - Test consensus algorithms
6. `test_expert_review.py` - Test expert review workflow
7. `test_earnings.py` - Test payment calculations

---

## Success Criteria

- [ ] All annotators receive tasks matching their expertise
- [ ] Projects without matching annotators queue tasks properly
- [ ] Honeypots correctly evaluate annotator quality
- [ ] Consolidation produces accurate final annotations
- [ ] Expert reviews resolve disagreements
- [ ] Earnings calculated correctly with multipliers
- [ ] Trust levels progress based on performance
- [ ] Streak system tracks daily activity
- [ ] No orphaned tasks or data inconsistencies
