import { Typography } from "@synapse/ui";

const testimonials = [
  {
    quote:
      "Synapse has transformed how we label data for our computer vision models. The collaborative features are game-changing.",
    author: "Sarah Chen",
    role: "ML Engineer",
    company: "TechVision AI",
    avatar: "👩‍💻",
  },
  {
    quote:
      "We moved from a commercial solution to Synapse and never looked back. It's more flexible and the open-source community is amazing.",
    author: "Marcus Johnson",
    role: "Data Scientist",
    company: "DataCorp",
    avatar: "👨‍🔬",
  },
  {
    quote:
      "The ability to integrate our custom ML models for pre-annotations saved us hundreds of hours. Incredible productivity boost.",
    author: "Priya Patel",
    role: "AI Team Lead",
    company: "Neural Systems",
    avatar: "👩‍🚀",
  },
];

export const Testimonials = () => {
  return (
    <section className="py-20 bg-neutral-surface-emphasis">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <Typography
            variant="headline"
            size="large"
            className="mb-4 text-primary-content"
          >
            Trusted by AI Teams Worldwide
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle max-w-2xl mx-auto"
          >
            Join thousands of data scientists and ML engineers building better
            models with Synapse.
          </Typography>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="p-6 bg-neutral-surface rounded-xl border border-neutral-border hover:border-accent-peach hover:shadow-lg transition-all"
            >
              <Typography className="text-neutral-content mb-6 leading-relaxed italic">
                "{testimonial.quote}"
              </Typography>
              <div className="flex items-center gap-3">
                <div className="text-3xl">{testimonial.avatar}</div>
                <div>
                  <Typography
                    variant="headline"
                    size="small"
                    className="text-primary-content"
                  >
                    {testimonial.author}
                  </Typography>
                  <Typography className="text-sm text-neutral-content-subtle">
                    {testimonial.role} • {testimonial.company}
                  </Typography>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Stats Bar */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Countries", value: "150+" },
            { label: "Projects", value: "1M+" },
            { label: "Annotations", value: "10B+" },
            { label: "Uptime", value: "99.9%" },
          ].map((stat, index) => (
            <div
              key={index}
              className="text-center p-6 bg-neutral-surface rounded-lg border border-neutral-border"
            >
              <Typography
                variant="headline"
                size="large"
                className="text-accent-orange mb-1"
              >
                {stat.value}
              </Typography>
              <Typography className="text-neutral-content-subtle">
                {stat.label}
              </Typography>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

