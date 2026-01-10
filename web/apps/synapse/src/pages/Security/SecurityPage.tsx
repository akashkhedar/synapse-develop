import { motion } from "framer-motion";
import { Footer } from "../Landing/components/Footer";
import { Navigation } from "../Landing/components/Navigation";
import type { Page } from "../types/Page";

const SmoothSection: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className={className}
    >
      {children}
    </motion.section>
  );
};

const commitments = [
  {
    number: "01",
    title: "Protect Our Customers' Data",
    description: "We are dedicated to safeguarding the data and integrity of our customers' critical work. Our security program is designed to protect customer assets and proactively reduce the frequency of negative security events."
  },
  {
    number: "02",
    title: "Secure Our Foundation",
    description: "We treat security as foundational, integrating it deeply into our company culture and product development lifecycle."
  },
  {
    number: "03",
    title: "Protect Our Shared Future",
    description: "As leaders in AI data infrastructure, we actively partner with government, industry, and the research community to define and elevate standards for secure and responsible AI."
  }
];

const certifications = [
  {
    name: "SOC 2 Type II",
    description: "Demonstrating commitment to protecting customer data through security, availability, and confidentiality controls that align with AICPA Trust Services Criteria."
  },
  {
    name: "ISO 27001",
    description: "Information security management system certified, ensuring systematic approach to managing sensitive company information."
  },
  {
    name: "GDPR Compliant",
    description: "Full compliance with European data protection regulations, ensuring privacy and data protection for EU citizens."
  },
  {
    name: "HIPAA Ready",
    description: "Healthcare data security and privacy compliance for handling protected health information."
  }
];

const securityPractices = [
  {
    category: "Data Protection",
    items: [
      "End-to-end encryption using TLS 1.3 in transit and AES-256 at rest",
      "Automatic daily backups with point-in-time recovery",
      "Data anonymization and pseudonymization options",
      "Secure data deletion and right to be forgotten"
    ]
  },
  {
    category: "Access Control",
    items: [
      "Role-based access control (RBAC) with granular permissions",
      "Single sign-on (SSO) with SAML 2.0 and OAuth 2.0",
      "Multi-factor authentication (MFA) for all accounts",
      "Comprehensive audit logging of all user actions"
    ]
  },
  {
    category: "Infrastructure Security",
    items: [
      "Network segmentation and firewall protection",
      "DDoS protection and rate limiting",
      "24/7 security monitoring and incident response",
      "Regular penetration testing by third-party firms"
    ]
  },
  {
    category: "Compliance & Auditing",
    items: [
      "Quarterly security audits and assessments",
      "Annual compliance certifications",
      "Bug bounty program with responsible disclosure",
      "Privacy by design in all product features"
    ]
  }
];

export const SecurityPage: Page = () => {
  return (
    <div className="bg-black min-h-screen">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative min-h-[60vh] flex items-center justify-center overflow-hidden pt-32 pb-20">
        <div className="absolute inset-0 opacity-[0.03]">
          <div 
            className="w-full h-full"
            style={{
              backgroundImage: `
                linear-gradient(to right, #ffffff 1px, transparent 1px),
                linear-gradient(to bottom, #ffffff 1px, transparent 1px)
              `,
              backgroundSize: '60px 60px'
            }}
          />
        </div>

        <div className="max-w-5xl mx-auto px-6 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6"
          >
            <span className="text-gray-500 font-mono text-sm tracking-wider uppercase">
              // Security at Synapse
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 leading-tight"
          >
            Trust through
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              security and compliance
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto font-mono"
          >
            At Synapse, our customers trust us to develop reliable systems for their most
            important applications. We take the security of their data seriously, embedding
            it into our platform at every level.
          </motion.p>
        </div>
      </section>

      {/* Commitment Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-white mb-16"
          >
            Our Commitment
          </motion.h2>

          <div className="space-y-12">
            {commitments.map((commitment, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="border-l-2 border-gray-800 pl-8 hover:border-purple-500 transition-colors"
              >
                <div className="text-gray-500 font-mono text-sm mb-2">{commitment.number}/</div>
                <h3 className="text-2xl font-bold text-white mb-3">{commitment.title}</h3>
                <p className="text-gray-400 font-mono leading-relaxed">{commitment.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* Certifications Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Certifications & Compliance
            </h2>
            <p className="text-gray-400 font-mono text-lg">
              Independently verified security and compliance standards
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            {certifications.map((cert, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="border border-gray-800 bg-black/50 p-8 hover:border-gray-700 transition-colors"
              >
                <h3 className="text-xl font-bold text-white mb-3">{cert.name}</h3>
                <p className="text-gray-400 font-mono text-sm leading-relaxed">
                  {cert.description}
                </p>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mt-12 text-center"
          >
            <p className="text-gray-500 font-mono text-sm">
              To access our latest security compliance certifications and reports,
              please contact our security team.
            </p>
          </motion.div>
        </div>
      </SmoothSection>

      {/* Security Practices Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              How we protect ourselves and our customers
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-12">
            {securityPractices.map((practice, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <h3 className="text-xl font-bold text-white mb-6 border-l-2 border-purple-500 pl-4">
                  {practice.category}
                </h3>
                <ul className="space-y-4">
                  {practice.items.map((item, i) => (
                    <li
                      key={i}
                      className="text-gray-400 font-mono text-sm leading-relaxed relative before:content-['—'] before:absolute before:-left-6 before:text-gray-600 pl-6"
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* Vulnerability Disclosure Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Need to report a vulnerability?
            </h2>
            <p className="text-gray-400 font-mono text-lg mb-8">
              Get in touch with our vulnerability disclosure team
            </p>
            <motion.a
              href="mailto:security@synapse.ai"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="inline-block bg-white text-black px-10 py-4 text-base font-semibold transition-all"
            >
              security@synapse.ai →
            </motion.a>
          </motion.div>
        </div>
      </SmoothSection>

      <Footer />
    </div>
  );
};

SecurityPage.title = "Security";
SecurityPage.path = "/security";
SecurityPage.exact = true;

