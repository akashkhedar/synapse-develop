import { Typography } from "@synapse/ui";

const features = [
  {
    icon: "🖼️",
    title: "Computer Vision",
    description:
      "Label images with bounding boxes, polygons, keypoints, and semantic segmentation for object detection and classification.",
  },
  {
    icon: "📝",
    title: "Natural Language",
    description:
      "Annotate text for NER, sentiment analysis, classification, and question answering with powerful text tools.",
  },
  {
    icon: "🎵",
    title: "Audio Labeling",
    description:
      "Transcribe, classify, and segment audio data for speech recognition and sound classification tasks.",
  },
  {
    icon: "🎬",
    title: "Video Analysis",
    description:
      "Frame-by-frame annotation, object tracking, and action recognition for video understanding models.",
  },
  {
    icon: "📊",
    title: "Time Series",
    description:
      "Label temporal data for anomaly detection, forecasting, and pattern recognition in sequential data.",
  },
  {
    icon: "🤖",
    title: "ML Integration",
    description:
      "Connect your models for active learning, pre-annotations, and continuous model improvement workflows.",
  },
];

export const Features = () => {
  return (
    <section className="py-20 bg-neutral-surface">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <Typography
            variant="headline"
            size="large"
            className="mb-4 text-primary-content"
          >
            Everything You Need to Label Data
          </Typography>
          <Typography
            size="large"
            className="text-neutral-content-subtle max-w-2xl mx-auto"
          >
            Comprehensive tools for every data type and annotation workflow.
            Built for teams of any size.
          </Typography>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group p-6 bg-neutral-surface-emphasis rounded-xl border border-neutral-border hover:border-accent-orange hover:shadow-xl transition-all cursor-pointer"
            >
              <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <Typography
                variant="headline"
                size="small"
                className="mb-2 text-primary-content"
              >
                {feature.title}
              </Typography>
              <Typography className="text-neutral-content-subtle leading-relaxed">
                {feature.description}
              </Typography>
            </div>
          ))}
        </div>

        {/* Additional Features */}
        <div className="mt-16 p-8 bg-gradient-to-r from-accent-peach/5 via-accent-orange/5 to-accent-grape/5 rounded-2xl border border-neutral-border">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <Typography
                variant="headline"
                size="large"
                className="text-accent-orange mb-2"
              >
                50+
              </Typography>
              <Typography className="text-neutral-content-subtle">
                Pre-built Templates
              </Typography>
            </div>
            <div>
              <Typography
                variant="headline"
                size="large"
                className="text-accent-grape mb-2"
              >
                100K+
              </Typography>
              <Typography className="text-neutral-content-subtle">
                Active Users
              </Typography>
            </div>
            <div>
              <Typography
                variant="headline"
                size="large"
                className="text-accent-peach mb-2"
              >
                25K+
              </Typography>
              <Typography className="text-neutral-content-subtle">
                GitHub Stars
              </Typography>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

