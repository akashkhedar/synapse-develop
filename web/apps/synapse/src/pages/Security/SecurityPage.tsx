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
    title: "Protect Patient Privacy (PHI)",
    description: "We are dedicated to safeguarding Protected Health Information (PHI). Our security program exceeds HIPAA requirements to ensure patient data remains confidential and secure."
  },
  {
    number: "02",
    title: "Secure Clinical Foundation",
    description: "We treat security as a patient safety issue, integrating strict controls into our annotation workflows and infrastructure."
  },
  {
    number: "03",
    title: "Enable Responsible Medical AI",
    description: "As partners in your clinical trials and research, we uphold the highest ethical standards for data handling in healthcare."
  }
];

const certifications = [
  {
    name: "HIPAA Compliant",
    description: "Fully compliant with Health Insurance Portability and Accountability Act standards for handling PHI."
  },
  {
    name: "SOC 2 Type II",
    description: "Demonstrating commitment to protecting customer data through security, availability, and confidentiality controls."
  },
  {
    name: "ISO 27001",
    description: "Information security management system certified, ensuring systematic approach to managing sensitive company information."
  },
  {
    name: "GDPR Compliant",
    description: "Full compliance with European data protection regulations, ensuring privacy and data protection for EU citizens."
  }
];

const securityPractices = [
  {
    category: "Data Protection",
    items: [
      "End-to-end encryption using TLS 1.3 in transit and AES-256 at rest",
      "Automatic PHI redaction and de-identification pipelines",
      "Strict data isolation between tenants and projects",
      "Secure data deletion and right to be forgotten"
    ]
  },
  {
    category: "Access Control",
    items: [
      "Role-based access control (RBAC) with clinical roles",
      "Single sign-on (SSO) with SAML 2.0 and OAuth 2.0",
      "Multi-factor authentication (MFA) mandatory for all staff",
      "Comprehensive audit logging of all data access"
    ]
  },
  {
    category: "Infrastructure Security",
    items: [
      "Network segmentation and firewall protection",
      "VPC Peering options for enterprise healthcare partners",
      "24/7 security monitoring and incident response",
      "Regular penetration testing by third-party firms"
    ]
  },
  {
    category: "Compliance & Auditing",
    items: [
      "Quarterly HIPAA risk assessments",
      "Annual SOC 2 and ISO compliance audits",
      "BAA (Business Associate Agreement) availability",
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
            HIPAA-Grade Security
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              for Patient Data
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto font-mono"
          >
            We handle sensitive Protected Health Information (PHI) with the highest standards.
            Trust, compliance, and patient privacy are embedded into our platform at every level.
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
      <Footer />
    </div>
  );
};

SecurityPage.title = "Security";
SecurityPage.path = "/security";
SecurityPage.exact = true;

