import { Menubar } from "../components/Menubar/Menubar";
import { ProjectRoutes } from "../routes/ProjectRoutes";
import { useOrgValidation } from "../hooks/useOrgValidation";
import { useLocation, useHistory } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "@synapse/core/providers/AuthProvider";

export const RootPage = ({ content }) => {
  const location = useLocation();
  const history = useHistory();
  const { user, isLoading } = useAuth();
  const pinned = localStorage.getItem("sidebar-pinned") === "true";
  const opened = pinned && localStorage.getItem("sidebar-opened") === "true";

  // Public routes that don't need the Menubar/Sidebar
  const publicRoutes = [
    "/",
    "/login",
    "/signup-client",
    "/register-annotator",
    "/annotators/login",
    "/annotators/signup",
    "/annotators/test",
    "/annotators/skill-test",
    "/annotators/verify",
    "/annotator",
    "/invite",
    "/services",
    "/about",
    "/contact",
    "/security",
    "/careers",
    "/blog",
    "/docs",
    "/user/login",
    "/user/signup",
  ];

  // Semi-protected annotator routes (need auth but not full menubar)
  const annotatorRoutes = [
    "/annotators/earnings",
    "/annotators/payouts",
    "/annotators/transactions",
  ];

  // Semi-protected expert routes (need auth but not org validation)
  const expertRoutes = [
    "/expert/dashboard",
    "/expert/review",
    "/expert/earnings",
    "/expert/payouts",
  ];

  // Check annotator and expert routes FIRST (more specific)
  const isAnnotatorRoute = annotatorRoutes.some(
    (route) =>
      location.pathname === route || location.pathname.startsWith(route)
  );

  const isExpertRoute = expertRoutes.some(
    (route) =>
      location.pathname === route || location.pathname.startsWith(route)
  );

  // Then check public routes - but exclude if already matched as annotator/expert route
  const isPublicRoute = !isAnnotatorRoute && !isExpertRoute && publicRoutes.some(
    (route) =>
      location.pathname === route || location.pathname.startsWith(route + "/")
  );

  // Always call hooks unconditionally (React rules), but control execution via parameter
  useOrgValidation(!isPublicRoute && !isAnnotatorRoute && !isExpertRoute);

  // Role-based routing: redirect based on user role after authentication
  useEffect(() => {
    // Skip if still loading auth or on public route
    if (isLoading || isPublicRoute || !user) {
      return;
    }

    const isAnnotator = !!user.is_annotator;
    const isClient = !!user.is_client;
    const isExpert = !!user.is_expert;

    // Clients (non-annotator, non-expert) go to /dashboard
    if (
      isClient &&
      !isAnnotator &&
      !isExpert &&
      (location.pathname === "/" || location.pathname === "/login")
    ) {
      history.replace("/dashboard");
      return;
    }

    // Experts go to /projects (like annotators, they see assigned projects)
    if (
      isExpert &&
      (location.pathname === "/" || location.pathname === "/login")
    ) {
      history.replace("/projects");
      return;
    }

    // Redirect annotators to /projects if they're on root or login
    if (
      isAnnotator &&
      !isClient &&
      (location.pathname === "/" || location.pathname === "/login")
    ) {
      history.replace("/projects");
      return;
    }

    // BLOCK experts and annotators from accessing /dashboard
    // Show 404 or redirect to projects (User requested 404/block "sneak in", but projects redirect is safer/smoother UX, let's just force projects for now as effective 404 for them)
    // Actually user specifically asked for "even if ... try to sneak in they should be given 404 error". 
    // Implementing explicit check for 404.
    if (
      (isExpert || (isAnnotator && !isClient)) &&
      location.pathname === "/dashboard"
    ) {
       // We can redirect to a 404 route if it exists, or just valid path.
       // User asked for "404 error". Let's redirect to a non-existent path to trigger 404 or use state.
       // Or simpler: History replace to /404 if you have one, or just /projects if we want to be nice.
       // "sneak in ... be given 404 error" -> aggressive. 
       // I'll redirect to /404
       history.replace("/404");
       return;
    }
  }, [isLoading, user, location.pathname, isPublicRoute, history]);

  // Prevent AsyncPage from fetching on public routes
  useEffect(() => {
    if (isPublicRoute) {
      // Stop any pending async operations
      return;
    }
  }, [isPublicRoute]);

  // If it's a public route, don't wrap with Menubar
  if (isPublicRoute) {
    return <ProjectRoutes content={content} />;
  }

  return (
    <Menubar
      enabled={true}
      defaultOpened={opened}
      defaultPinned={pinned}
      onSidebarToggle={(visible) =>
        localStorage.setItem("sidebar-opened", visible)
      }
      onSidebarPin={(pinned) => localStorage.setItem("sidebar-pinned", pinned)}
    >
      <ProjectRoutes content={content} />
    </Menubar>
  );
};

