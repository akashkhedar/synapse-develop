import { Footer } from "../Landing/components/Footer";
import { Navigation } from "../Landing/components/Navigation";
import type { Page } from "../types/Page";
import { useState } from "react";
import { motion } from "framer-motion";

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

export const ContactPage: Page = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    subject: "",
    message: "",
  });

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement form submission
    alert("Thank you for contacting us! We'll get back to you soon.");
    setFormData({
      name: "",
      email: "",
      company: "",
      subject: "",
      message: "",
    });
  };

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
              // Get in Touch
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 leading-tight"
          >
            Let's start a
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              conversation
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto font-mono"
          >
            Whether you're ready to start a project or just want to learn more,
            we're here to help.
          </motion.p>
        </div>
      </section>

      {/* Contact Info Section */}
      <SmoothSection className="py-20 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-12 mb-20">
            <div className="border-l-2 border-gray-800 pl-6 hover:border-purple-500 transition-colors">
              <div className="text-gray-500 font-mono text-sm mb-2">Email</div>
              <a href="mailto:hello@synapse.ai" className="text-white text-lg hover:text-purple-400 transition-colors">
                hello@synapse.ai
              </a>
            </div>

            <div className="border-l-2 border-gray-800 pl-6 hover:border-purple-500 transition-colors">
              <div className="text-gray-500 font-mono text-sm mb-2">Phone</div>
              <a href="tel:+15551234567" className="text-white text-lg hover:text-purple-400 transition-colors">
                +1 (555) 123-4567
              </a>
            </div>

            <div className="border-l-2 border-gray-800 pl-6 hover:border-purple-500 transition-colors">
              <div className="text-gray-500 font-mono text-sm mb-2">Location</div>
              <div className="text-white text-lg">
                San Francisco, CA
              </div>
            </div>
          </div>
        </div>
      </SmoothSection>

      {/* Main Content Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid lg:grid-cols-3 gap-16">
            {/* Contact Form */}
            <div className="lg:col-span-2">
              <div className="flex items-start gap-4 mb-8">
                <div className="flex flex-col items-start">
                  <div className="w-6 h-[2px] bg-gray-600" />
                  <div className="w-[2px] h-6 bg-gray-600" />
                </div>
                <h2 className="text-4xl md:text-5xl font-bold text-white">Send a Message</h2>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="name" className="block text-gray-400 font-mono text-sm mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      className="w-full px-0 py-3 bg-transparent border-b border-gray-800 text-white font-mono focus:outline-none focus:border-gray-600 transition-colors"
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-gray-400 font-mono text-sm mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full px-0 py-3 bg-transparent border-b border-gray-800 text-white font-mono focus:outline-none focus:border-gray-600 transition-colors"
                      placeholder="john@company.com"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="company" className="block text-gray-400 font-mono text-sm mb-2">
                    Company
                  </label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    value={formData.company}
                    onChange={handleChange}
                    className="w-full px-0 py-3 bg-transparent border-b border-gray-800 text-white font-mono focus:outline-none focus:border-gray-600 transition-colors"
                    placeholder="Your Company"
                  />
                </div>

                <div>
                  <label htmlFor="subject" className="block text-gray-400 font-mono text-sm mb-2">
                    Subject
                  </label>
                  <select
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="w-full px-0 py-3 bg-transparent border-b border-gray-800 text-white font-mono focus:outline-none focus:border-gray-600 transition-colors"
                  >
                    <option value="" className="bg-black">Select...</option>
                    <option value="sales" className="bg-black">Sales Inquiry</option>
                    <option value="support" className="bg-black">Technical Support</option>
                    <option value="partnership" className="bg-black">Partnership</option>
                    <option value="other" className="bg-black">Other</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="message" className="block text-gray-400 font-mono text-sm mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="w-full px-0 py-3 bg-transparent border-b border-gray-800 text-white font-mono focus:outline-none focus:border-gray-600 transition-colors resize-none"
                    placeholder="Tell us about your project..."
                  />
                </div>

                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="bg-white text-black px-10 py-4 text-base font-semibold transition-all mt-4"
                >
                  Send Message →
                </motion.button>
              </form>
            </div>

            {/* Contact Details Sidebar */}
            <div>
              <h3 className="text-2xl font-bold text-white mb-8">Departments</h3>
              
              <div className="space-y-8">
                <div className="border-l-2 border-gray-800 pl-6 hover:border-purple-500 transition-colors">
                  <div className="text-gray-500 font-mono text-sm mb-2">Sales</div>
                  <a href="mailto:sales@synapse.ai" className="text-white text-sm hover:text-purple-400 transition-colors block mb-2">
                    sales@synapse.ai
                  </a>
                  <p className="text-gray-500 font-mono text-xs">
                    Product demos and pricing
                  </p>
                </div>

                <div className="border-l-2 border-gray-800 pl-6 hover:border-purple-500 transition-colors">
                  <div className="text-gray-500 font-mono text-sm mb-2">Support</div>
                  <a href="mailto:support@synapse.ai" className="text-white text-sm hover:text-purple-400 transition-colors block mb-2">
                    support@synapse.ai
                  </a>
                  <p className="text-gray-500 font-mono text-xs">
                    Technical assistance
                  </p>
                </div>

                <div className="border-l-2 border-gray-800 pl-6 hover:border-purple-500 transition-colors">
                  <div className="text-gray-500 font-mono text-sm mb-2">Partnerships</div>
                  <a href="mailto:partnerships@synapse.ai" className="text-white text-sm hover:text-purple-400 transition-colors block mb-2">
                    partnerships@synapse.ai
                  </a>
                  <p className="text-gray-500 font-mono text-xs">
                    Integration opportunities
                  </p>
                </div>
              </div>

              <div className="mt-12 pt-12 border-t border-gray-900">
                <div className="text-gray-500 font-mono text-sm mb-4">Office</div>
                <p className="text-gray-400 font-mono text-sm leading-relaxed">
                  123 Innovation Drive<br />
                  San Francisco, CA 94105<br />
                  United States
                </p>
              </div>
            </div>
          </div>
        </div>
      </SmoothSection>

      {/* Response Time Section */}
      <SmoothSection className="py-20 bg-black border-t border-gray-900">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-gray-500 font-mono text-sm mb-4">
            // Response Time
          </p>
          <p className="text-white text-xl font-mono leading-relaxed">
            We typically respond within 24 hours on business days.
            <br />
            Enterprise customers receive priority support.
          </p>
        </div>
      </SmoothSection>

      <Footer />
    </div>
  );
};

ContactPage.title = "Contact Us";
ContactPage.path = "/contact";
ContactPage.exact = true;

