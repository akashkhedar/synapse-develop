import { Typography } from "@synapse/ui";

export const Navbar = () => {

  const handleGetStarted = () => {
    window.location.href = "/user/signup";
  };

  const handleAnnotator = ()=>{
  window.location.href = "/annotators/signup";
  }

  const handleServices = ()=>{
  window.location.href = "/services";
  }
  const handleAbout = () => {
    window.location.href = "/about";
  };
  const handleContact = ()=>{
  window.location.href = "/contact";
  }
  const handleSecurity = ()=>{
  window.location.href = "/security";
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-neutral-border bg-neutral-surface backdrop-blur-lg bg-opacity-90">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-gradient-to-br from-accent-peach via-accent-orange to-accent-grape rounded-sm transition-transform group-hover:scale-110" />
          <Typography
            variant="headline"
            size="small"
            className="font-['Nova_Oval'] text-primary-content"
          >
            Synapse
          </Typography>
        </a>
        <div className="flex items-center gap-4">
          <button
            onClick={handleContact}
            className="px-6 py-2 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            contact us
          </button>
          <button
            onClick={handleSecurity}
            className="px-6 py-2 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            security
          </button>
          <button
            onClick={handleAbout}
            className="px-6 py-2 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            about us
          </button>
          <button
            onClick={handleServices}
            className="px-6 py-2 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            Services
          </button>
          <button
            onClick={handleGetStarted}
            className="px-6 py-2 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            Sign Up as Client
          </button>
          <button
            onClick={handleAnnotator}
            className="px-6 py-2 bg-neutral-surface border border-neutral-border text-primary-content rounded-lg font-medium hover:bg-neutral-surface-hover transition-all"
          >
            Register as Annotator
          </button>
        </div>
      </div>
    </nav>
  );
};

