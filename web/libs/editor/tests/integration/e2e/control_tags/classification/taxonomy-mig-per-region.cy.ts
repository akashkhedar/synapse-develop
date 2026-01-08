import { Synapse, ImageView, Taxonomy, ToolBar, Modals, Sidebar } from "@synapse/frontend-test/helpers/SF";
import {
  simpleMIGData,
  TAXONOMY_REQUIRED_WARNING,
  perRegionMIGTaxonomyConfig,
  perRegionRegionsResult,
  perRegionTaxonomyResult,
  requiredPerRegionMIGTaxonomyConfig,
} from "../../../data/control_tags/per-item";
import { commonBeforeEach } from "./common";

beforeEach(commonBeforeEach);

/* <Taxonomy /> */
describe("Control Tags - MIG perRegion - Taxonomy", () => {
  it("should create result with item_index", () => {
    Synapse.params()
      .config(perRegionMIGTaxonomyConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();
    Sidebar.hasRegions(2);

    Sidebar.findRegionByIndex(0).click();

    Taxonomy.open();
    Taxonomy.findItem("Choice 1").click();
    Taxonomy.close();

    Synapse.serialize().then((result) => {
      expect(result.length).to.be.eq(3);
      expect(result[1]).to.include({
        type: "taxonomy",
        item_index: 0,
      });
    });
  });

  it("should load result correctly", () => {
    Synapse.params()
      .config(perRegionMIGTaxonomyConfig)
      .data(simpleMIGData)
      .withResult(perRegionTaxonomyResult)
      .init();

    ImageView.waitForImage();
    Sidebar.hasRegions(2);

    Sidebar.findRegionByIndex(0).click();

    Taxonomy.hasSelected("Choice 2");

    Synapse.serialize().then((result) => {
      const { value, ...expectedResult } = perRegionTaxonomyResult[1];

      expect(result.length).to.be.eq(3);
      expect(result[1]).to.deep.include(expectedResult);
      expect(result[1].value.taxonomy).to.be.deep.eq(value.taxonomy);
    });
  });

  it("should require result", () => {
    Synapse.params()
      .config(requiredPerRegionMIGTaxonomyConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    ToolBar.updateBtn.click();
    Modals.hasWarning(TAXONOMY_REQUIRED_WARNING);
  });

  it("should require result for other region too", () => {
    Synapse.params()
      .config(requiredPerRegionMIGTaxonomyConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    Sidebar.findRegionByIndex(0).click();
    Taxonomy.open();
    Taxonomy.findItem("Choice 1").click();

    ToolBar.updateBtn.click();
    Modals.hasWarning(TAXONOMY_REQUIRED_WARNING);
  });

  it("should not require result if there are all of them", () => {
    Synapse.params()
      .config(requiredPerRegionMIGTaxonomyConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    Sidebar.findRegionByIndex(0).click();
    Taxonomy.open();
    Taxonomy.findItem("Choice 1").click();

    Sidebar.findRegionByIndex(1).click();
    ImageView.waitForImage();
    Taxonomy.open();
    Taxonomy.findItem("Choice 2").click();

    ToolBar.updateBtn.click();
    Modals.hasNoWarnings();
  });
});

