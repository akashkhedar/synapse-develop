import { motion } from "framer-motion";
import { Navigation } from "../Landing/components/Navigation";
import type { Page } from "../types/Page";
import { useParams, useHistory } from "react-router-dom";
import { useEffect, useState } from "react";
import { blogsApi, BlogPost } from "../../services/blogsApi";
import ReactMarkdown from "react-markdown";

export const BlogPostPage: Page = () => {
  const { id } = useParams<{ id: string }>(); // 'id' here is the slug defined in route /blog/:id
  const history = useHistory();
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const data = await blogsApi.getBlogPostBySlug(id);
        setPost(data);
      } catch (err) {
        console.error("Failed to fetch blog post:", err);
        setError("Post not found");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchPost();
    }
  }, [id]);

  if (loading) {
     return (
        <div className="bg-black min-h-screen text-white flex items-center justify-center font-mono">
           Loading...
        </div>
     );
  }

  if (error || !post) {
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
    <div className="bg-black min-h-screen selection:bg-purple-500/30 selection:text-white">
      <Navigation />
      
      {/* Background Grid - consistent with List Page */}
      <div className="fixed inset-0 opacity-[0.03] pointer-events-none">
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

      <article className="relative pt-32 pb-20">
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          {/* Back button */}
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            onClick={() => history.push('/blog')}
            className="group flex items-center gap-2 text-gray-400 hover:text-white mb-12 transition-colors duration-300"
          >
            <span className="font-mono text-xs uppercase tracking-[0.2em] border-b border-transparent group-hover:border-purple-500 transition-all">
              ← Back to Blog
            </span>
          </motion.button>

          {/* Meta Information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-8"
          >
            <div className="flex flex-wrap items-center gap-4 mb-6">
              {post.tags.length > 0 && (
                <span className="px-3 py-1 bg-purple-500/10 border border-purple-500/20 text-purple-400 font-mono text-[10px] uppercase tracking-wider rounded">
                  {post.tags[0]}
                </span>
              )}
              <div className="h-1 w-1 bg-gray-800 rounded-full" />
              <span className="text-gray-500 font-mono text-xs uppercase tracking-wider">
                {new Date(post.created_at).toLocaleDateString('en-US', { 
                  month: 'long', 
                  day: 'numeric', 
                  year: 'numeric' 
                })}
              </span>
              <div className="h-1 w-1 bg-gray-800 rounded-full" />
              <span className="text-gray-500 font-mono text-xs uppercase tracking-wider">
                5 MIN READ
              </span>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-[1.1]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            {post.title}
          </motion.h1>

          {/* Subtitle */}
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.25 }}
            className="text-xl md:text-2xl text-gray-400 font-light leading-relaxed mb-10"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
             {post.subtitle}
          </motion.p>

          {/* Author Block */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex items-center gap-4 mb-12 border-b border-gray-900 pb-12"
          >
            <div className="w-12 h-12 bg-gray-900 border border-gray-800 flex items-center justify-center text-white font-mono text-lg rounded-full">
              {post.author_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="text-white font-medium" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                {post.author_name}
              </div>
              <div className="text-gray-500 text-xs uppercase tracking-wider font-mono mt-0.5">
                Author
              </div>
            </div>
          </motion.div>

          {/* Cover Image */}
          {post.cover_image && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="mb-16 relative group"
            >
              <div className="absolute inset-0 bg-purple-500/5 group-hover:bg-purple-500/0 transition-colors duration-500" />
              <div className="absolute -inset-px border border-gray-800 z-10 pointer-events-none" />
              <img 
                src={post.cover_image} 
                alt={post.title} 
                className="w-full h-auto object-cover grayscale-[20%] group-hover:grayscale-0 transition-all duration-700" 
              />
            </motion.div>
          )}

          {/* Content */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="prose prose-invert max-w-none prose-lg"
          >
            <ReactMarkdown
              components={{
                h1: ({node, ...props}) => (
                  <h1 className="text-3xl font-bold text-white mt-12 mb-6" style={{ fontFamily: "'Space Grotesk', sans-serif" }} {...props} />
                ),
                h2: ({node, ...props}) => (
                  <h2 className="text-2xl font-bold text-white mt-16 mb-6 flex items-center gap-4" style={{ fontFamily: "'Space Grotesk', sans-serif" }} {...props}>
                    <span className="w-8 h-[1px] bg-purple-500/50 inline-block" />
                    {props.children}
                  </h2>
                ),
                h3: ({node, ...props}) => (
                  <h3 className="text-xl font-bold text-white mt-12 mb-4" style={{ fontFamily: "'Space Grotesk', sans-serif" }} {...props} />
                ),
                p: ({node, ...props}) => (
                  <p className="text-gray-300 leading-relaxed mb-6 font-light" {...props} />
                ),
                ul: ({node, ...props}) => (
                  <ul className="space-y-3 my-8" {...props} />
                ),
                li: ({node, ...props}) => (
                  <li className="flex gap-3 text-gray-300 group" {...props}>
                    <span className="text-purple-500 font-mono mt-1 opacity-60 group-hover:opacity-100 transition-opacity">›</span>
                    <span>{props.children}</span>
                  </li>
                ),
                blockquote: ({node, ...props}) => (
                  <blockquote className="border-l-2 border-purple-500 pl-6 my-10 italic text-xl text-gray-200" style={{ fontFamily: "'Space Grotesk', sans-serif" }} {...props} />
                ),
                code: ({node, ...props}) => {
                   // Separate inline code vs block code
                   const match = /language-(\w+)/.exec(props.className || '')
                   const isInline = !match && !props.children?.toString().includes('\n')
                   
                   return isInline ? (
                     <code className="bg-gray-800/50 text-purple-300 rounded px-1.5 py-0.5 font-mono text-sm border border-gray-800" {...props} />
                   ) : (
                     <pre className="bg-[#0a0a0a] border border-gray-800 p-6 overflow-x-auto my-8 rounded-sm relative group">
                        <div className="absolute top-0 left-0 right-0 h-6 bg-gray-900/50 border-b border-gray-800 flex items-center px-2 gap-1.5">
                           <div className="w-2.5 h-2.5 rounded-full bg-slate-700/50" />
                           <div className="w-2.5 h-2.5 rounded-full bg-slate-700/50" />
                           <div className="w-2.5 h-2.5 rounded-full bg-slate-700/50" />
                        </div>
                        <code className="text-gray-300 font-mono text-sm block mt-4" {...props} />
                     </pre>
                   )
                },
                a: ({node, ...props}) => (
                  <a className="text-purple-400 hover:text-purple-300 underline underline-offset-4 decoration-purple-500/30 hover:decoration-purple-500 transition-all" {...props} />
                ),
              }}
            >
              {post.content}
            </ReactMarkdown>
          </motion.div>

          {/* Footer Divider */}
          <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-gray-800 to-transparent mt-24 mb-16" />

          {/* Bottom Back Button */}
          <motion.div
             initial={{ opacity: 0 }}
             whileInView={{ opacity: 1 }}
             viewport={{ once: true }}
             className="text-center"
          >
             <button
              onClick={() => history.push('/blog')}
              className="bg-gray-900 text-white px-8 py-4 font-mono text-sm uppercase tracking-widest hover:bg-gray-800 border border-gray-800 transition-all hover:scale-105 active:scale-95 hover:border-purple-500/30"
            >
              Back to All Insights
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
