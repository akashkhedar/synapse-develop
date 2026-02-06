"""URL configuration for annotators app"""

from django.urls import path
from django.conf import settings
from . import api, views, honeypot_api

app_name = "annotators"

urlpatterns = [
    # Registration & Verification
    path("register", api.AnnotatorRegistrationAPI.as_view(), name="register"),
    path("login", api.AnnotatorLoginAPI.as_view(), name="login"),
    path(
        "verify-email", api.AnnotatorEmailVerificationAPI.as_view(), name="verify-email"
    ),
    path("logout", api.AnnotatorLogoutAPI.as_view()),
    path(
        "resend-verification",
        api.ResendVerificationEmailAPI.as_view(),
        name="resend-verification",
    ),
    # Profile
    path("profile", api.AnnotatorProfileAPI.as_view(), name="profile"),
    # Project Assignment & Tasks
    path(
        "task-assignment",
        api.AnnotatorTaskAssignmentAPI.as_view(),
        name="task-assignment",
    ),
    # Test page view (React-based)
    path("test/", views.annotator_test_page, name="test-page"),
    # Test APIs
    path(
        "test/questions", api.AnnotatorTestQuestionsAPI.as_view(), name="test-questions"
    ),
    path("test/start", api.AnnotatorTestStartAPI.as_view(), name="test-start"),
    path("test/submit", api.AnnotatorTestSubmitAPI.as_view(), name="test-submit"),
    path("test/status", api.AnnotatorTestStatusAPI.as_view(), name="test-status"),
    # ============================================================================
    # PAYMENT URLS
    # ============================================================================
    # Earnings & Balance
    path("earnings/", api.AnnotatorEarningsAPI.as_view(), name="earnings"),
    path("transactions", api.AnnotatorTransactionsAPI.as_view(), name="transactions"),
    path("trust-level", api.AnnotatorTrustLevelAPI.as_view(), name="trust-level"),
    # Payout Requests
    path("payouts", api.PayoutRequestAPI.as_view(), name="payouts"),
    path(
        "payouts/<int:payout_id>/cancel",
        api.PayoutCancelAPI.as_view(),
        name="payout-cancel",
    ),
    # Bank Details
    path("bank-details", api.BankDetailsAPI.as_view(), name="bank-details"),
    # Payment Settings (public config)
    path("payment-settings", api.PaymentSettingsAPI.as_view(), name="payment-settings"),
    # Test Payout (for testing RazorpayX integration)
    path("test-payout", api.TestPayoutAPI.as_view(), name="test-payout"),
    # RazorpayX Balance (admin only)
    path(
        "razorpayx-balance", api.RazorpayXBalanceAPI.as_view(), name="razorpayx-balance"
    ),
    # Razorpay Test Mode Info (get test bank accounts/UPI IDs)
    path(
        "razorpay-test-mode",
        api.RazorpayTestModeAPI.as_view(),
        name="razorpay-test-mode",
    ),
    # Test payout with Razorpay test accounts (for testing scenarios)
    path(
        "test-payout-with-test-account",
        api.TestPayoutWithTestAccountAPI.as_view(),
        name="test-payout-with-test-account",
    ),
    # Admin Payout Management
    path(
        "admin/payouts",
        api.AdminPayoutApprovalAPI.as_view(),
        name="admin-payouts",
    ),
    path(
        "admin/payouts/<int:payout_id>/approve",
        api.AdminPayoutApprovalAPI.as_view(),
        name="admin-payout-approve",
    ),
    path(
        "admin/payouts/<int:payout_id>/reject",
        api.AdminPayoutRejectAPI.as_view(),
        name="admin-payout-reject",
    ),
    # ============================================================================
    # AUTOMATIC TASK ASSIGNMENT URLS
    # ============================================================================
    # Trigger auto-assignment
    path(
        "trigger-assignment",
        api.TriggerAutoAssignmentAPI.as_view(),
        name="trigger-assignment",
    ),
    # Assignment metrics
    path(
        "assignment-metrics/<int:project_id>",
        api.AssignmentMetricsAPI.as_view(),
        name="assignment-metrics",
    ),
    # ============================================================================
    # GAMIFICATION URLS
    # ============================================================================
    # Gamification stats
    path(
        "gamification", api.AnnotatorGamificationStatsAPI.as_view(), name="gamification"
    ),
    # Leaderboard
    path("leaderboard", api.LeaderboardAPI.as_view(), name="leaderboard"),
    # Achievements
    path("achievements", api.AchievementsAPI.as_view(), name="achievements"),
    # Skill badges
    path("skill-badges", api.SkillBadgesAPI.as_view(), name="skill-badges"),
    # Streak info
    path("streak", api.StreakInfoAPI.as_view(), name="streak"),
    # ============================================================================
    # NOTIFICATION URLS
    # ============================================================================
    # Get annotator notifications
    path(
        "notifications",
        api.AnnotatorNotificationsAPI.as_view(),
        name="notifications",
    ),
    # Mark notification as read
    path(
        "notifications/mark-read",
        api.AnnotatorNotificationMarkReadAPI.as_view(),
        name="notifications-mark-read",
    ),
    path(
        "notifications/<int:notification_id>/mark-read",
        api.AnnotatorNotificationMarkReadAPI.as_view(),
        name="notification-mark-read",
    ),
    # Get tasks that need rework
    path(
        "rework-tasks",
        api.AnnotatorReworkTasksAPI.as_view(),
        name="rework-tasks",
    ),
    # ============================================================================
    # ACCURACY AND PERFORMANCE URLS
    # ============================================================================
    # Annotator accuracy statistics
    path(
        "accuracy-stats",
        api.AnnotatorAccuracyStatsAPI.as_view(),
        name="accuracy-stats",
    ),
    # Annotator performance history
    path(
        "performance-history",
        api.AnnotatorPerformanceHistoryAPI.as_view(),
        name="performance-history",
    ),
    # ============================================================================
    # CONSENSUS URLS
    # ============================================================================
    # Task consensus status
    path(
        "consensus/task/<int:task_id>",
        api.TaskConsensusStatusAPI.as_view(),
        name="task-consensus-status",
    ),
    # Project consensus overview
    path(
        "consensus/project/<int:project_id>",
        api.ProjectConsensusOverviewAPI.as_view(),
        name="project-consensus-overview",
    ),
    # Finalize consensus
    path(
        "consensus/finalize/<int:task_id>",
        api.FinalizeConsensusAPI.as_view(),
        name="finalize-consensus",
    ),
    # Bulk finalize
    path(
        "consensus/bulk-finalize/<int:project_id>",
        api.BulkFinalizeConsensusAPI.as_view(),
        name="bulk-finalize-consensus",
    ),
    # Annotator quality stats
    path(
        "quality-stats",
        api.AnnotatorQualityStatsAPI.as_view(),
        name="quality-stats",
    ),
    # Update consolidated result
    path(
        "consensus/update-result/<int:task_id>",
        api.UpdateConsolidatedResultAPI.as_view(),
        name="update-consolidated-result",
    ),
    # ============================================================================
    # ADMIN EXPERT MANAGEMENT URLS
    # ============================================================================
    # Assign expert role to user
    path(
        "admin/assign-expert",
        api.AdminAssignExpertAPI.as_view(),
        name="admin-assign-expert",
    ),
    # Revoke expert role
    path(
        "admin/revoke-expert",
        api.AdminRevokeExpertAPI.as_view(),
        name="admin-revoke-expert",
    ),
    # Assign expert to project
    path(
        "admin/assign-expert-project",
        api.AdminAssignExpertToProjectAPI.as_view(),
        name="admin-assign-expert-project",
    ),
    # List all experts
    path(
        "admin/experts",
        api.AdminListExpertsAPI.as_view(),
        name="admin-list-experts",
    ),
    # Manage expert project assignments (new)
    path(
        "admin/expert-project-assignments",
        api.AdminExpertProjectAssignmentAPI.as_view(),
        name="admin-expert-project-assignments",
    ),
    # ============================================================================
    # EXPERT REVIEW URLS
    # ============================================================================
    # Expert dashboard
    path(
        "expert/dashboard",
        api.ExpertDashboardAPI.as_view(),
        name="expert-dashboard",
    ),
    # Expert projects (returns review tasks in projects format)
    path(
        "expert/projects",
        api.ExpertProjectsAPI.as_view(),
        name="expert-projects",
    ),
    # Expert review task list
    path(
        "expert/reviews",
        api.ExpertReviewTaskListAPI.as_view(),
        name="expert-review-list",
    ),
    # Expert review task detail
    path(
        "expert/reviews/<int:review_id>",
        api.ExpertReviewTaskDetailAPI.as_view(),
        name="expert-review-detail",
    ),
    # Start review
    path(
        "expert/reviews/<int:review_id>/start",
        api.ExpertStartReviewAPI.as_view(),
        name="expert-start-review",
    ),
    # Submit review
    path(
        "expert/reviews/<int:review_id>/submit",
        api.ExpertSubmitReviewAPI.as_view(),
        name="expert-submit-review",
    ),
    # ============================================================================
    # EXPERT EARNINGS & PAYOUT URLS
    # ============================================================================
    # Expert earnings
    path(
        "expert/earnings",
        api.ExpertEarningsAPI.as_view(),
        name="expert-earnings",
    ),
    # Expert payout requests
    path(
        "expert/payouts",
        api.ExpertPayoutRequestAPI.as_view(),
        name="expert-payouts",
    ),
    # Expert bank details
    path(
        "expert/bank-details",
        api.ExpertBankDetailsAPI.as_view(),
        name="expert-bank-details",
    ),
    # ============================================================================
    # EXPERT REVIEW ACCEPT/REJECT URLS (NEW)
    # ============================================================================
    # Accept/reject consolidated annotation
    path(
        "expert/review/<int:task_id>/action",
        api.ExpertReviewActionAPI.as_view(),
        name="expert-review-action",
    ),
    # Get detailed task info for review
    path(
        "expert/review/<int:task_id>/details",
        api.ExpertReviewTaskDetailAPI.as_view(),
        name="expert-review-task-details",
    ),
    # Get pending reviews for expert
    path(
        "expert/pending-reviews",
        api.ExpertPendingReviewsAPI.as_view(),
        name="expert-pending-reviews",
    ),
    # ============================================================================
    # EXPERT TASK ASSIGNMENT URLS
    # ============================================================================
    # Expert's task queue (simplified project cards view)
    path(
        "expert/task-queue",
        api.ExpertTaskQueueAPI.as_view(),
        name="expert-task-queue",
    ),
    # Get pending tasks awaiting expert assignment (admin)
    path(
        "expert/pending-tasks",
        api.ExpertPendingTasksAPI.as_view(),
        name="expert-pending-tasks",
    ),
    # Get available experts for assignment (admin)
    path(
        "expert/available-experts",
        api.ExpertAvailableExpertsAPI.as_view(),
        name="expert-available-experts",
    ),
    # Manually assign task to expert (admin)
    path(
        "expert/assign-task",
        api.ExpertAssignTaskAPI.as_view(),
        name="expert-assign-task",
    ),
    # Batch assign pending tasks (admin)
    path(
        "expert/batch-assign",
        api.ExpertBatchAssignAPI.as_view(),
        name="expert-batch-assign",
    ),
    # Get assignment statistics
    path(
        "expert/assignment-stats",
        api.ExpertAssignmentStatsAPI.as_view(),
        name="expert-assignment-stats",
    ),
    # ============================================================================
    # EXPERT PAYMENT URLS
    # ============================================================================
    # Payment dashboard
    path(
        "expert/payment/dashboard",
        api.ExpertPaymentDashboardAPI.as_view(),
        name="expert-payment-dashboard",
    ),
    # Transaction history
    path(
        "expert/payment/transactions",
        api.ExpertTransactionHistoryAPI.as_view(),
        name="expert-payment-transactions",
    ),
    # Request payout
    path(
        "expert/payment/request-payout",
        api.ExpertRequestPayoutAPI.as_view(),
        name="expert-request-payout",
    ),
    # Get payout requests
    path(
        "expert/payment/payout-requests",
        api.ExpertPayoutRequestsAPI.as_view(),
        name="expert-payout-requests",
    ),
    # Update payment details
    path(
        "expert/payment/update-details",
        api.ExpertUpdatePaymentDetailsAPI.as_view(),
        name="expert-update-payment-details",
    ),
    # ============================================================================
    # ADMIN PAYMENT URLS
    # ============================================================================
    # Get pending payouts (admin)
    path(
        "admin/expert-payouts/pending",
        api.AdminPendingPayoutsAPI.as_view(),
        name="admin-pending-payouts",
    ),
    # Process payout (admin)
    path(
        "admin/expert-payouts/<int:payout_id>/process",
        api.AdminProcessPayoutAPI.as_view(),
        name="admin-process-payout",
    ),
    # Expert payment analytics (admin)
    path(
        "admin/expert-analytics",
        api.AdminExpertPaymentAnalyticsAPI.as_view(),
        name="admin-expert-analytics",
    ),
    # ============================================================================
    # HONEYPOT MANAGEMENT URLS
    # ============================================================================
    # List/Create honeypots for a project
    path(
        "honeypots/project/<int:project_id>",
        honeypot_api.ProjectHoneypotsAPI.as_view(),
        name="project-honeypots",
    ),
    # Get/Update/Delete specific honeypot
    path(
        "honeypots/project/<int:project_id>/<int:honeypot_id>",
        honeypot_api.ProjectHoneypotDetailAPI.as_view(),
        name="project-honeypot-detail",
    ),
    # Honeypot statistics
    path(
        "honeypots/project/<int:project_id>/stats",
        honeypot_api.ProjectHoneypotStatsAPI.as_view(),
        name="project-honeypot-stats",
    ),
    # Honeypot configuration
    path(
        "honeypots/project/<int:project_id>/config",
        honeypot_api.ProjectHoneypotConfigAPI.as_view(),
        name="project-honeypot-config",
    ),
    # Bulk create honeypots
    path(
        "honeypots/project/<int:project_id>/bulk",
        honeypot_api.ProjectHoneypotBulkCreateAPI.as_view(),
        name="project-honeypot-bulk",
    ),
    # ============================================================================
    # EXPERTISE SYSTEM URLS
    # ============================================================================
    # List all expertise categories (public)
    path(
        "expertise/categories",
        api.ExpertiseCategoryListAPI.as_view(),
        name="expertise-categories",
    ),
    # Get specific category details
    path(
        "expertise/categories/<slug:category_slug>",
        api.ExpertiseCategoryDetailAPI.as_view(),
        name="expertise-category-detail",
    ),
    # Annotator expertise management
    path(
        "expertise/my-expertise",
        api.AnnotatorExpertiseListAPI.as_view(),
        name="my-expertise",
    ),
    path(
        "expertise/my-expertise/<int:expertise_id>",
        api.AnnotatorExpertiseDetailAPI.as_view(),
        name="my-expertise-detail",
    ),
    # Expertise summary for dashboard
    path(
        "expertise/summary",
        api.AnnotatorExpertiseSummaryAPI.as_view(),
        name="expertise-summary",
    ),
    # Expertise test management
    path(
        "expertise/test/start/<int:expertise_id>",
        api.ExpertiseTestStartAPI.as_view(),
        name="expertise-test-start",
    ),
    path(
        "expertise/test/<int:test_id>/submit",
        api.ExpertiseTestSubmitAPI.as_view(),
        name="expertise-test-submit",
    ),
    path(
        "expertise/test/<int:test_id>",
        api.ExpertiseTestDetailAPI.as_view(),
        name="expertise-test-detail",
    ),
]
