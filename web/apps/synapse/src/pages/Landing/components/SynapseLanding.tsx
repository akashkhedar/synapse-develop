import { Navigation } from "./Navigation";
import { HeroSection } from "./HeroSection";
import { FeaturesSection } from "./FeaturesSection";
import { ProductsSection } from "./ProductsSection";
import { StatsSection } from "./StatsSection";
import { TrustSection } from "./TrustSection";
import { CTASection } from "./CTASection";
import { Footer } from "./Footer";

// Main Landing Page
export const SynapseLanding = () => {
  return (
    <div className="bg-black min-h-screen">
      <Navigation />
      <HeroSection />
      <FeaturesSection />
      <ProductsSection />
      <StatsSection />
      <TrustSection />
      <CTASection />
      <Footer />
    </div>
  );
};
