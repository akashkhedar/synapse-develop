import { Typography } from "@synapse/ui";
import { Footer } from "../../components/Footer/Footer";
import type { Page } from "../types/Page";

const services = [
  {
    icon: "🎯",
    title: "Data Annotation",
    description:
      "Professional annotation services for images, text, audio, and video. Our expert annotators ensure high-quality labeled data for your ML projects.",
    features: [
      "Multi-format support (images, text, audio, video)",
      "Quality assurance & validation",
      "Custom annotation workflows",
      "Fast turnaround times",
    ],
  },
  {
    icon: "🤖",
    title: "AI Model Training",
    description:
      "End-to-end machine learning solutions from data preparation to model deployment. We help you build, train, and optimize your AI models.",
    features: [
      "Custom model development",
      "Transfer learning & fine-tuning",
      "Model evaluation & optimization",
      "Production deployment support",
    ],
  },
  {
    icon: "🔍",
    title: "Data Quality Assurance",
    description:
      "Comprehensive quality control processes to ensure your training data meets the highest standards for accuracy and consistency.",
    features: [
      "Multi-level review process",
      "Inter-annotator agreement analysis",
      "Error detection & correction",
      "Detailed quality reports",
    ],
  },
  {
    icon: "👥",
    title: "Managed Annotation Teams",
    description:
      "Dedicated teams of trained annotators managed by experienced project managers to handle your large-scale annotation projects.",
    features: [
      "Scalable workforce",
      "Domain expert annotators",
      "Project management & coordination",
      "Regular progress updates",
    ],
  },
  {
    icon: "🔄",
    title: "Active Learning Pipelines",
    description:
      "Implement efficient active learning workflows to reduce annotation costs while maximizing model performance with smart data selection.",
    features: [
      "Automated data selection",
      "Model-in-the-loop workflows",
      "Continuous improvement cycles",
      "Cost optimization strategies",
    ],
  },
  {
    icon: "🛠️",
    title: "Custom Solutions",
    description:
      "Tailored annotation solutions designed for your specific use case, industry, and data requirements with full technical support.",
    features: [
      "Custom labeling interfaces",
      "Industry-specific workflows",
      "API & integration support",
      "Dedicated technical support",
    ],
  },
];

const pricingPlans = [
  {
    name: "Starter",
    price: "$99",
    period: "/month",
    description: "Perfect for small projects and individual researchers",
    features: [
      "Up to 10,000 annotations/month",
      "Basic annotation tools",
      "Email support",
      "5 GB storage",
      "Single user",
    ],
  },
  {
    name: "Professional",
    price: "$499",
    period: "/month",
    description: "For growing teams and production workflows",
    features: [
      "Up to 100,000 annotations/month",
      "Advanced annotation tools",
      "Priority support",
      "50 GB storage",
      "Up to 10 users",
      "API access",
      "Custom workflows",
    ],
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For large-scale operations and custom requirements",
    features: [
      "Unlimited annotations",
      "All annotation tools",
      "24/7 dedicated support",
      "Unlimited storage",
      "Unlimited users",
      "Full API access",
      "Custom integrations",
      "SLA guarantee",
    ],
  },
];

export const ServicesPage: Page = () => {
  return (
    <div className="min-h-screen bg-neutral-surface-emphasis">

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-black to-neutral-surface-emphasis py-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <Typography
            variant="display"
            size="large"
            className="mb-6 text-white"
          >
            Our Services
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle max-w-3xl mx-auto mb-8"
          >
            Comprehensive data annotation and AI solutions to power your machine
            learning projects. From expert annotation teams to custom AI
            pipelines, we've got you covered.
          </Typography>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => (window.location.href = "/contact")}
              className="px-8 py-3 bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white rounded-lg font-medium hover:shadow-lg hover:scale-105 transition-all"
            >
              Get Started
            </button>
            <button
              onClick={() => (window.location.href = "/contact")}
              className="px-8 py-3 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
            >
              Talk to Sales
            </button>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              What We Offer
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              End-to-end solutions for your data labeling and AI needs
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <div
                key={index}
                className="group p-8 bg-neutral-surface-emphasis rounded-2xl border border-neutral-border hover:border-accent-orange hover:shadow-xl transition-all"
              >
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">
                  {service.icon}
                </div>
                <Typography
                  variant="headline"
                  size="medium"
                  className="mb-3 text-primary-content"
                >
                  {service.title}
                </Typography>
                <Typography className="text-neutral-content-subtle mb-4">
                  {service.description}
                </Typography>
                <ul className="space-y-2">
                  {service.features.map((feature, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-neutral-content text-sm"
                    >
                      <span className="text-positive-content mt-0.5">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 bg-neutral-surface-emphasis">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Simple, Transparent Pricing
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              Choose the plan that fits your needs. All plans include core features.
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {pricingPlans.map((plan, index) => (
              <div
                key={index}
                className={`p-8 rounded-2xl border ${
                  plan.featured
                    ? "bg-gradient-to-br from-accent-peach/10 via-accent-orange/10 to-accent-grape/10 border-accent-orange shadow-xl scale-105"
                    : "bg-neutral-surface border-neutral-border"
                }`}
              >
                {plan.featured && (
                  <div className="inline-block px-3 py-1 bg-gradient-to-r from-accent-peach to-accent-orange text-white text-sm font-medium rounded-full mb-4">
                    Most Popular
                  </div>
                )}
                <Typography
                  variant="headline"
                  size="medium"
                  className="mb-2 text-primary-content"
                >
                  {plan.name}
                </Typography>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-primary-content">
                    {plan.price}
                  </span>
                  <span className="text-neutral-content-subtle">
                    {plan.period}
                  </span>
                </div>
                <Typography className="text-neutral-content-subtle mb-6">
                  {plan.description}
                </Typography>
                <button
                  onClick={() => (window.location.href = "/user/signup")}
                  className={`w-full px-6 py-3 rounded-lg font-medium transition-all mb-6 ${
                    plan.featured
                      ? "bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white hover:shadow-lg hover:scale-105"
                      : "bg-neutral-surface-subtle border border-neutral-border text-primary-content hover:bg-neutral-surface-hover"
                  }`}
                >
                  {plan.name === "Enterprise" ? "Contact Sales" : "Get Started"}
                </button>
                <ul className="space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-neutral-content text-sm"
                    >
                      <span className="text-positive-content mt-0.5">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="bg-gradient-to-br from-accent-peach/20 via-accent-orange/20 to-accent-grape/20 rounded-3xl p-12 border border-accent-orange/30">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Ready to Get Started?
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle mb-8 max-w-2xl mx-auto"
            >
              Join thousands of teams using Synapse to build better AI models
              with high-quality labeled data.
            </Typography>
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                onClick={() => (window.location.href = "/user/signup")}
                className="px-8 py-3 bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white rounded-lg font-medium hover:shadow-lg hover:scale-105 transition-all"
              >
                Start Free Trial
              </button>
              <button
                onClick={() => (window.location.href = "/contact")}
                className="px-8 py-3 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
              >
                Schedule Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

ServicesPage.title = "Our Services";
ServicesPage.path = "/services";
ServicesPage.exact = true;

