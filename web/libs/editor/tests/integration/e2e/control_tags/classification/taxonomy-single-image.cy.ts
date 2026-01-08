import { Synapse, ImageView, Taxonomy } from "@synapse/frontend-test/helpers/SF";
import { simpleImageTaxonomyConfig, simpleImageData, perTagTaxonomyResult } from "../../../data/control_tags/per-item";
import { commonBeforeEach } from "./common";

beforeEach(commonBeforeEach);

/* <Taxonomy /> */
describe("Classification - single image - Taxonomy", () => {
  it("should create result without item_index", () => {
    Synapse.params().config(simpleImageTaxonomyConfig).data(simpleImageData).withResult([]).init();

    ImageView.waitForImage();

    Taxonomy.open();
    Taxonomy.findItem("Choice 2").click();
    Taxonomy.close();

    Synapse.serialize().then((result) => {
      expect(result[0]).not.to.haveOwnProperty("item_index");
    });
  });

  it("should load perTag result correctly", () => {
    Synapse.params()
      .config(simpleImageTaxonomyConfig)
      .data(simpleImageData)
      .withResult(perTagTaxonomyResult)
      .init();

    ImageView.waitForImage();

    Taxonomy.hasSelected("Choice 1");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.deep.include(perTagTaxonomyResult[0]);
      expect(result[0]).not.to.haveOwnProperty("item_index");
    });
  });
});

