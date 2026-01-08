import { Synapse, ImageView, ToolBar, Number, Modals, Sidebar } from "@synapse/frontend-test/helpers/SF";
import {
  simpleImageNumberConfig,
  simpleImageData,
  perTagNumberResult,
  perTagMIGNumberConfig,
  simpleMIGData,
  requiredPerTagMIGNumberConfig,
  NUMBER_REQUIRED_WARNING,
  perRegionMIGNumberConfig,
  perRegionRegionsResult,
  perRegionNumberResult,
  requiredPerRegionMIGNumberConfig,
  perItemMIGNumberConfig,
  perItemNumberResult,
  requiredPerItemMIGNumberConfig,
} from "../../../data/control_tags/per-item";
import { commonBeforeEach } from "./common";

beforeEach(commonBeforeEach);

/* <Number /> */
describe("Classification - single image - Number", () => {
  it("should create result without item_index", () => {
    Synapse.params().config(simpleImageNumberConfig).data(simpleImageData).withResult([]).init();

    ImageView.waitForImage();

    Number.type("123");

    Synapse.serialize().then((result) => {
      expect(result[0]).not.to.haveOwnProperty("item_index");
    });
  });

  it("should load perTag result correctly", () => {
    Synapse.params().config(simpleImageNumberConfig).data(simpleImageData).withResult(perTagNumberResult).init();

    ImageView.waitForImage();

    Number.hasValue("123");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.deep.include(perTagNumberResult[0]);
      expect(result[0]).not.to.haveOwnProperty("item_index");
    });
  });
});
describe("Classification - MIG perTag - Number", () => {
  it("should not have item_index in result", () => {
    Synapse.params().config(perTagMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    Number.type("123");

    Synapse.serialize().then((result) => {
      expect(result[0]).not.to.haveOwnProperty("item_index");
    });
  });

  it("should load perTag result correctly", () => {
    Synapse.params().config(perTagMIGNumberConfig).data(simpleMIGData).withResult(perTagNumberResult).init();

    ImageView.waitForImage();

    Number.hasValue("123");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.deep.include(perTagNumberResult[0]);
      expect(result[0]).not.to.haveOwnProperty("item_index");
    });
  });

  it("should keep value between items", () => {
    Synapse.params().config(perTagMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    Number.type("123");
    Number.hasValue("123");

    ImageView.paginationNextBtn.click();

    Number.hasValue("123");
  });

  it("should require result", () => {
    Synapse.params().config(requiredPerTagMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    ToolBar.updateBtn.click();
    Modals.hasWarning(NUMBER_REQUIRED_WARNING);
  });

  it("should not require result if there is one", () => {
    Synapse.params().config(requiredPerTagMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    Number.type("123");

    ToolBar.updateBtn.click();
    Modals.hasNoWarnings();
  });
});
describe("Control Tags - MIG perRegion - Number", () => {
  it("should create result with item_index", () => {
    Synapse.params().config(perRegionMIGNumberConfig).data(simpleMIGData).withResult(perRegionRegionsResult).init();

    ImageView.waitForImage();
    Sidebar.hasRegions(2);

    Sidebar.findRegionByIndex(0).click();

    Number.type("123");

    Synapse.serialize().then((result) => {
      expect(result.length).to.be.eq(3);
      expect(result[1]).to.include({
        type: "number",
        item_index: 0,
      });
    });
  });

  it("should load result correctly", () => {
    Synapse.params().config(perRegionMIGNumberConfig).data(simpleMIGData).withResult(perRegionNumberResult).init();

    ImageView.waitForImage();
    Sidebar.hasRegions(2);

    Sidebar.findRegionByIndex(0).click();

    Number.hasValue("123");

    Synapse.serialize().then((result) => {
      const { value, ...expectedResult } = perRegionNumberResult[1];

      expect(result.length).to.be.eq(3);
      expect(result[1]).to.deep.include(expectedResult);
      expect(result[1].value.number).to.be.deep.eq(value.number);
    });
  });

  it("should require result", () => {
    Synapse.params()
      .config(requiredPerRegionMIGNumberConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    ToolBar.updateBtn.click();
    Modals.hasWarning(NUMBER_REQUIRED_WARNING);
  });

  it("should require result for other region too", () => {
    Synapse.params()
      .config(requiredPerRegionMIGNumberConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    Sidebar.findRegionByIndex(0).click();
    Number.type("123");

    ToolBar.updateBtn.click();
    Modals.hasWarning(NUMBER_REQUIRED_WARNING);
  });

  it("should not require result if there are all of them", () => {
    Synapse.params()
      .config(requiredPerRegionMIGNumberConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    Sidebar.findRegionByIndex(0).click();
    Number.type("123");

    Sidebar.findRegionByIndex(1).click();
    ImageView.waitForImage();
    Number.type("456");

    ToolBar.updateBtn.click();
    Modals.hasNoWarnings();
  });
});
describe("Control Tags - MIG perItem - Number", () => {
  it("should create result with item_index", () => {
    Synapse.params().config(perItemMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    Number.type("123");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.have.property("item_index", 0);
    });
  });

  it("should load perItem result correctly", () => {
    Synapse.params().config(perItemMIGNumberConfig).data(simpleMIGData).withResult(perItemNumberResult).init();

    ImageView.waitForImage();

    Number.hasValue("123");
    ImageView.paginationNextBtn.click();
    Number.hasValue("456");
    ImageView.paginationNextBtn.click();
    Number.hasValue("789");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.deep.include(perItemNumberResult[0]);
      expect(result[1]).to.deep.include(perItemNumberResult[1]);
      expect(result[2]).to.deep.include(perItemNumberResult[2]);
    });
  });

  it("should be able to create result for second item", () => {
    Synapse.params().config(perItemMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    ImageView.paginationNextBtn.click();
    ImageView.waitForImage();

    Number.type("456");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.have.property("item_index", 1);
    });
  });

  it("should be able to create more that one result", () => {
    Synapse.params().config(perItemMIGNumberConfig).data(simpleMIGData).withResult([]).init();

    ImageView.waitForImage();

    Number.type("123");

    ImageView.paginationNextBtn.click();
    ImageView.waitForImage();
    Number.type("456");

    ImageView.paginationNextBtn.click();
    ImageView.waitForImage();
    Number.type("789");

    Synapse.serialize().then((result) => {
      expect(result[0]).to.include({ item_index: 0 });
      expect(result[0]).to.nested.include({ "value.number": 123 });

      expect(result[1]).to.include({ item_index: 1 });
      expect(result[1]).to.nested.include({ "value.number": 456 });

      expect(result[2]).to.include({ item_index: 2 });
      expect(result[2]).to.nested.include({ "value.number": 789 });
    });
  });

  it("should require result", () => {
    Synapse.params()
      .config(requiredPerItemMIGNumberConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    ToolBar.updateBtn.click();
    Modals.hasWarning(NUMBER_REQUIRED_WARNING);
  });

  it("should require result for other region too", () => {
    Synapse.params()
      .config(requiredPerItemMIGNumberConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    Number.type("123");

    ToolBar.updateBtn.click();
    Modals.hasWarning(NUMBER_REQUIRED_WARNING);
  });

  it("should not require result if there are all of them", () => {
    Synapse.params()
      .config(requiredPerItemMIGNumberConfig)
      .data(simpleMIGData)
      .withResult(perRegionRegionsResult)
      .init();

    ImageView.waitForImage();

    Number.type("123");
    ImageView.paginationNextBtn.click();
    ImageView.waitForImage();

    Number.type("456");
    ImageView.paginationNextBtn.click();
    ImageView.waitForImage();

    Number.type("789");
    ImageView.paginationNextBtn.click();
    ImageView.waitForImage();

    Number.type("0");

    ToolBar.updateBtn.click();
    Modals.hasNoWarnings();
  });
});

