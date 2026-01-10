import { motion } from "framer-motion";
import { Navigation } from "../Landing/components/Navigation";
import type { Page } from "../types/Page";
import { useParams, useHistory } from "react-router-dom";

interface BlogContent {
  id: string;
  title: string;
  date: string;
  readTime: string;
  category: string;
  author: {
    name: string;
    role: string;
  };
  content: {
    type: 'paragraph' | 'heading' | 'quote' | 'code' | 'list';
    text?: string;
    items?: string[];
    level?: number;
  }[];
}

const blogContents: Record<string, BlogContent> = {
  "scaling-annotation-pipelines": {
    id: "scaling-annotation-pipelines",
    title: "Scaling annotation pipelines to millions of data points",
    date: "2026-01-08",
    readTime: "8 min read",
    category: "Engineering",
    author: {
      name: "Michael Rodriguez",
      role: "CTO",
    },
    content: [
      {
        type: 'paragraph',
        text: "When we started Synapse in 2020, processing 10,000 annotations per day felt like a massive achievement. Today, we handle over 10 million annotations monthly across hundreds of enterprise customers. This is the story of how we built infrastructure that scales."
      },
      {
        type: 'heading',
        level: 2,
        text: "The scaling challenge"
      },
      {
        type: 'paragraph',
        text: "Traditional annotation platforms hit a wall around 100K daily annotations. The problem isn't just database throughput—it's the entire stack. Real-time validation, consensus algorithms, quality checks, and payment calculations all need to happen in milliseconds."
      },
      {
        type: 'quote',
        text: "We needed to rethink our entire architecture. Every component had to be designed for horizontal scalability from day one."
      },
      {
        type: 'heading',
        level: 2,
        text: "Architecture decisions"
      },
      {
        type: 'paragraph',
        text: "Our solution involved three key architectural changes:"
      },
      {
        type: 'list',
        items: [
          "Event-driven microservices: Each annotation triggers events processed by specialized services",
          "Distributed consensus: Quality checks run in parallel across multiple worker nodes",
          "Intelligent caching: Hot data stays in Redis, cold data moves to S3 automatically"
        ]
      },
      {
        type: 'paragraph',
        text: "The event-driven approach was crucial. Instead of synchronous processing, we queue every annotation for async handling. This means annotators never wait for backend processing to complete."
      },
      {
        type: 'heading',
        level: 2,
        text: "Database sharding"
      },
      {
        type: 'paragraph',
        text: "We shard our PostgreSQL databases by project ID. Each enterprise customer's data lives on dedicated shards, ensuring noisy neighbors never impact performance. Cross-shard queries run through our aggregation layer that maintains materialized views."
      },
      {
        type: 'code',
        text: "# Simplified sharding logic\ndef get_shard(project_id):\n    shard_num = hash(project_id) % NUM_SHARDS\n    return shard_connections[shard_num]"
      },
      {
        type: 'heading',
        level: 2,
        text: "Results"
      },
      {
        type: 'paragraph',
        text: "After these changes, we saw dramatic improvements:"
      },
      {
        type: 'list',
        items: [
          "P95 latency dropped from 450ms to 85ms",
          "Database CPU usage decreased by 60%",
          "We can now handle 50K concurrent annotators",
          "Zero downtime during our busiest days"
        ]
      },
      {
        type: 'paragraph',
        text: "Building scalable systems is hard. But it's essential when your customers depend on your infrastructure for their ML pipelines. We're still iterating and improving, but we're proud of how far we've come."
      }
    ]
  },
  "future-of-data-labeling": {
    id: "future-of-data-labeling",
    title: "The future of data labeling in the age of foundation models",
    date: "2026-01-05",
    readTime: "6 min read",
    category: "AI/ML",
    author: {
      name: "Sarah Chen",
      role: "CEO",
    },
    content: [
      {
        type: 'paragraph',
        text: "GPT-4, Claude, Llama—foundation models have transformed how we build AI systems. But they haven't eliminated the need for high-quality training data. In fact, they've made it more important than ever."
      },
      {
        type: 'heading',
        level: 2,
        text: "The annotation paradox"
      },
      {
        type: 'paragraph',
        text: "Here's the paradox: foundation models can label data pretty well. But to build specialized AI that outperforms general-purpose models, you need expert-annotated data that captures nuances no foundation model understands."
      },
      {
        type: 'paragraph',
        text: "Medical imaging, legal document analysis, industrial inspection—these domains require expertise that can't be replicated by models trained on internet text."
      },
      {
        type: 'heading',
        level: 2,
        text: "AI-assisted annotation"
      },
      {
        type: 'paragraph',
        text: "We're using foundation models to accelerate human annotators, not replace them. Our AI-assist features:"
      },
      {
        type: 'list',
        items: [
          "Pre-label data to reduce annotator workload by 70%",
          "Suggest corrections in real-time based on project patterns",
          "Flag potentially difficult cases for expert review",
          "Generate synthetic variations for data augmentation"
        ]
      },
      {
        type: 'quote',
        text: "The future isn't AI versus humans—it's AI empowering humans to work faster and more accurately."
      },
      {
        type: 'heading',
        level: 2,
        text: "What's changing"
      },
      {
        type: 'paragraph',
        text: "We're seeing three major shifts in how teams approach training data:"
      },
      {
        type: 'paragraph',
        text: "First, quality over quantity. Instead of millions of noisy labels, teams want thousands of expert-validated examples. Foundation models can handle the rest through few-shot learning."
      },
      {
        type: 'paragraph',
        text: "Second, iterative refinement. Rather than one-time annotation projects, teams continuously improve their datasets based on model performance. It's becoming part of the ML workflow."
      },
      {
        type: 'paragraph',
        text: "Third, multimodal complexity. Modern models process text, images, audio, and video simultaneously. Annotation needs to match this complexity with linked, cross-modal labels."
      },
      {
        type: 'heading',
        level: 2,
        text: "Looking ahead"
      },
      {
        type: 'paragraph',
        text: "Data labeling isn't going away—it's evolving. The teams that win will be those who combine human expertise with AI assistance, focus on quality over scale, and treat data annotation as a core part of their ML infrastructure."
      }
    ]
  },
  "quality-at-scale": {
    id: "quality-at-scale",
    title: "Quality at scale: Our approach to annotation validation",
    date: "2025-12-28",
    readTime: "10 min read",
    category: "Product",
    author: {
      name: "Emily Watson",
      role: "Head of Product",
    },
    content: [
      {
        type: 'paragraph',
        text: "Maintaining 99.9% accuracy across millions of annotations isn't magic—it's a combination of smart product design, quality processes, and the right incentives for annotators."
      },
      {
        type: 'heading',
        level: 2,
        text: "Multi-layered validation"
      },
      {
        type: 'paragraph',
        text: "Every annotation in our platform goes through multiple validation layers before being marked as complete. Here's our quality pipeline:"
      },
      {
        type: 'list',
        items: [
          "Real-time validation: Check constraints as annotators work",
          "Peer review: Random sample reviewed by other annotators",
          "Expert validation: Complex cases escalated to domain experts",
          "Automated quality checks: ML models flag suspicious patterns",
          "Customer review: Final approval by the customer's team"
        ]
      },
      {
        type: 'heading',
        level: 2,
        text: "Consensus mechanisms"
      },
      {
        type: 'paragraph',
        text: "For critical projects, we use consensus labeling. Multiple annotators label the same data independently, and we only accept labels where they agree. Our consensus engine:"
      },
      {
        type: 'code',
        text: "consensus_threshold = 0.85\nif agreement_score >= consensus_threshold:\n    accept_label()\nelse:\n    escalate_to_expert()"
      },
      {
        type: 'paragraph',
        text: "We've found that 3-way consensus with an 85% agreement threshold gives the best balance of accuracy and throughput."
      },
      {
        type: 'heading',
        level: 2,
        text: "Annotator scoring"
      },
      {
        type: 'paragraph',
        text: "Every annotator has a dynamic quality score based on their historical accuracy. Higher scores unlock access to more complex (and higher-paying) projects. This creates a natural incentive for quality work."
      },
      {
        type: 'quote',
        text: "The best quality system is one where everyone's incentives are aligned. When annotators benefit from accurate work, quality improves naturally."
      },
      {
        type: 'heading',
        level: 2,
        text: "Continuous improvement"
      },
      {
        type: 'paragraph',
        text: "We review every annotation that gets flagged or rejected. These become training examples for improving our guidelines, onboarding process, and automated quality checks. It's a flywheel that gets better over time."
      }
    ]
  },
  "autonomous-vehicles-data": {
    id: "autonomous-vehicles-data",
    title: "Building datasets for autonomous vehicles",
    date: "2025-12-20",
    readTime: "12 min read",
    category: "Case Study",
    author: {
      name: "David Kim",
      role: "VP Engineering",
    },
    content: [
      {
        type: 'paragraph',
        text: "Autonomous vehicle perception is one of the most demanding annotation challenges we've tackled. A single hour of driving generates terabytes of sensor data that needs pixel-perfect labels."
      },
      {
        type: 'heading',
        level: 2,
        text: "The scale challenge"
      },
      {
        type: 'paragraph',
        text: "Modern self-driving cars capture data from multiple sensors simultaneously:"
      },
      {
        type: 'list',
        items: [
          "8+ cameras recording at 30fps in 4K resolution",
          "LiDAR generating 2 million points per second",
          "Radar tracking hundreds of objects",
          "GPS, IMU, and vehicle state data"
        ]
      },
      {
        type: 'paragraph',
        text: "Our customer needed 10,000 hours of driving data annotated in 6 months. That's 288 million frames requiring bounding boxes, semantic segmentation, and tracking IDs."
      },
      {
        type: 'heading',
        level: 2,
        text: "Tooling innovations"
      },
      {
        type: 'paragraph',
        text: "We built specialized tools for this project that reduced annotation time by 80%:"
      },
      {
        type: 'paragraph',
        text: "First, auto-propagation. Annotators label a single frame, and our tracking algorithm propagates boxes across the sequence. They only adjust when the algorithm fails."
      },
      {
        type: 'paragraph',
        text: "Second, 3D workspace. Instead of labeling each camera view separately, annotators work in a unified 3D space where one label automatically projects to all camera views."
      },
      {
        type: 'paragraph',
        text: "Third, quality predictors. ML models predict which frames are likely to have errors, prioritizing them for review."
      },
      {
        type: 'heading',
        level: 2,
        text: "Results"
      },
      {
        type: 'paragraph',
        text: "We completed the project in 5 months with 99.7% accuracy:"
      },
      {
        type: 'list',
        items: [
          "288M frames annotated",
          "2.3B bounding boxes drawn",
          "450 trained annotators",
          "Zero missed deadlines"
        ]
      },
      {
        type: 'paragraph',
        text: "The customer's perception model achieved state-of-the-art performance on industry benchmarks and is now running in their production vehicles."
      }
    ]
  },
  "annotation-tools-2026": {
    id: "annotation-tools-2026",
    title: "The annotation tools we're building in 2026",
    date: "2025-12-15",
    readTime: "5 min read",
    category: "Product",
    author: {
      name: "Emily Watson",
      role: "Head of Product",
    },
    content: [
      {
        type: 'paragraph',
        text: "We're shipping some of our biggest product updates ever this year. Here's what we're building based on customer feedback and where we see the market heading."
      },
      {
        type: 'heading',
        level: 2,
        text: "AI-assisted labeling"
      },
      {
        type: 'paragraph',
        text: "Our new AI assistant will pre-label your data using foundation models fine-tuned on your previous annotations. Early testing shows 70% reduction in annotation time while maintaining accuracy."
      },
      {
        type: 'paragraph',
        text: "The assistant learns from your corrections in real-time, getting better the more you use it. It's like having an intern who never stops learning."
      },
      {
        type: 'heading',
        level: 2,
        text: "Collaborative workflows"
      },
      {
        type: 'paragraph',
        text: "Teams can now work together in real-time on the same project:"
      },
      {
        type: 'list',
        items: [
          "Live cursors showing who's working on what",
          "Comments and discussions attached to specific annotations",
          "Approval workflows for quality gates",
          "Project-level chat and notifications"
        ]
      },
      {
        type: 'heading',
        level: 2,
        text: "Advanced analytics"
      },
      {
        type: 'paragraph',
        text: "Our new analytics dashboard helps you understand project health at a glance:"
      },
      {
        type: 'list',
        items: [
          "Real-time throughput and velocity metrics",
          "Quality trends and annotator performance",
          "Cost projections and budget tracking",
          "Model performance correlation"
        ]
      },
      {
        type: 'heading',
        level: 2,
        text: "Video understanding"
      },
      {
        type: 'paragraph',
        text: "We're launching specialized tools for video annotation with automatic tracking, action recognition, and temporal segmentation. Annotate once, track automatically."
      },
      {
        type: 'heading',
        level: 2,
        text: "Custom model integration"
      },
      {
        type: 'paragraph',
        text: "Bring your own models into Synapse for assisted labeling. Upload a model checkpoint, and we'll use it to pre-label data. As you correct labels, we fine-tune the model automatically."
      },
      {
        type: 'quote',
        text: "Our goal is to make Synapse feel like an extension of your ML workflow, not a separate tool you have to learn."
      },
      {
        type: 'paragraph',
        text: "All these features are rolling out over Q1 2026. Enterprise customers will get early access—reach out to your account manager for details."
      }
    ]
  },
  "security-compliance": {
    id: "security-compliance",
    title: "SOC 2 Type II and beyond: Our security journey",
    date: "2025-12-10",
    readTime: "7 min read",
    category: "Security",
    author: {
      name: "Sarah Chen",
      role: "CEO",
    },
    content: [
      {
        type: 'paragraph',
        text: "Achieving SOC 2 Type II compliance took us 18 months. It was painful, expensive, and absolutely worth it. Here's what we learned about building security into a fast-growing startup."
      },
      {
        type: 'heading',
        level: 2,
        text: "Why we prioritized security"
      },
      {
        type: 'paragraph',
        text: "Enterprise customers won't even talk to you without proper security certifications. We needed SOC 2 to compete for large deals, but we also wanted to build security correctly from the start."
      },
      {
        type: 'quote',
        text: "Security isn't something you bolt on later. It has to be part of your company culture from day one."
      },
      {
        type: 'heading',
        level: 2,
        text: "The audit process"
      },
      {
        type: 'paragraph',
        text: "SOC 2 Type II audits verify that your security controls actually work over a 6-month period. Auditors examine everything:"
      },
      {
        type: 'list',
        items: [
          "Access controls and authentication systems",
          "Data encryption at rest and in transit",
          "Incident response procedures",
          "Vendor risk management",
          "Employee security training",
          "Change management processes"
        ]
      },
      {
        type: 'heading',
        level: 2,
        text: "Key changes we made"
      },
      {
        type: 'paragraph',
        text: "We implemented dozens of controls, but a few had the biggest impact:"
      },
      {
        type: 'paragraph',
        text: "First, infrastructure as code. Every system configuration is version controlled and reviewed. No manual changes allowed in production."
      },
      {
        type: 'paragraph',
        text: "Second, automated compliance. We built tools that continuously verify our controls are working. Manual compliance checking doesn't scale."
      },
      {
        type: 'paragraph',
        text: "Third, security training. Every employee completes security training during onboarding and annually thereafter. Security is everyone's job."
      },
      {
        type: 'heading',
        level: 2,
        text: "Beyond SOC 2"
      },
      {
        type: 'paragraph',
        text: "We're now working on HIPAA compliance for healthcare customers and exploring ISO 27001. Each certification opens new market opportunities."
      },
      {
        type: 'paragraph',
        text: "More importantly, strong security practices have become a competitive advantage. Customers trust us with their most sensitive data because they know we take security seriously."
      }
    ]
  }
};

