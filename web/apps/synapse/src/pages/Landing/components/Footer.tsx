export const Footer = () => {
  const footerLinks = {
    "Platform": ["Features", "Pricing", "Templates", "Integrations", "API"],
    "Solutions": ["Computer Vision", "NLP", "Audio", "LLM Training"],
    "Resources": ["Documentation", "Blog", "Customer Stories", "Research"],
    "Company": ["About", "Careers", "Contact", "Partners"]
  };

  return (
    <footer className="bg-black border-t border-gray-900 py-16">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid md:grid-cols-5 gap-12 mb-12">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 border-2 border-white flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="text-white font-semibold text-xl">Synapse</span>
            </div>
            <p className="text-gray-500 text-sm leading-relaxed">
              Enterprise data annotation platform for AI teams.
            </p>
          </div>

          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">{category}</h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-gray-500 hover:text-gray-300 text-sm transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-900 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-600 text-sm">
            © 2026 Synapse. All rights reserved.
          </p>
          <div className="flex gap-6">
            {["Privacy", "Terms", "Security"].map((link) => (
              <a key={link} href="#" className="text-gray-600 hover:text-gray-400 text-sm transition-colors">
                {link}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};
