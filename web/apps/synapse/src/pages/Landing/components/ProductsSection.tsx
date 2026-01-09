import { motion } from "framer-motion";
import { SmoothSection } from "./shared";

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
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Annotation for every modality
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Purpose-built tools for every type of AI training data
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {products.map((product, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              whileHover={{ y: -8, transition: { duration: 0.2 } }}
              className="group relative bg-gray-900/50 border border-gray-800 rounded-2xl p-8 hover:border-gray-700 transition-all cursor-pointer overflow-hidden"
            >
              {/* Gradient overlay on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${product.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              
              <div className="relative z-10">
                <div className="text-5xl mb-6">{product.icon}</div>
                <h3 className="text-2xl font-bold text-white mb-3">{product.title}</h3>
                <p className="text-gray-400 leading-relaxed">{product.description}</p>
                
                <motion.div 
                  className="mt-6 flex items-center gap-2 text-gray-400 group-hover:text-white transition-colors"
                  whileHover={{ x: 5 }}
                >
                  <span className="text-sm font-medium">Learn more</span>
                  <span>→</span>
                </motion.div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </SmoothSection>
  );
};
