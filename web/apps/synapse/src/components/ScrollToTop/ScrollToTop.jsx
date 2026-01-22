import { useEffect, useLayoutEffect } from "react";
import { useLocation } from "react-router-dom";

export const ScrollToTop = () => {
  const { pathname } = useLocation();

  useLayoutEffect(() => {
    // Disable browser's default scroll restoration to prevent it from interfering
    if ("scrollRestoration" in window.history) {
      window.history.scrollRestoration = "manual";
    }

    // Force scroll to top immediately
    window.scrollTo(0, 0);
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
  }, [pathname]);

  return null;
};
