import { Typography } from "@synapse/ui";
import { Footer } from "../../components/Footer/Footer";
import { Navbar } from "../../components/Navbar/Navbar";
import type { Page } from "../types/Page";

const securityFeatures = [
  {
    icon: "🔐",
    title: "End-to-End Encryption",
    description:
      "All data is encrypted in transit using TLS 1.3 and at rest using AES-256 encryption.",
  },
  {
    icon: "🔑",
    title: "SSO & SAML 2.0",
    description:
      "Enterprise single sign-on with support for SAML 2.0, OAuth 2.0, and LDAP integration.",
  },
  {
    icon: "👥",
    title: "Role-Based Access Control",
    description:
      "Granular permissions and role management to control who can access and modify data.",
  },
  {
    icon: "📊",
    title: "Audit Logging",
    description:
      "Comprehensive audit trails tracking all user actions and data modifications.",
  },
  {
    icon: "🏢",
    title: "Private Cloud Deployment",
    description:
      "Deploy on your own infrastructure with on-premise or private cloud options.",
  },
  {
    icon: "🛡️",
    title: "Data Residency",
    description:
      "Choose where your data is stored with regional data center options.",
  },
];

const certifications = [
  {
    badge: "✓",
    name: "SOC 2 Type II",
    description: "Certified for security, availability, and confidentiality",
  },
  {
    badge: "✓",
    name: "ISO 27001",
    description: "Information security management system certified",
  },
  {
    badge: "✓",
    name: "GDPR Compliant",
    description: "Full compliance with European data protection regulations",
  },
  {
    badge: "✓",
    name: "HIPAA Ready",
    description: "Healthcare data security and privacy compliance",
  },
  {
    badge: "✓",
    name: "CCPA Compliant",
    description: "California Consumer Privacy Act compliant",
  },
  {
    badge: "✓",
    name: "PCI DSS",
    description: "Payment card industry data security standard",
  },
];

const securityPractices = [
  {
    title: "Regular Security Audits",
    items: [
      "Quarterly penetration testing by third-party security firms",
      "Continuous vulnerability scanning and assessment",
      "Annual compliance audits and certifications",
      "Bug bounty program with responsible disclosure policy",
    ],
  },
  {
    title: "Data Protection",
    items: [
      "Automatic daily backups with point-in-time recovery",
      "Data anonymization and pseudonymization options",
      "Secure data deletion and right to be forgotten",
      "Data export capabilities in multiple formats",
    ],
  },
  {
    title: "Infrastructure Security",
    items: [
      "Multi-factor authentication (MFA) for all accounts",
      "Network segmentation and firewall protection",
      "DDoS protection and rate limiting",
      "24/7 security monitoring and incident response",
    ],
  },
  {
    title: "Compliance & Privacy",
    items: [
      "Privacy by design principles in all features",
      "Data processing agreements (DPA) available",
      "Regular staff security training and awareness",
      "Transparent security policies and documentation",
    ],
  },
];

export const SecurityPage: Page = () => {
  return (
    <div className="min-h-screen bg-neutral-surface-emphasis">
      <Navbar />

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-black to-neutral-surface-emphasis py-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-accent-peach via-accent-orange to-accent-grape rounded-full mb-6">
            <span className="text-4xl">🔒</span>
          </div>
          <Typography
            variant="display"
            size="large"
            className="mb-6 text-white"
          >
            Security & Compliance
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle max-w-3xl mx-auto"
          >
            Your data security is our top priority. We implement industry-leading
            security measures and maintain strict compliance standards to protect
            your sensitive information.
          </Typography>
        </div>
      </section>

      {/* Security Features */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Enterprise-Grade Security
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              Comprehensive security features to keep your data safe
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {securityFeatures.map((feature, index) => (
              <div
                key={index}
                className="p-8 bg-neutral-surface-emphasis rounded-2xl border border-neutral-border hover:border-accent-orange hover:shadow-lg transition-all"
              >
                <div className="text-5xl mb-4">{feature.icon}</div>
                <Typography
                  variant="headline"
                  size="medium"
                  className="mb-3 text-primary-content"
                >
                  {feature.title}
                </Typography>
                <Typography className="text-neutral-content-subtle">
                  {feature.description}
                </Typography>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Certifications */}
      <section className="py-20 bg-neutral-surface-emphasis">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Certifications & Compliance
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              Independently verified security and compliance standards
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {certifications.map((cert, index) => (
              <div
                key={index}
                className="p-6 bg-neutral-surface rounded-xl border border-neutral-border flex items-start gap-4"
              >
                <div className="flex-shrink-0 w-10 h-10 bg-positive-surface rounded-full flex items-center justify-center">
                  <span className="text-positive-content font-bold text-xl">
                    {cert.badge}
                  </span>
                </div>
                <div>
                  <Typography
                    variant="headline"
                    size="small"
                    className="mb-1 text-primary-content"
                  >
                    {cert.name}
                  </Typography>
                  <Typography className="text-neutral-content-subtle text-sm">
                    {cert.description}
                  </Typography>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security Practices */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Our Security Practices
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              Comprehensive measures to protect your data
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {securityPractices.map((practice, index) => (
              <div
                key={index}
                className="p-8 bg-neutral-surface-emphasis rounded-2xl border border-neutral-border"
              >
                <Typography
                  variant="headline"
                  size="medium"
                  className="mb-4 text-primary-content"
                >
                  {practice.title}
                </Typography>
                <ul className="space-y-3">
                  {practice.items.map((item, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-neutral-content"
                    >
                      <span className="text-positive-content mt-1">✓</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Report Vulnerability */}
      <section className="py-20 bg-neutral-surface-emphasis">
        <div className="max-w-4xl mx-auto px-6">
          <div className="bg-gradient-to-br from-accent-peach/20 via-accent-orange/20 to-accent-grape/20 rounded-3xl p-12 border border-accent-orange/30 text-center">
            <div className="text-5xl mb-6">🛡️</div>
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Security Vulnerability Disclosure
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle mb-8 max-w-2xl mx-auto"
            >
              If you've discovered a security vulnerability, please report it
              responsibly through our bug bounty program. We take all reports
              seriously and respond promptly.
            </Typography>
            <button
              onClick={() => (window.location.href = "/contact")}
              className="px-8 py-3 bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white rounded-lg font-medium hover:shadow-lg hover:scale-105 transition-all"
            >
              Report a Vulnerability
            </button>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <Typography
            variant="headline"
            size="large"
            className="mb-4 text-primary-content"
          >
            Questions About Security?
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle mb-8 max-w-2xl mx-auto"
          >
            Our security team is here to answer your questions and provide
            detailed information about our security practices.
          </Typography>
          <button
            onClick={() => (window.location.href = "/contact")}
            className="px-8 py-3 bg-neutral-surface-subtle border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            Contact Security Team
          </button>
        </div>
      </section>

      <Footer />
    </div>
  );
};

SecurityPage.title = "Security & Compliance";
SecurityPage.path = "/security";
SecurityPage.exact = true;

