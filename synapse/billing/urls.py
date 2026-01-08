from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    SubscriptionPlanViewSet,
    CreditPackageViewSet,
    BillingViewSet,
    AnnotationPricingViewSet,
    ProjectBillingViewSet,
    APIUsageViewSet,
)

router = DefaultRouter()
router.register(r"plans", SubscriptionPlanViewSet, basename="subscription-plans")
router.register(r"packages", CreditPackageViewSet, basename="credit-packages")
router.register(r"billing", BillingViewSet, basename="billing")
router.register(r"pricing", AnnotationPricingViewSet, basename="annotation-pricing")
router.register(r"project-billing", ProjectBillingViewSet, basename="project-billing")
router.register(r"api-usage", APIUsageViewSet, basename="api-usage")

urlpatterns = [
    path("", include(router.urls)),
]





