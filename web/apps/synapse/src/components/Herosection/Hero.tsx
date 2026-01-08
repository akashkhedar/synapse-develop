import { IconArrowRight, IconCheck } from "@synapse/icons";
import { Typography } from "@synapse/ui";

export const Hero = () => {
  const handleGetStarted = () => {
    window.location.href = "/user/signup";
  };

  const handleDocs = ()=>{
    window.location.href = "/docs/api"
  }

  return (
    <section className="relative overflow-hidden bg-neutral-surface-emphasis">
      {/* Background gradients */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-accent-peach/10 rounded-full blur-3xl" />
        <div className="absolute top-40 -left-40 w-80 h-80 bg-accent-grape/10 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-20 lg:py-32">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-surface rounded-full mb-6 border border-neutral-border">
            <span className="w-2 h-2 bg-positive-surface rounded-full animate-pulse" />
            <Typography className="text-sm text-neutral-content">
              Open Source • Self-Hosted • Enterprise Ready
            </Typography>
          </div>

          {/* Headline */}
          <Typography
            variant="display"
            size="large"
            className="mb-6 text-primary-content leading-tight"
          >
            Intelligent Data Labeling
            <br />
            <span className="bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape bg-clip-text text-transparent">
              Platform for AI Teams
            </span>
          </Typography>

          {/* Subheadline */}
          <Typography
            size="large"
            className="text-neutral-content-subtle mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            Build better AI models with collaborative annotation tools. Support
            for images, text, audio, video, and time-series data.
          </Typography>

          {/* CTA Buttons */}
          <div className="flex items-center justify-center gap-4 flex-wrap mb-8">
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-accent-peach via-accent-orange to-accent-grape text-white rounded-lg font-medium text-lg hover:shadow-2xl hover:scale-105 transition-all"
            >
              Start Building Free
              <IconArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={handleDocs}
              className="inline-flex items-center gap-2 px-8 py-4 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium text-lg hover:bg-neutral-surface-hover transition-all"
            >
              View Documentation
            </button>
          </div>

          {/* Features List */}
          <div className="flex items-center justify-center gap-6 text-sm text-neutral-content-subtle flex-wrap">
            <span className="flex items-center gap-2">
              <IconCheck className="w-4 h-4 text-positive-content" />
              No Credit Card
            </span>
            <span className="flex items-center gap-2">
              <IconCheck className="w-4 h-4 text-positive-content" />
              Unlimited Projects
            </span>
            <span className="flex items-center gap-2">
              <IconCheck className="w-4 h-4 text-positive-content" />
              Community Support
            </span>
          </div>
        </div>

        {/* Demo Visual */}
        <div className="mt-16 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-accent-peach/20 via-accent-orange/20 to-accent-grape/20 rounded-2xl blur-3xl" />
          <div className="relative bg-neutral-surface rounded-2xl border border-neutral-border shadow-2xl overflow-hidden">
            <div className="aspect-video bg-gradient-to-br from-neutral-surface to-neutral-surface-subtle flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🎯</div>
                <Typography className="text-neutral-content-subtle">
                  Interactive Demo Placeholder
                </Typography>
                <Typography className="text-sm text-neutral-content-subtler mt-2">
                  Add your product screenshot or video here
                </Typography>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

