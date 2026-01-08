import { CTA } from "../../components/CTA/CTA";
import { Features } from "../../components/Features/Features";
import { Footer } from "../../components/Footer/Footer";
import { Hero } from "../../components/Herosection/Hero";
import { Navbar } from "../../components/Navbar/Navbar";
import { Testimonials } from "../../components/Testimonials/Testimonials";
import type { Page } from "../types/Page";


export const LandingPage: Page = () => {
  return (
    <div className="min-h-screen bg-black">
      <Navbar />
      <Hero />
      <Features />
      <Testimonials />
      <CTA />
      <Footer />
    </div>
  );
};

LandingPage.title = "Welcome";
LandingPage.path = "/";
LandingPage.exact = true;

