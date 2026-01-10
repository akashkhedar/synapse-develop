import { motion } from "framer-motion";
import { Navigation } from "../Landing/components/Navigation";
import { Footer } from "../Landing/components/Footer";
import { SmoothSection } from "../Landing/components/shared";
import type { Page } from "../types/Page";

export const AboutPage: Page = {
  path: "/about",
  title: "About",
  component: () => {
    const stats = [
    { value: "2020", label: "Founded" },
    { value: "500+", label: "Enterprise Clients" },
    { value: "10M+", label: "Annotations Delivered" },
    { value: "50+", label: "Countries Served" },
  ];

  const values = [
    {
      number: "01",
      title: "Quality First",
      description: "We obsess over data quality. Every annotation goes through rigorous validation to ensure your AI models train on the best possible data.",
    },
    {
      number: "02", 
      title: "Built for Scale",
      description: "From startup to enterprise, our platform grows with you. Handle millions of data points without compromising speed or accuracy.",
    },
    {
      number: "03",
      title: "Security Native",
      description: "Enterprise-grade security isn't an afterthought. SOC 2 Type II, GDPR, and HIPAA compliance built into every layer.",
    },
  ];

  const team = [
    {
      name: "Sarah Chen",
      role: "CEO & Co-Founder",
      description: "Former ML engineer at Google. PhD in Computer Vision from MIT. Built annotation pipelines for autonomous vehicles.",
    },
    {
      name: "Michael Rodriguez",
      role: "CTO & Co-Founder", 
      description: "Ex-Tesla senior engineer. Scaled annotation infrastructure for production self-driving systems.",
    },
    {
      name: "Emily Watson",
      role: "Head of Product",
      description: "10+ years building enterprise ML tools. Previously led product at Salesforce Einstein.",
    },
    {
      name: "David Kim",
      role: "VP Engineering",
      description: "Infrastructure architect from Uber. Expert in distributed systems and platform scalability.",
    },
  ];

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
              // About Synapse
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 leading-tight"
          >
            Building the infrastructure
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
              for AI at scale
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto font-mono"
          >
            We're on a mission to make high-quality training data accessible to every AI team,
            from startups to enterprises.
          </motion.p>
        </div>
      </section>

      {/* Stats Section */}
      <SmoothSection className="py-20 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-12">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="text-4xl md:text-5xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-gray-500 font-mono text-sm">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* Our Story Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <div className="flex items-start gap-4 mb-8">
              <div className="flex flex-col items-start">
                <div className="w-6 h-[2px] bg-gray-600" />
                <div className="w-[2px] h-6 bg-gray-600" />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-white">Our Story</h2>
            </div>
            
            <div className="space-y-6 text-gray-400 font-mono text-lg leading-relaxed">
              <p>
                Synapse was born from a simple frustration: getting high-quality training data 
                for AI models was too hard, too slow, and too expensive.
              </p>
              <p>
                In 2020, our founders—veterans from Google, Tesla, and Uber—came together with 
                a vision to build the annotation infrastructure that they wished existed. An 
                infrastructure that could scale from a weekend project to enterprise production 
                without breaking.
              </p>
              <p>
                Today, we power annotation pipelines for hundreds of organizations, from YC 
                startups training their first models to Fortune 500 companies deploying AI at scale.
              </p>
            </div>
          </motion.div>
        </div>
      </SmoothSection>

      {/* Values Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-white mb-16"
          >
            What we believe
          </motion.h2>

          <div className="space-y-12">
            {values.map((value, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="border-l-2 border-gray-800 pl-8 hover:border-purple-500 transition-colors"
              >
                <div className="text-gray-500 font-mono text-sm mb-2">{value.number}/</div>
                <h3 className="text-2xl font-bold text-white mb-3">{value.title}</h3>
                <p className="text-gray-400 font-mono leading-relaxed">{value.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* Team Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-white mb-16"
          >
            Leadership Team
          </motion.h2>

          <div className="grid md:grid-cols-2 gap-8">
            {team.map((member, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="border border-gray-800 bg-black/50 p-8 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-16 h-16 border border-gray-700 flex items-center justify-center text-3xl">
                    {member.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-1">{member.name}</h3>
                    <div className="text-gray-500 font-mono text-sm">{member.role}</div>
                  </div>
                </div>
                <p className="text-gray-400 font-mono text-sm leading-relaxed">
                  {member.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </SmoothSection>

      {/* CTA Section */}
      <SmoothSection className="py-32 bg-black border-t border-gray-900">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-white mb-6"
          >
            Join us in building the future of AI
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            viewport={{ once: true }}
            className="text-gray-400 font-mono mb-12 text-lg"
          >
            We're always looking for talented people who share our vision.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="bg-white text-black px-10 py-4 text-base font-semibold transition-all"
            >
              View Open Positions →
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.05)" }}
              whileTap={{ scale: 0.98 }}
              className="border border-gray-700 text-white px-10 py-4 text-base font-semibold transition-all"
            >
              Get in Touch
            </motion.button>
          </motion.div>
        </div>
      </SmoothSection>

      <Footer />
    </div>
    );
  },
};