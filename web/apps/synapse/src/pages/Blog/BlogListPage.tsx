import { motion } from "framer-motion";
import { Navigation } from "../Landing/components/Navigation";
import { Footer } from "../Landing/components/Footer";
import type { Page } from "../types/Page";
import { useHistory } from "react-router-dom";
import { useEffect, useState } from "react";
import { blogsApi, BlogPost } from "../../services/blogsApi";

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
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const data = await blogsApi.getBlogPosts();
        setPosts(data);
      } catch (error) {
        console.error("Failed to fetch blog posts:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

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
          {loading ? (
             <div className="text-white text-center font-mono">Loading...</div>
          ) : (
            <div className="space-y-0">
              {posts.map((post, index) => (
                <motion.article
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  onClick={() => history.push(`/blog/${post.slug}`)}
                  className="border-t border-gray-900 py-12 cursor-pointer group"
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-4">
                        {post.tags.length > 0 && (
                          <span className="text-gray-500 font-mono text-xs uppercase tracking-wider">
                            {post.tags[0]}
                          </span>
                        )}
                        <span className="text-gray-700 font-mono text-xs">
                          {new Date(post.created_at).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric', 
                            year: 'numeric' 
                          })}
                        </span>
                        <span className="text-gray-700 font-mono text-xs">
                          5 min read
                        </span>
                      </div>

                      <div className="flex gap-6">
                         {/* Optional Image Thumbnail if available, or just keeping text design */}
                         {post.cover_image && (
                           <div className="hidden md:block w-32 h-24 bg-gray-900 overflow-hidden flex-shrink-0">
                             <img src={post.cover_image} alt="" className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" />
                           </div>
                         )}
                         <div>
                            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4 group-hover:text-purple-400 transition-colors">
                              {post.title}
                            </h2>

                            <p className="text-gray-400 font-mono text-base leading-relaxed mb-6">
                              {post.subtitle || "Checking internal consistency..."}
                            </p>
                         </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 border border-gray-700 flex items-center justify-center text-sm text-white">
                          {post.author_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="text-white text-sm font-medium">{post.author_name}</div>
                          {/* <div className="text-gray-500 font-mono text-xs">Author</div> */}
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
          )}
        </div>
      </SmoothSection>

      <Footer />
    </div>
  );
};

BlogListPage.title = "Blog";
BlogListPage.path = "/blog";
BlogListPage.exact = true;
