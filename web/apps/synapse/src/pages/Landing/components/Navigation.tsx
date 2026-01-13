import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useHistory } from "react-router-dom";

export const Navigation = () => {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const history = useHistory();

  const dropdownContent: Record<string, { title: string; items: string[] }[]> = {
    'RESOURCES': [
      { title: '//COMPANY', items: ['ABOUT', 'CONTACT US'] },
      { title: '//LEARN', items: ['BLOG', 'SECURITY'] },
    ],
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-black border-b border-gray-800"
    >
      {/* Main navbar container */}
      <div className="max-w-[1400px] mx-auto px-10 lg:px-16 py-2">
        <div className="flex items-center justify-between h-20">
          
          {/* Left section - Logo */}
          <motion.div 
            className="flex items-center gap-3 flex-shrink-0 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            onClick={() => history.push('/')}
          >
            <div className="w-8 h-8 border border-white flex items-center justify-center">
              <span className="text-white font-light text-lg">λ</span>
            </div>
            <span className="text-white font-medium text-3xl tracking-wide">Synapse</span>
          </motion.div>

          {/* Center section - Nav Links */}
          <div className="hidden md:flex items-center gap-14 flex-1 justify-center">
            <span className="text-gray-300 hover:text-white text-[13px] font-medium tracking-[0.2em] cursor-pointer transition-colors" onClick={() => {
              history.push("/docs/")
            }}>
              DOCS
            </span>

            {/* Resources Dropdown */}
            <div 
              className="relative"
              onMouseEnter={() => setActiveDropdown('RESOURCES')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <span className="text-gray-300 hover:text-white text-[13px] font-medium tracking-[0.2em] cursor-pointer transition-colors">
                RESOURCES
              </span>
              <AnimatePresence>
                {activeDropdown === 'RESOURCES' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.2 }}
                    className="absolute top-full left-1/2 -translate-x-1/2 mt-6 bg-black border border-gray-800 p-8 min-w-[300px] grid grid-cols-2 gap-8"
                  >
                    {dropdownContent['RESOURCES'].map((section, idx) => (
                      <div key={idx}>
                        <div className="text-gray-600 text-[10px] mb-4 tracking-widest font-medium">
                          {section.title}
                        </div>
                        <div className="space-y-1">
                          {section.items.map((item, itemIdx) => (
                            <div 
                              key={itemIdx}
                              onClick={() => {
                                if (item === 'ABOUT') history.push('/about');
                                if (item === 'CONTACT US') history.push('/contact');
                                if (item === 'BLOG') history.push('/blog');
                                setActiveDropdown(null);
                              }}
                              className="text-white text-xs tracking-wide hover:bg-white hover:text-black cursor-pointer transition-colors font-medium px-2 py-2 -mx-2"
                            >
                              {item}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Right section - Auth buttons */}
          <div className="flex items-center gap-8 flex-shrink-0">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                window.location.href = "/user/login";
              }}
              className="text-gray-300 hover:text-white text-[13px] font-medium tracking-[0.2em] transition-colors"
            >
              LOG IN
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                window.location.href = "/user/signup";
              }}
              className="bg-[#e8e4d9] text-black px-8 py-5 text-[13px] font-semibold tracking-[0.15em] transition-all hover:bg-[#d4d0c5]"
            >
              GET STARTED
            </motion.button>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};
