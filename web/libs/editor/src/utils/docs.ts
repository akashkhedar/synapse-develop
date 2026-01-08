/**
 * Returns the base URL for documentation depending on deployment type.
 * - Enterprise: https://docs.Synapse.com/
 * - Open Source: https://synapse.io/
 */
export function getDocsBaseUrl(): string {
  if (typeof window !== "undefined" && window.APP_SETTINGS?.billing?.enterprise) {
    return "https://docs.Synapse.com/";
  }
  return "https://synapse.io/";
}

/**
 * Returns a full documentation URL for the current deployment type.
 *
 * Usage:
 *   getDocsUrl('guide/labeling') // same path for both domains
 *   getDocsUrl('guide/labeling', 'guide/label-guide') // first param for synapse.io, second for docs.Synapse.com
 *
 * @param pathOSS - Path for synapse.io (and default for both if only one param)
 * @param pathEnterprise - Optional path for docs.Synapse.com
 * @returns {string} Full documentation URL
 */
export function getDocsUrl(pathOSS: string, pathEnterprise?: string): string {
  const base = getDocsBaseUrl();
  const isEnterprise = typeof window !== "undefined" && window.APP_SETTINGS?.billing?.enterprise;
  const path = isEnterprise && pathEnterprise ? pathEnterprise : pathOSS;
  return `${base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

