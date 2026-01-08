import { Synapse } from "@synapse/frontend-test/helpers/SF";

describe("Feature Flags", () => {
  it("can set feature flags on the global object", () => {
    const flagName = "customFeatureFlag";
    const anotherFlag = "anotherFlag";

    cy.visit("/");

    Synapse.setFeatureFlags({
      [flagName]: true,
    });

    Synapse.featureFlag(flagName).should("be.true");
    Synapse.featureFlag(anotherFlag).should("be.false");
  });

  it("can set feature flags before navigation", () => {
    // setting only this flag
    const flagName = "customFeatureFlag";
    const anotherFlag = "anotherFlag";

    Synapse.setFeatureFlagsOnPageLoad({
      [flagName]: true,
    });

    cy.visit("/");

    Synapse.featureFlag(flagName).should("be.true");
    Synapse.featureFlag(anotherFlag).should("be.false");
  });

  // helpers' self-testing to keep it clear
  it("can extend previously set flag list and set them all before navigation", () => {
    // setting only this flag
    const setFlagName = "setFlag";
    const setButCanceledFlag = "setButCanceledFlag";
    const addedFlagName = "addedFlag";

    Synapse.setFeatureFlagsOnPageLoad({
      [setFlagName]: true,
      [setButCanceledFlag]: true,
    });

    Synapse.addFeatureFlagsOnPageLoad({
      [setButCanceledFlag]: false,
      [addedFlagName]: true,
    });

    cy.visit("/");

    Synapse.featureFlag(setFlagName).should("be.true");
    Synapse.featureFlag(setButCanceledFlag).should("be.false");
    Synapse.featureFlag(addedFlagName).should("be.true");
  });
});

