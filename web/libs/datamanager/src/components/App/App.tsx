import { observer, Provider } from "mobx-react";
import React from "react";
import clsx from "clsx";
import { SDKProvider } from "../../providers/SDKProvider";
import { cn } from "../../utils/bem";
import { Spinner } from "../Common/Spinner";
import { DataManager } from "../DataManager/DataManager";
import { Labeling } from "../Label/Label";
import "./App.scss";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@synapse/core/lib/utils/query-client";
import { AuthProvider } from "@synapse/core/providers/AuthProvider";


interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    error: null,
  };

  componentDidCatch(error: Error): void {
    this.setState({ error });
  }

  render(): React.ReactNode {
    return this.state.error ? (
      <div className="error">{this.state.error.toString()}</div>
    ) : (
      this.props.children
    );
  }
}

interface AppComponentProps {
  app: any;
}

/**
 * Main Component
 */
const AppComponent: React.FC<AppComponentProps> = ({ app }) => {
  const rootCN = cn("root");
  const rootClassName = rootCN.mod({ mode: app.SDK.mode }).toString();



  // Debug: Check canAnnotate status
  console.log(
    "App rendering - canAnnotate:",
    app.SDK?.canAnnotate,
    "isLabeling:",
    app.isLabeling,
    "loading:",
    app.loading
  );

  // Inject font if not present
  React.useEffect(() => {
    if (!document.getElementById("dm-font-space-grotesk")) {
      const link = document.createElement("link");
      link.id = "dm-font-space-grotesk";
      link.rel = "stylesheet";
      link.href =
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap";
      document.head.appendChild(link);
    }
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Provider store={app}>
            <SDKProvider sdk={app.SDK}>
              <div className={rootClassName}>
                {app.crashed ? (
                  <div className={clsx(rootCN.toString(), rootClassName)}>
                    <span className={rootCN.elem("header").toString()}>
                      Oops...
                    </span>
                    <span className={rootCN.elem("description").toString()}>
                      Project has been deleted or not yet created.
                    </span>
                  </div>
                ) : app.loading ? (
                  <div className={cn("app-loader").toString()}>
                    <Spinner size="large" />
                  </div>
                ) : app.isLabeling ? (
                  <Labeling />
                ) : (
                  <DataManager />
                )}
                <div className={cn("offscreen").toString()} />
              </div>
            </SDKProvider>
          </Provider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export const App = observer(AppComponent);
