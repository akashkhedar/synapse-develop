import { Synapse, Sidebar, Tooltip } from "@synapse/frontend-test/helpers/SF/index";
import { simpleRegionsConfig, simpleRegionsData, simpleRegionsResult } from "../../data/outliner/hide-all";

describe("Outliner - Hide all regions", () => {
  it("should exist", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.hideAllRegionsButton.should("be.visible").should("be.enabled");
  });

  it("should be disabled without existed regions", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult([]).init();

    Sidebar.hasRegions(0);
    Sidebar.hideAllRegionsButton.should("be.visible").should("be.disabled");
  });

  it("should hide all regions", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.hasHiddenRegion(0);
    Sidebar.hideAllRegionsButton.click();
    Sidebar.hasHiddenRegion(3);
  });

  it("should show all regions", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.hideAllRegionsButton.click();
    Sidebar.hasHiddenRegion(3);
    Sidebar.showAllRegionsButton.click();
    Sidebar.hasHiddenRegion(0);
  });

  it("should hide rest regions", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.toggleRegionVisibility(1);
    Sidebar.hasHiddenRegion(1);
    Sidebar.hideAllRegionsButton.click();
    Sidebar.hasHiddenRegion(3);
  });

  it("should hide all regions except the target region by ID from param", () => {
    Synapse.params()
      .config(simpleRegionsConfig)
      .data(simpleRegionsData)
      .withResult(simpleRegionsResult)
      .withParam("region", "label_2")
      .init();

    cy.window().then((window: any | unknown) => {
      window.Htx.annotationStore.annotations[0].regionStore.setRegionVisible(window.SF_CONFIG.region);
    });

    Sidebar.hasRegions(3);
    Sidebar.hasHiddenRegion(2);

    Sidebar.assertRegionHidden(0, "Label 1", true);
    Sidebar.assertRegionHidden(1, "Label 2", false);
    Sidebar.assertRegionHidden(2, "Label 3", true);
  });

  it("should hide all regions except the target region by ID within the targeted annotation tab specified by param", () => {
    Synapse.params()
      .config(simpleRegionsConfig)
      .data(simpleRegionsData)
      .withAnnotation({ id: "10", result: simpleRegionsResult })
      .withAnnotation({ id: "20", result: simpleRegionsResult })
      .withParam("annotation", "10")
      .withParam("region", "label_2")
      .init();

    cy.window().then((window: any | unknown) => {
      const annIdFromParam = window.SF_CONFIG.annotation;
      const annotations = window.Htx.annotationStore.annotations;
      const sfAnnotation = annotations.find((ann: any) => ann.pk === annIdFromParam || ann.id === annIdFromParam);
      const annID = sfAnnotation.pk ?? sfAnnotation.id;

      expect(annID).to.equal("10");

      // Move to the annotation tab specified by param
      cy.get('[class="sf-annotations-list__toggle"]').click();
      cy.get('[class="sf-annotations-list__entity-id"]').contains("10").click();

      annotations[1].regionStore.setRegionVisible(window.SF_CONFIG.region);
    });

    Sidebar.hasRegions(3);
    Sidebar.hasHiddenRegion(2);

    Sidebar.assertRegionHidden(0, "Label 1", true);
    Sidebar.assertRegionHidden(1, "Label 2", false);
    Sidebar.assertRegionHidden(2, "Label 3", true);
  });

  it("should not hide regions in the non-targeted annotaion tab", () => {
    Synapse.params()
      .config(simpleRegionsConfig)
      .data(simpleRegionsData)
      .withAnnotation({ id: "10", result: simpleRegionsResult })
      .withAnnotation({ id: "20", result: simpleRegionsResult })
      .withParam("annotation", "10")
      .withParam("region", "label_2")
      .init();

    cy.window().then((window: any | unknown) => {
      window.Htx.annotationStore.annotations[1].regionStore.setRegionVisible(window.SF_CONFIG.region);
    });

    // Validate the annotation tab
    cy.get('[class="sf-annotations-list__entity-id"]').should("contain.text", "20");

    Sidebar.hasRegions(3);
    Sidebar.hasHiddenRegion(0);
  });

  it("should select the target region by ID from param", () => {
    Synapse.params()
      .config(simpleRegionsConfig)
      .data(simpleRegionsData)
      .withResult(simpleRegionsResult)
      .withParam("region", "label_2")
      .init();

    cy.window().then((window: any | unknown) => {
      window.Htx.annotationStore.annotations[0].regionStore.selectRegionByID(window.SF_CONFIG.region);
    });

    Sidebar.hasRegions(3);
    Sidebar.hasSelectedRegions(1);
    Sidebar.hasSelectedRegion(1);
  });

  it("should have tooltip for hide action", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.hideAllRegionsButton.trigger("mouseover");
    Tooltip.hasText("Hide all regions");
  });

  it("should have tooltip for show action", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.hideAllRegionsButton.click();
    Sidebar.showAllRegionsButton.trigger("mouseover");
    Tooltip.hasText("Show all regions");
  });

  it("should react to changes in regions' visibility", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);
    Sidebar.hideAllRegionsButton.click();

    Sidebar.showAllRegionsButton.should("be.visible");
    Sidebar.toggleRegionVisibility(1);
    Sidebar.hideAllRegionsButton.should("be.visible");
  });

  it("should toggle visibility when its grouped by tool ", () => {
    Synapse.params().config(simpleRegionsConfig).data(simpleRegionsData).withResult(simpleRegionsResult).init();

    Sidebar.hasRegions(3);

    cy.get('[data-testid="grouping-manual"]').click();
    cy.wait(500);
    cy.contains("Group by Tool").click({ force: true });
    Sidebar.toggleRegionVisibility(0);
    Sidebar.hasHiddenRegion(3);
  });
});

