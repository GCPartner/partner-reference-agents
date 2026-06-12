import { AppConfig } from "./types.js";
import { theme } from "../theme/default-theme.js";

export const config: AppConfig = {
  key: "phoneplan",
  title: "Corporate Phone Plan Shopper",
  placeholder: "e.g. I need a plan with international calling and a Pixel 9",
  theme: theme,
  loadingText: [
    "Checking plan eligibility...",
    "Searching for devices...",
    "Reviewing pricing..."
  ]
};
