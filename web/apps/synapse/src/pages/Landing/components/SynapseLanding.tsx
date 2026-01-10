import { Navigation } from "./Navigation";
import { HeroSection } from "./HeroSection";
import { FeaturesSection } from "./FeaturesSection";
import { ProductsSection } from "./ProductsSection";
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
      <TrustSection />
      <CTASection />
      <Footer />
    </div>
  );
};
