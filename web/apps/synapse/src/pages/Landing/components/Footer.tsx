export const Footer = () => {
  const links = [
    "Platform",
    "SDK Documentation", 
    "Pricing",
    "Annotation Types",
    "Enterprise",
    "API Reference",
    "Support"
  ];

  const socialIcons = [
    { name: "Twitter", icon: "𝕏" },
    { name: "LinkedIn", icon: "in" },
    { name: "GitHub", icon: "G" }
  ];

  return (
    <footer className="bg-black border-t border-gray-900/50 py-20 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-start justify-between mb-20">
          {/* Large logo text on left */}
          <div className="flex-1">
            <h2 className="text-[8rem] md:text-[12rem] lg:text-[14rem] font-bold leading-none tracking-tight">
              Synapse
            </h2>
          </div>

          {/* Social icons and links column on right */}
          <div className="ml-12 mt-8">
            {/* Social icons */}
            <div className="flex gap-4 mb-8">
              {socialIcons.map((social) => (
                <a
                  key={social.name}
                  href="#"
                  className="w-10 h-10 rounded-full border border-gray-800 flex items-center justify-center text-gray-600 hover:text-gray-400 hover:border-gray-700 transition-colors text-xs"
                  aria-label={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>

            {/* Links */}
            <ul className="space-y-3">
              {links.map((link) => (
                <li key={link}>
                  <a 
                    href="#" 
                    className="text-gray-600 hover:text-gray-400 text-sm transition-colors"
                  >
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-900/50 pt-8 flex flex-wrap justify-between items-center gap-6 text-gray-700 text-sm">
          <p>Copyright 2026</p>
          <div className="flex gap-8">
            <a href="#" className="hover:text-gray-500 transition-colors">Terms & Condition</a>
            <a href="#" className="hover:text-gray-500 transition-colors">Rules</a>
          </div>
        </div>
      </div>
    </footer>
  );
};