export const BlogPostPage: Page = () => {
  const { id } = useParams<{ id: string }>();
  const history = useHistory();
  const post = blogContents[id];

  if (!post) {
    return (
      <div className="bg-black min-h-screen">
        <Navigation />
        <div className="max-w-4xl mx-auto px-6 py-32 text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Post not found</h1>
          <button 
            onClick={() => history.push('/blog')}
            className="text-purple-400 hover:text-purple-300 font-mono"
          >
            ← Back to blog
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-black min-h-screen">
      <Navigation />
      
      {/* Article Header */}
      <article className="relative pt-32 pb-20">
        <div className="max-w-3xl mx-auto px-6">
          {/* Back button */}
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            onClick={() => history.push('/blog')}
            className="text-gray-500 hover:text-white font-mono text-sm mb-12 transition-colors"
          >
            ← Back to blog
          </motion.button>

          {/* Meta information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-8"
          >
            <div className="flex items-center gap-4 mb-6">
              <span className="text-purple-400 font-mono text-xs uppercase tracking-wider">
                {post.category}
              </span>
              <span className="text-gray-600 font-mono text-xs">
                {new Date(post.date).toLocaleDateString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric' 
                })}
              </span>
              <span className="text-gray-600 font-mono text-xs">
                {post.readTime}
              </span>
            </div>

            {/* Author */}
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 border border-gray-700 flex items-center justify-center text-white">
                {post.author.name.charAt(0)}
              </div>
              <div>
                <div className="text-white font-medium">{post.author.name}</div>
                <div className="text-gray-500 font-mono text-sm">{post.author.role}</div>
              </div>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-12 leading-tight"
          >
            {post.title}
          </motion.h1>

          {/* Divider */}
          <div className="w-full h-[1px] bg-gray-900 mb-12" />

          {/* Content */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="prose prose-invert max-w-none"
          >
            {post.content.map((block, index) => {
              switch (block.type) {
                case 'heading':
                  return (
                    <h2
                      key={index}
                      className="text-2xl md:text-3xl font-bold text-white mt-16 mb-6 first:mt-0"
                    >
                      {block.text}
                    </h2>
                  );
                
                case 'paragraph':
                  return (
                    <p
                      key={index}
                      className="text-gray-400 font-mono text-base leading-relaxed mb-6"
                    >
                      {block.text}
                    </p>
                  );
                
                case 'quote':
                  return (
                    <blockquote
                      key={index}
                      className="border-l-2 border-purple-500 pl-6 my-8 italic"
                    >
                      <p className="text-gray-300 font-mono text-lg leading-relaxed">
                        {block.text}
                      </p>
                    </blockquote>
                  );
                
                case 'code':
                  return (
                    <pre
                      key={index}
                      className="bg-gray-900 border border-gray-800 rounded p-6 overflow-x-auto my-8"
                    >
                      <code className="text-purple-400 font-mono text-sm">
                        {block.text}
                      </code>
                    </pre>
                  );
                
                case 'list':
                  return (
                    <ul
                      key={index}
                      className="space-y-3 my-6 ml-6"
                    >
                      {block.items?.map((item, i) => (
                        <li
                          key={i}
                          className="text-gray-400 font-mono text-base leading-relaxed relative before:content-['—'] before:absolute before:-left-6 before:text-gray-600"
                        >
                          {item}
                        </li>
                      ))}
                    </ul>
                  );
                
                default:
                  return null;
              }
            })}
          </motion.div>

          {/* Divider */}
          <div className="w-full h-[1px] bg-gray-900 mt-16 mb-12" />

          {/* Back to blog link */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-center"
          >
            <button
              onClick={() => history.push('/blog')}
              className="text-gray-500 hover:text-white font-mono transition-colors"
            >
              ← Back to all posts
            </button>
          </motion.div>
        </div>
      </article>
    </div>
  );
};

BlogPostPage.title = "Blog Post";
BlogPostPage.path = "/blog/:id";
BlogPostPage.exact = true;
