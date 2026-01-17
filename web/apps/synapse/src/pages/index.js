import { ProjectsPage } from "./Projects/Projects";
import { HomePage } from "./Home/HomePage";
import { LandingPage } from "./Landing/LandingPage";
import { ApiDocsPage } from "./ApiDocs/ApiDocsPage";
import {
  AnnotatorSkillTest,
  TestResult,
  EarningsDashboard,
  PayoutRequest,
} from "./Annotators";
import {
  ExpertEarnings,
  ExpertPayoutPage,
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
ExpertEarnings.title = "Expert Earnings";
ExpertEarnings.path = "/expert/earnings";
ExpertEarnings.exact = true;

ExpertPayoutPage.title = "Expert Payout";
ExpertPayoutPage.path = "/expert/payouts";
ExpertPayoutPage.exact = true;

export const Pages = [
  LandingPage,
  ServicesPage,
  AboutPage,
  SecurityPage,
  ContactPage,
  BlogListPage,
  BlogPostPage,
  ApiDocsPage,
  AnnotatorSkillTest,
  TestResult,
  EarningsDashboard,
  PayoutRequest,
  ExpertEarnings,
  ExpertPayoutPage,
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
