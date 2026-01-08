import { Typography } from "@synapse/ui";
import { Footer } from "../../components/Footer/Footer";
import { Navbar } from "../../components/Navbar/Navbar";
import type { Page } from "../types/Page";

const teamMembers = [
  {
    name: "Sarah Chen",
    role: "CEO & Co-Founder",
    image: "👩‍💼",
    bio: "Former ML engineer at Google. Passionate about making AI accessible.",
  },
  {
    name: "Michael Rodriguez",
    role: "CTO & Co-Founder",
    image: "👨‍💻",
    bio: "PhD in Computer Vision. Built annotation systems at Tesla.",
  },
  {
    name: "Emily Watson",
    role: "Head of Product",
    image: "👩‍🔬",
    bio: "10+ years in enterprise software. Previously at Salesforce.",
  },
  {
    name: "David Kim",
    role: "VP Engineering",
    image: "👨‍🔧",
    bio: "Scaled platforms at Uber. Expert in distributed systems.",
  },
];

const milestones = [
  {
    year: "2020",
    title: "Company Founded",
    description: "Started with a vision to democratize data labeling for AI teams.",
  },
  {
    year: "2021",
    title: "Series A Funding",
    description: "Raised $10M to expand our platform and team.",
  },
  {
    year: "2022",
    title: "1000+ Customers",
    description: "Reached milestone of serving over 1000 organizations worldwide.",
  },
  {
    year: "2023",
    title: "Enterprise Launch",
    description: "Launched enterprise features with advanced security and compliance.",
  },
  {
    year: "2024",
    title: "Global Expansion",
    description: "Opened offices in Europe and Asia to serve customers globally.",
  },
];

const values = [
  {
    icon: "🎯",
    title: "Customer First",
    description:
      "We prioritize our customers' success and build features that solve real problems.",
  },
  {
    icon: "🚀",
    title: "Innovation",
    description:
      "We constantly push boundaries to create cutting-edge annotation tools.",
  },
  {
    icon: "🤝",
    title: "Collaboration",
    description:
      "We believe in the power of teamwork and open communication.",
  },
  {
    icon: "🔒",
    title: "Trust & Security",
    description:
      "We maintain the highest standards of data security and privacy.",
  },
  {
    icon: "🌍",
    title: "Global Impact",
    description:
      "We're building tools that help create AI systems that benefit humanity.",
  },
  {
    icon: "💡",
    title: "Continuous Learning",
    description:
      "We foster a culture of growth and learning from our experiences.",
  },
];

export const AboutPage: Page = () => {
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
            About Synapse
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle max-w-3xl mx-auto"
          >
            We're on a mission to empower teams to build better AI models through
            high-quality data annotation and intelligent workflows.
          </Typography>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Our Mission
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle leading-relaxed"
            >
              At Synapse, we believe that high-quality training data is the
              foundation of successful AI systems. Our mission is to provide the
              most powerful, flexible, and user-friendly data annotation platform
              that enables teams of all sizes to label data efficiently and
              accurately. We're committed to accelerating AI development by making
              data labeling accessible, collaborative, and intelligent.
            </Typography>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-neutral-surface-emphasis">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Our Values
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              The principles that guide everything we do
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {values.map((value, index) => (
              <div
                key={index}
                className="p-6 bg-neutral-surface rounded-xl border border-neutral-border hover:border-accent-orange hover:shadow-lg transition-all"
              >
                <div className="text-4xl mb-4">{value.icon}</div>
                <Typography
                  variant="headline"
                  size="small"
                  className="mb-2 text-primary-content"
                >
                  {value.title}
                </Typography>
                <Typography className="text-neutral-content-subtle">
                  {value.description}
                </Typography>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 bg-neutral-surface">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Meet Our Team
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              Experienced leaders passionate about AI and data quality
            </Typography>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {teamMembers.map((member, index) => (
              <div
                key={index}
                className="text-center p-6 bg-neutral-surface-emphasis rounded-xl border border-neutral-border hover:border-accent-orange hover:shadow-lg transition-all"
              >
                <div className="text-6xl mb-4">{member.image}</div>
                <Typography
                  variant="headline"
                  size="small"
                  className="mb-1 text-primary-content"
                >
                  {member.name}
                </Typography>
                <Typography
                  variant="label"
                  className="text-accent-orange mb-3"
                >
                  {member.role}
                </Typography>
                <Typography className="text-neutral-content-subtle text-sm">
                  {member.bio}
                </Typography>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-20 bg-neutral-surface-emphasis">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <Typography
              variant="headline"
              size="large"
              className="mb-4 text-primary-content"
            >
              Our Journey
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle max-w-2xl mx-auto"
            >
              Key milestones in our company's growth
            </Typography>
          </div>

          <div className="space-y-8">
            {milestones.map((milestone, index) => (
              <div
                key={index}
                className="flex gap-6 items-start p-6 bg-neutral-surface rounded-xl border border-neutral-border"
              >
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 bg-gradient-to-br from-accent-peach via-accent-orange to-accent-grape rounded-full flex items-center justify-center">
                    <Typography
                      variant="headline"
                      size="small"
                      className="text-white font-bold"
                    >
                      {milestone.year}
                    </Typography>
                  </div>
                </div>
                <div className="flex-1">
                  <Typography
                    variant="headline"
                    size="medium"
                    className="mb-2 text-primary-content"
                  >
                    {milestone.title}
                  </Typography>
                  <Typography className="text-neutral-content-subtle">
                    {milestone.description}
                  </Typography>
                </div>
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
              Join Our Mission
            </Typography>
            <Typography
              size="large"
              className="text-neutral-content-subtle mb-8 max-w-2xl mx-auto"
            >
              We're always looking for talented individuals who are passionate
              about AI and data quality.
            </Typography>
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                onClick={() => (window.location.href = "/careers")}
                className="px-8 py-3 bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white rounded-lg font-medium hover:shadow-lg hover:scale-105 transition-all"
              >
                View Open Positions
              </button>
              <button
                onClick={() => (window.location.href = "/contact")}
                className="px-8 py-3 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
              >
                Get in Touch
              </button>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

AboutPage.title = "About Us";
AboutPage.path = "/about";
AboutPage.exact = true;

