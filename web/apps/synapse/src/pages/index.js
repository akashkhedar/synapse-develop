import { ProjectsPage } from "./Projects/Projects";
import { HomePage } from "./Home/HomePage";
import { LandingPage } from "./Landing/LandingPage";
import { ApiDocsPage } from "./ApiDocs/ApiDocsPage";
import {
  AnnotatorSignup,
  AnnotatorLogin,
  VerificationSent,
  VerifyEmail,
  AnnotatorTest,
  AnnotatorSkillTest,
  TestResult,
  EarningsDashboard,
  PayoutRequest,
} from "./Annotators";
import {
  ExpertEarnings,
  ExpertDashboard,
  ExpertProjects,
  ExpertReviewPage,
  ExpertProjectReview,
} from "./Expert";
import { ServicesPage } from "./Services";
import { AboutPage } from "./About";
import { SecurityPage } from "./Security";
import { ContactPage } from "./Contact";
import { BlogListPage, BlogPostPage } from "./Blog";
import { OrganizationPage } from "./Organization";
import { ModelsPage } from "./Organization/Models/ModelsPage";
import { AcceptInvite } from "./AcceptInvite";
import { BillingPage } from "./Billing";
import { FF_HOMEPAGE, isFF } from "../utils/feature-flags";
import { pages } from "@synapse/app-common";

// Configure AcceptInvite page
AcceptInvite.title = "Accept Invitation";
AcceptInvite.path = "/invite";
AcceptInvite.exact = true;

// Configure Annotator pages
AnnotatorSignup.title = "Annotator Signup";
AnnotatorSignup.path = "/annotators/signup";
AnnotatorSignup.exact = true;

AnnotatorLogin.title = "Annotator Login";
AnnotatorLogin.path = "/annotators/login";
AnnotatorLogin.exact = true;

VerificationSent.title = "Email Verification Sent";
VerificationSent.path = "/annotators/verification-sent";
VerificationSent.exact = true;

VerifyEmail.title = "Verify Email";
VerifyEmail.path = "/annotators/verify-email";
VerifyEmail.exact = true;

AnnotatorTest.title = "Qualification Test";
AnnotatorTest.path = "/annotators/test";
AnnotatorTest.exact = true;

AnnotatorSkillTest.title = "Skill Assessment";
AnnotatorSkillTest.path = "/annotators/skill-test";
AnnotatorSkillTest.exact = true;

TestResult.title = "Test Results";
TestResult.path = "/annotators/test-result";
TestResult.exact = true;

// Annotator Payment Pages
EarningsDashboard.title = "My Earnings";
EarningsDashboard.path = "/annotators/earnings";
EarningsDashboard.exact = true;

PayoutRequest.title = "Request Payout";
PayoutRequest.path = "/annotators/payouts";
PayoutRequest.exact = true;

// Expert Pages
ExpertDashboard.title = "Expert Dashboard";
ExpertDashboard.path = "/expert/dashboard";
ExpertDashboard.exact = true;

ExpertEarnings.title = "Expert Earnings";
ExpertEarnings.path = "/expert/earnings";
ExpertEarnings.exact = true;

ExpertProjects.title = "Expert Projects";
ExpertProjects.path = "/expert/projects";
ExpertProjects.exact = true;

ExpertReviewPage.title = "Expert Review";
ExpertReviewPage.path = "/expert/task/:taskId";
ExpertReviewPage.exact = true;

ExpertProjectReview.title = "Project Review";
ExpertProjectReview.path = "/expert/review/:projectId";
ExpertProjectReview.exact = true;

export const Pages = [
  LandingPage,
  ServicesPage,
  AboutPage,
  SecurityPage,
  ContactPage,
  BlogListPage,
  BlogPostPage,
  ApiDocsPage,
  AnnotatorSignup,
  AnnotatorLogin,
  VerificationSent,
  VerifyEmail,

  AnnotatorTest,
  AnnotatorSkillTest,
  TestResult,
  EarningsDashboard,
  PayoutRequest,
  ExpertDashboard,
  ExpertEarnings,
  ExpertProjects,
  ExpertReviewPage,
  ExpertProjectReview,
  AcceptInvite,
  BillingPage,
  isFF(FF_HOMEPAGE) && HomePage,
  ProjectsPage,
  OrganizationPage,
  ModelsPage,
  pages.AccountSettingsPage,
].filter(Boolean);

// Configure BillingPage
BillingPage.title = "Billing & Credits";
BillingPage.path = "/billing";
BillingPage.exact = true;

