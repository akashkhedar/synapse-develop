import { motion } from "framer-motion";
import { Navigation } from "../Landing/components/Navigation";
import { Footer } from "../Landing/components/Footer";
import type { Page } from "../types/Page";
import { useHistory } from "react-router-dom";

export interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: string;
  author: {
    name: string;
    role: string;
  };
}

const blogPosts: BlogPost[] = [
  {
    id: "scaling-annotation-pipelines",
    title: "Scaling annotation pipelines to millions of data points",
    excerpt: "How we built infrastructure to handle 10M+ annotations per month without compromising on quality or speed.",
    date: "2026-01-08",
    readTime: "8 min read",
    category: "Engineering",
    author: {
      name: "Michael Rodriguez",
      role: "CTO",
    },
  },
  {
    id: "future-of-data-labeling",
    title: "The future of data labeling in the age of foundation models",
    excerpt: "Large language models are changing how we think about training data. Here's what it means for annotation.",
    date: "2026-01-05",
    readTime: "6 min read",
    category: "AI/ML",
    author: {
      name: "Sarah Chen",
      role: "CEO",
    },
  },
  {
    id: "quality-at-scale",
    title: "Quality at scale: Our approach to annotation validation",
    excerpt: "A deep dive into our multi-layered quality assurance process that maintains 99.9% accuracy.",
    date: "2025-12-28",
    readTime: "10 min read",
    category: "Product",
    author: {
      name: "Emily Watson",
      role: "Head of Product",
    },
  },
  {
    id: "autonomous-vehicles-data",
    title: "Building datasets for autonomous vehicles",
    excerpt: "What it takes to annotate millions of frames for self-driving car perception systems.",
    date: "2025-12-20",
    readTime: "12 min read",
    category: "Case Study",
    author: {
      name: "David Kim",
      role: "VP Engineering",
    },
  },
  {
    id: "annotation-tools-2026",
    title: "The annotation tools we're building in 2026",
    excerpt: "A preview of upcoming features including AI-assisted labeling, collaborative workflows, and more.",
    date: "2025-12-15",
    readTime: "5 min read",
    category: "Product",
    author: {
      name: "Emily Watson",
      role: "Head of Product",
    },
  },
  {
    id: "security-compliance",
    title: "SOC 2 Type II and beyond: Our security journey",
    excerpt: "How we achieved enterprise-grade security compliance and what it means for our customers.",
    date: "2025-12-10",
    readTime: "7 min read",
    category: "Security",
    author: {
      name: "Sarah Chen",
      role: "CEO",
    },
  },
];

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

export const BlogListPage: Page = () => {
  const history = useHistory();

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
              // Blog
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 leading-tight"
          >
            Insights on AI,
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              data, and scale
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto font-mono"
          >
            Technical deep-dives, product updates, and lessons learned building
            annotation infrastructure at scale.
          </motion.p>
        </div>
      </section>

      {/* Blog Posts Grid */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <div className="space-y-0">
            {blogPosts.map((post, index) => (
              <motion.article
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                onClick={() => history.push(`/blog/${post.id}`)}
                className="border-t border-gray-900 py-12 cursor-pointer group"
              >
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-4">
                      <span className="text-gray-500 font-mono text-xs uppercase tracking-wider">
                        {post.category}
                      </span>
                      <span className="text-gray-700 font-mono text-xs">
                        {new Date(post.date).toLocaleDateString('en-US', { 
                          month: 'short', 
                          day: 'numeric', 
                          year: 'numeric' 
                        })}
                      </span>
                      <span className="text-gray-700 font-mono text-xs">
                        {post.readTime}
                      </span>
                    </div>

                    <h2 className="text-2xl md:text-3xl font-bold text-white mb-4 group-hover:text-purple-400 transition-colors">
                      {post.title}
                    </h2>

                    <p className="text-gray-400 font-mono text-base leading-relaxed mb-6">
                      {post.excerpt}
                    </p>

                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 border border-gray-700 flex items-center justify-center text-sm text-white">
                        {post.author.name.charAt(0)}
                      </div>
                      <div>
                        <div className="text-white text-sm font-medium">{post.author.name}</div>
                        <div className="text-gray-500 font-mono text-xs">{post.author.role}</div>
                      </div>
                    </div>
                  </div>

                  <div className="md:w-24 flex md:justify-end">
                    <motion.div
                      className="text-gray-600 group-hover:text-white transition-colors font-mono text-sm"
                      whileHover={{ x: 5 }}
                    >
                      Read →
                    </motion.div>
                  </div>
                </div>
              </motion.article>
            ))}
          </div>
        </div>
      </SmoothSection>

      <Footer />
    </div>
  );
};

BlogListPage.title = "Blog";
BlogListPage.path = "/blog";
BlogListPage.exact = true;
