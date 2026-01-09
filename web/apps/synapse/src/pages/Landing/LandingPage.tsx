import { SynapseLanding } from "./components/SynapseLanding";
import type { Page } from "../types/Page";
import "./landing.css";

export const LandingPage: Page = () => {
  return <SynapseLanding />;
};

LandingPage.title = "Welcome";
LandingPage.path = "/";
LandingPage.exact = true;

