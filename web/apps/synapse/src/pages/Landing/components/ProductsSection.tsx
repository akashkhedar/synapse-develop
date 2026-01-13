import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

// Placeholder for future brain visualization
const BrainVisualization = () => {
  return (
    <div className="w-full h-[400px] mb-20 relative overflow-hidden flex items-center justify-center" style={{ backgroundColor: '#a7b6d2' }}>
      <div className="text-center text-gray-600/50">
        {/* Brain visualization coming soon */}
      </div>
    </div>
  );
};

export const ProductsSection = () => {
  const products = [
    {
      title: "Computer Vision",
      description: "Image segmentation, object detection, keypoint annotation",
      icon: "👁️",
      gradient: "from-blue-500/20 to-cyan-500/20"
    },
    {
      title: "Natural Language",
      description: "NER, text classification, sentiment analysis, relation extraction",
      icon: "📝",
      gradient: "from-purple-500/20 to-pink-500/20"
    },
    {
      title: "Audio & Speech",
      description: "Transcription, speaker diarization, sound classification",
      icon: "🎵",
      gradient: "from-green-500/20 to-emerald-500/20"
    }
  ];

  return (
    <SmoothSection className="py-32 bg-black border-t border-gray-900">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-8">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Every Data Type. Every Annotation.
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            From bounding boxes to named entities — Synapse supports 50+ annotation types across images, text, audio, video, and multi-modal data
          </p>
        </div>

        <BrainVisualization />

        
      </div>
    </SmoothSection>
  );
};
