/* global Sentry */

import { createBrowserHistory } from "history";
import { render } from "react-dom";
import { Router } from "react-router-dom";
import {
  LEAVE_BLOCKER_KEY,
  leaveBlockerCallback,
} from "../components/LeaveBlocker/LeaveBlocker";
import { initSentry } from "../config/Sentry";
import { ScrollToTop } from "../components/ScrollToTop/ScrollToTop";
import { ApiProvider, useAPI } from "../providers/ApiProvider";
import { AppStoreProvider } from "../providers/AppStoreProvider";
import { ConfigProvider } from "../providers/ConfigProvider";
import { MultiProvider } from "../providers/MultiProvider";
import { ProjectProvider } from "../providers/ProjectProvider";
import { RoutesProvider } from "../providers/RoutesProvider";
import {
  DRAFT_GUARD_KEY,
  DraftGuard,
  draftGuardCallback,
} from "../components/DraftGuard/DraftGuard";
import { AsyncPage } from "./AsyncPage/AsyncPage";
import ErrorBoundary from "./ErrorBoundary";
import { FF_UNSAVED_CHANGES, isFF } from "../utils/feature-flags";
import { TourProvider } from "@synapse/core";
import { ToastProvider, ToastViewport } from "@synapse/ui";
import { JotaiProvider, JotaiStore } from "../utils/jotai-store";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@synapse/core/lib/utils/query-client";
import { RootPage } from "./RootPage";
import { ff } from "@synapse/core";
import "@synapse/ui/src/tailwind.css";
import "./App.scss";
import { AuthProvider } from "@synapse/core/providers/AuthProvider";

const getBaseUrl = () => {
  const hostname = window.APP_SETTINGS?.hostname;
  return new URL(hostname || window.location.origin);
};

const baseURL = getBaseUrl();
export const UNBLOCK_HISTORY_MESSAGE = "UNBLOCK_HISTORY";

const browserHistory = createBrowserHistory({
  basename: baseURL.pathname || "/",
  // callback is an async way to confirm or decline going to another page in the context of routing. It accepts `true` or `false`
  getUserConfirmation: (message, callback) => {
    // `history.block` doesn't block events, so in the case of listeners,
    // we need to have some flag that can be checked for preventing related actions
    // `isBlocking` flag is used for this purpose
    browserHistory.isBlocking = true;
    const callbackWrapper = (result) => {
      browserHistory.isBlocking = false;
      callback(result);
      isFF(FF_UNSAVED_CHANGES) &&
        window.postMessage({
          source: "synapse",
          payload: UNBLOCK_HISTORY_MESSAGE,
        });
    };
    if (message === DRAFT_GUARD_KEY) {
      draftGuardCallback.current = callbackWrapper;
    } else if (isFF(FF_UNSAVED_CHANGES) && message === LEAVE_BLOCKER_KEY) {
      leaveBlockerCallback.current = callbackWrapper;
    } else {
      callbackWrapper(window.confirm(message));
    }
  },
});

window.LSH = browserHistory;

initSentry(browserHistory);

const App = ({ content }) => {
  return (
    <ErrorBoundary>
      <Router history={browserHistory}>
        <ScrollToTop />
        <MultiProvider
          providers={[
            <QueryClientProvider client={queryClient} key="query" />,
            <JotaiProvider key="jotai" store={JotaiStore} />,
            <AuthProvider key="auth" />,
            <AppStoreProvider key="app-store" />,
            <ToastProvider key="toast" />,
            <ApiProvider key="api" />,
            <ConfigProvider key="config" />,
            <RoutesProvider key="rotes" />,
            <ProjectProvider key="project" />,
            ff.isActive(ff.FF_PRODUCT_TOUR) && <TourProvider useAPI={useAPI} />,
          ].filter(Boolean)}
        >
          <AsyncPage>
            <DraftGuard />
            <RootPage content={content} />
            <ToastViewport />
          </AsyncPage>
        </MultiProvider>
      </Router>
    </ErrorBoundary>
  );
};

const root = document.querySelector(".app-wrapper");
const content = document.querySelector("#main-content");

// Apply dark theme
document.documentElement.setAttribute("data-color-scheme", "dark");
document.body.setAttribute("data-color-scheme", "dark");

if (root && content) {
  render(<App content={content.innerHTML} />, root);
}

if (module?.hot) {
  module.hot.accept(); // Enable HMR for React components
}