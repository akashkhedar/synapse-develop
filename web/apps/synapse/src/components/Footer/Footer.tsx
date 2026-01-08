import { Typography } from "@synapse/ui";

const footerLinks = {
  product: [
    { label: "Features", href: "#features" },
    { label: "Documentation", href: "/guide/" },
    { label: "Templates", href: "/templates/" },
    { label: "API Reference", href: "/api/" },
    { label: "Release Notes", href: "/guide/release_notes" },
  ],
  resources: [
    { label: "Blog", href: "https://synapse.io/blog/", external: true },
    { label: "Community", href: "https://slack.synapse.io", external: true },
    {
      label: "GitHub",
      href: "https://github.com/Synapse/synapse",
      external: true,
    },
    { label: "Tutorials", href: "/tutorials/" },
    {
      label: "Video Guides",
      href: "https://youtube.com/@Synapse",
      external: true,
    },
  ],
  company: [
    { label: "About Us", href: "#about" },
    { label: "Careers", href: "#careers" },
    { label: "Contact", href: "#contact" },
    { label: "Partners", href: "#partners" },
  ],
  legal: [
    { label: "Privacy Policy", href: "#privacy" },
    { label: "Terms of Service", href: "#terms" },
    { label: "Cookie Policy", href: "#cookies" },
    {
      label: "License",
      href: "https://github.com/Synapse/synapse/blob/master/LICENSE",
      external: true,
    },
  ],
};

export const Footer = () => {
  return (
    <footer className="bg-neutral-surface-emphasis border-t border-neutral-border">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-12">
          {/* Brand Column */}
          <div className="lg:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-accent-peach via-accent-orange to-accent-grape rounded-sm" />
              <Typography 
                variant="headline"
                size="small"
                className="font-['Nova_Oval'] text-primary-content"
              >
                Synapse
              </Typography>
            </div>
            <Typography className="text-neutral-content-subtle text-sm mb-4">
              Open source data labeling platform for building better AI models.
            </Typography>
            <div className="flex items-center gap-3">
              <a
                href="https://github.com/Synapse/synapse"
                target="_blank"
                rel="noreferrer"
                className="text-neutral-content-subtle hover:text-accent-orange transition-colors"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
              </a>
              <a
                href="https://slack.synapse.io"
                target="_blank"
                rel="noreferrer"
                className="text-neutral-content-subtle hover:text-accent-orange transition-colors"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Links Columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <Typography
                variant="headline"
                size="small"
                className="mb-4 text-primary-content capitalize"
              >
                {category}
              </Typography>
              <ul className="space-y-2">
                {links.map((link, index) => (
                  <li key={index}>
                    <a
                      href={link.href}
                      target={link.external ? "_blank" : undefined}
                      rel={link.external ? "noreferrer" : undefined}
                      className="text-sm text-neutral-content-subtle hover:text-accent-orange transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-neutral-border pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <Typography className="text-sm text-neutral-content-subtler">
            © {new Date().getFullYear()} Synapse. Open source under Apache 2.0
            License.
          </Typography>
          <div className="flex items-center gap-6">
            <a
              href="#"
              className="text-sm text-neutral-content-subtle hover:text-accent-orange transition-colors"
            >
              Status
            </a>
            <a
              href="#"
              className="text-sm text-neutral-content-subtle hover:text-accent-orange transition-colors"
            >
              Security
            </a>
            <a
              href="#"
              className="text-sm text-neutral-content-subtle hover:text-accent-orange transition-colors"
            >
              Changelog
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

