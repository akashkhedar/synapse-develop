import { isFlagEnabled } from "@synapse/core/lib/utils/helpers";

export function isInLicense(id: string) {
  return isFlagEnabled(id, window.APP_SETTINGS?.flags || {});
}

