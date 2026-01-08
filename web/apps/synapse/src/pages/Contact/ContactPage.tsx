import { Typography } from "@synapse/ui";
import { Footer } from "../../components/Footer/Footer";
import { Navbar } from "../../components/Navbar/Navbar";
import type { Page } from "../types/Page";
import { useState } from "react";

const contactMethods = [
  {
    icon: "📧",
    title: "Email",
    value: "hello@synapse.ai",
    description: "Send us an email anytime",
  },
  {
    icon: "💬",
    title: "Live Chat",
    value: "Available 24/7",
    description: "Get instant support",
  },
  {
    icon: "📞",
    title: "Phone",
    value: "+1 (555) 123-4567",
    description: "Mon-Fri, 9am-6pm EST",
  },
  {
    icon: "🏢",
    title: "Office",
    value: "San Francisco, CA",
    description: "Schedule a visit",
  },
];

const departments = [
  {
    name: "Sales",
    email: "sales@synapse.ai",
    description: "Product demos, pricing, and enterprise inquiries",
  },
  {
    name: "Support",
    email: "support@synapse.ai",
    description: "Technical support and troubleshooting",
  },
  {
    name: "Partnerships",
    email: "partnerships@synapse.ai",
    description: "Integration partnerships and collaborations",
  },
  {
    name: "Press & Media",
    email: "press@synapse.ai",
    description: "Media inquiries and press releases",
  },
];

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
    <div className="min-h-screen bg-neutral-surface-emphasis">
      <Navbar />

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-black to-neutral-surface-emphasis py-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <Typography
            variant="display"
            size="large"
            className="mb-6 text-white"
          >
            Get in Touch
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle max-w-3xl mx-auto"
          >
            Have questions? We'd love to hear from you. Send us a message and
            we'll respond as soon as possible.
          </Typography>
        </div>
      </section>

      {/* Contact Methods */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {contactMethods.map((method, index) => (
              <div
                key={index}
                className="p-6 bg-neutral-surface-emphasis rounded-xl border border-neutral-border text-center hover:border-accent-orange hover:shadow-lg transition-all"
              >
                <div className="text-4xl mb-3">{method.icon}</div>
                <Typography
                  variant="headline"
                  size="small"
                  className="mb-1 text-primary-content"
                >
                  {method.title}
                </Typography>
                <Typography
                  variant="label"
                  className="text-accent-orange mb-2"
                >
                  {method.value}
                </Typography>
                <Typography className="text-neutral-content-subtle text-sm">
                  {method.description}
                </Typography>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Form & Departments */}
      <section className="py-20 bg-neutral-surface-emphasis">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Contact Form */}
            <div className="lg:col-span-2">
              <div className="bg-neutral-surface rounded-2xl border border-neutral-border p-8">
                <Typography
                  variant="headline"
                  size="large"
                  className="mb-6 text-primary-content"
                >
                  Send us a Message
                </Typography>

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-primary-content font-medium mb-2">
                        Name *
                      </label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="w-full px-4 py-3 bg-neutral-surface-emphasis border border-neutral-border rounded-lg text-primary-content focus:outline-none focus:border-accent-orange transition-colors"
                        placeholder="John Doe"
                      />
                    </div>
                    <div>
                      <label className="block text-primary-content font-medium mb-2">
                        Email *
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        className="w-full px-4 py-3 bg-neutral-surface-emphasis border border-neutral-border rounded-lg text-primary-content focus:outline-none focus:border-accent-orange transition-colors"
                        placeholder="john@company.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-primary-content font-medium mb-2">
                      Company
                    </label>
                    <input
                      type="text"
                      name="company"
                      value={formData.company}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-neutral-surface-emphasis border border-neutral-border rounded-lg text-primary-content focus:outline-none focus:border-accent-orange transition-colors"
                      placeholder="Company Name"
                    />
                  </div>

                  <div>
                    <label className="block text-primary-content font-medium mb-2">
                      Subject *
                    </label>
                    <select
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-neutral-surface-emphasis border border-neutral-border rounded-lg text-primary-content focus:outline-none focus:border-accent-orange transition-colors"
                    >
                      <option value="">Select a subject</option>
                      <option value="sales">Sales Inquiry</option>
                      <option value="support">Technical Support</option>
                      <option value="partnership">Partnership</option>
                      <option value="feedback">Feedback</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-primary-content font-medium mb-2">
                      Message *
                    </label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      required
                      rows={6}
                      className="w-full px-4 py-3 bg-neutral-surface-emphasis border border-neutral-border rounded-lg text-primary-content focus:outline-none focus:border-accent-orange transition-colors resize-none"
                      placeholder="Tell us how we can help..."
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full px-8 py-3 bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white rounded-lg font-medium hover:shadow-lg hover:scale-[1.02] transition-all"
                  >
                    Send Message
                  </button>
                </form>
              </div>
            </div>

            {/* Departments */}
            <div className="space-y-6">
              <div className="bg-neutral-surface rounded-2xl border border-neutral-border p-8">
                <Typography
                  variant="headline"
                  size="medium"
                  className="mb-6 text-primary-content"
                >
                  Departments
                </Typography>

                <div className="space-y-6">
                  {departments.map((dept, index) => (
                    <div key={index} className="pb-6 border-b border-neutral-border last:border-0 last:pb-0">
                      <Typography
                        variant="headline"
                        size="small"
                        className="mb-1 text-primary-content"
                      >
                        {dept.name}
                      </Typography>
                      <a
                        href={`mailto:${dept.email}`}
                        className="text-accent-orange hover:underline text-sm block mb-2"
                      >
                        {dept.email}
                      </a>
                      <Typography className="text-neutral-content-subtle text-sm">
                        {dept.description}
                      </Typography>
                    </div>
                  ))}
                </div>
              </div>

              {/* Office Location */}
              <div className="bg-gradient-to-br from-accent-peach/20 via-accent-orange/20 to-accent-grape/20 rounded-2xl border border-accent-orange/30 p-8">
                <div className="text-4xl mb-4">📍</div>
                <Typography
                  variant="headline"
                  size="medium"
                  className="mb-3 text-primary-content"
                >
                  Visit Our Office
                </Typography>
                <Typography className="text-neutral-content mb-2">
                  123 Innovation Drive
                  <br />
                  San Francisco, CA 94105
                  <br />
                  United States
                </Typography>
                <Typography className="text-neutral-content-subtle text-sm">
                  Visits by appointment only
                </Typography>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-12">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Frequently Asked Questions
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle"
            >
              Quick answers to common questions
            </Typography>
          </div>

          <div className="space-y-4">
            <div className="bg-neutral-surface-emphasis rounded-xl border border-neutral-border p-6">
              <Typography
                variant="headline"
                size="small"
                className="mb-2 text-primary-content"
              >
                What's your response time?
              </Typography>
              <Typography className="text-neutral-content-subtle">
                We typically respond to all inquiries within 24 hours on business
                days. Enterprise customers with SLA agreements receive priority
                support with faster response times.
              </Typography>
            </div>

            <div className="bg-neutral-surface-emphasis rounded-xl border border-neutral-border p-6">
              <Typography
                variant="headline"
                size="small"
                className="mb-2 text-primary-content"
              >
                Do you offer phone support?
              </Typography>
              <Typography className="text-neutral-content-subtle">
                Phone support is available for Professional and Enterprise plan
                customers. Contact your account manager for phone support access.
              </Typography>
            </div>

            <div className="bg-neutral-surface-emphasis rounded-xl border border-neutral-border p-6">
              <Typography
                variant="headline"
                size="small"
                className="mb-2 text-primary-content"
              >
                Can I schedule a demo?
              </Typography>
              <Typography className="text-neutral-content-subtle">
                Absolutely! Select "Sales Inquiry" in the contact form above, and
                our team will reach out to schedule a personalized demo at your
                convenience.
              </Typography>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

ContactPage.title = "Contact Us";
ContactPage.path = "/contact";
ContactPage.exact = true;

