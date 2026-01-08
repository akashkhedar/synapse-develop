import { Footer } from "../../components/Footer/Footer";
import { Navbar } from "../../components/Navbar/Navbar";
import type { Page } from "../types/Page";

export const ApiDocsPage: Page = () => {
  return (
    <div className="min-h-screen bg-black">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            API Documentation
          </h1>
          <p className="text-xl text-gray-400">
            Comprehensive API reference for Synapse platform
          </p>
        </div>
        
        <div className="bg-neutral-900 rounded-lg p-8 border border-neutral-800">
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-semibold text-white mb-4">
              Coming Soon
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              API documentation is under development. Check back soon for detailed 
              endpoints, authentication guides, and code examples.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

ApiDocsPage.title = "API Documentation";
ApiDocsPage.path = "/docs";
ApiDocsPage.exact = true;

