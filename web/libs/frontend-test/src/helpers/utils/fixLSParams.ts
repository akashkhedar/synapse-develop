/**
 * This function will fix Synapse parameters
 * as parameters created in cypress tests are not considered as plain objects by MST as it has it's own Object and Object.prototype is uniq as well
 */
export function fixSFParams(params: Record<string, any>, win: Window): Record<string, any> {
  if (Array.isArray(params)) {
    return win.Array.from(params.map((val) => fixSFParams(val, win)));
  }
  if (typeof params === "object") {
    return win.Object.assign(new win.Object(), {
      ...Object.fromEntries(Object.entries(params).map(([key, value]) => [key, fixSFParams(value, win)])),
    });
  }
  return params;
}

