import { addons } from "storybook/manager-api";
import { create } from "storybook/theming/create";

const theme = create({
  base: "dark",
  brandTitle: "Synapse",
  brandUrl: "https://synapse.io",
  brandImage: "logo.svg",
  brandTarget: "_blank",
});

addons.setConfig({
  theme,
});

