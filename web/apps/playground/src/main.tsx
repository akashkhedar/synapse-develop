import { createRoot } from "react-dom/client";
import "./utils/embedFeatureFlags";
import { PlaygroundApp } from "./components/PlaygroundApp";

import "@synapse/ui/src/styles.scss";
import "@synapse/ui/src/tailwind.css";

const root = createRoot(document.getElementById("root")!);
root.render(<PlaygroundApp />);

