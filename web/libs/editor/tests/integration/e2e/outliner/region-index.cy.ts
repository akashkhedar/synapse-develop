import { Labels, Synapse, Relations, Sidebar } from "@synapse/frontend-test/helpers/SF";
import { FF_DEV_3873 } from "../../../../src/utils/feature-flags";
import {
  Synapse_settings,
  panelState,
  resultWithRelations,
  simpleConfig,
  simpleData,
} from "../../data/outliner/region-index";
import { RichText } from "@synapse/frontend-test/helpers/SF/RichText";
import { Hotkeys } from "@synapse/frontend-test/helpers/SF/Hotkeys";

describe("Region Index", () => {
  beforeEach(() => {
    Synapse.addFeatureFlagsOnPageLoad({
      [FF_DEV_3873]: true,
    });
  });
  it("should be visible at the outliner", () => {
    Synapse.params().config(simpleConfig).data(simpleData).withResult(resultWithRelations).init();
    Synapse.waitForObjectsReady();

    Sidebar.findByRegionIndex(1).should("contain", "Label 1");
    Sidebar.findByRegionIndex(3).should("contain", "Label 3");
  });

  it("should depends on the order of the regions", () => {
    Synapse.params().config(simpleConfig).data(simpleData).withResult(resultWithRelations).init();
    Synapse.waitForObjectsReady();

    Sidebar.toggleOrderByTime();
    Sidebar.findByRegionIndex(1).should("contain", "Label 3");
    Sidebar.findByRegionIndex(3).should("contain", "Label 1");
  });

  it("should affect the labels on region on changing order", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .withLocalStorageItem("Synapse:settings", Synapse_settings)
      .init();

    Synapse.waitForObjectsReady();

    Sidebar.toggleOrderByTime();

    RichText.hasRegionWithLabel("1:Label 3");
    RichText.hasRegionWithLabel("2:Label 2");
    RichText.hasRegionWithLabel("3:Label 1");
  });

  it("should be displayed in region's label", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .localStorageItems({
        "Synapse:settings": Synapse_settings,
      })
      .init();

    RichText.hasRegionWithLabel("1:Label 1");
    RichText.hasRegionWithLabel("2:Label 2");
    RichText.hasRegionWithLabel("3:Label 3");
  });

  it("should not depend on the visibility of the region panel", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .localStorageItems({
        panelState,
        "Synapse:settings": Synapse_settings,
      })
      .init();
    Synapse.waitForObjectsReady();

    RichText.hasRegionWithLabel("1:Label 1");
    RichText.hasRegionWithLabel("2:Label 2");
    RichText.hasRegionWithLabel("3:Label 3");
  });

  it("should be displayed on relations panel", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .localStorageItems({
        panelState,
        "Synapse:settings": Synapse_settings,
      })
      .init();
    Synapse.waitForObjectsReady();

    Relations.relationRegions.eq(0).contains(".sf-detailed-region__index", "1").should("exist");
    Relations.relationRegions.eq(1).contains(".sf-detailed-region__index", "3").should("exist");
  });

  it("should be consistent on region delete / create", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .localStorageItems({
        panelState,
        "Synapse:settings": Synapse_settings,
      })
      .init();
    Synapse.waitForObjectsReady();

    RichText.hasRegionWithLabel("1:Label 1");
    RichText.hasRegionWithLabel("2:Label 2");
    RichText.hasRegionWithLabel("3:Label 3");

    RichText.findRegionWithLabel("2:Label 2").trigger("click");
    Hotkeys.deleteRegion();
    RichText.hasRegionWithLabel("1:Label 1");
    RichText.hasRegionWithLabel("2:Label 3");

    Labels.select("Label 2");
    RichText.selectText("is");
    RichText.hasRegionWithLabel("3:Label 2");
  });

  it("should be consistent on region delete / create with full list affected by change", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .localStorageItems({
        panelState,
        "Synapse:settings": Synapse_settings,
        "outliner:sort": "date",
        "outliner:sort-direction": "desc",
      })
      .init();
    Synapse.waitForObjectsReady();

    RichText.hasRegionWithLabel("3:Label 1");
    RichText.hasRegionWithLabel("2:Label 2");
    RichText.hasRegionWithLabel("1:Label 3");

    RichText.findRegionWithLabel("2:Label 2").trigger("click");
    Hotkeys.deleteRegion();
    RichText.hasRegionWithLabel("2:Label 1");
    RichText.hasRegionWithLabel("1:Label 3");

    Labels.select("Label 2");
    RichText.selectText("is");

    RichText.hasRegionWithLabel("3:Label 1");
    RichText.hasRegionWithLabel("2:Label 3");
    RichText.hasRegionWithLabel("1:Label 2");
  });

  it("should work with history traveling", () => {
    Synapse.params()
      .config(simpleConfig)
      .data(simpleData)
      .withResult(resultWithRelations)
      .localStorageItems({
        "Synapse:settings": Synapse_settings,
      })
      .init();
    Synapse.waitForObjectsReady();

    RichText.findRegionWithLabel("2:Label 2").trigger("click");
    Hotkeys.deleteRegion();

    cy.wait(1);
    Hotkeys.undo();
    cy.wait(1);
    Hotkeys.redo();
  });
});

