import { Choices, Synapse, Tooltip } from "@synapse/frontend-test/helpers/SF";
import {
  choicesConfig,
  choicesMultipleSelectionConfig,
  choicesSelectLayoutConfig,
  simpleData,
} from "../../data/control_tags/choice";
import { FF_DEV_2007 } from "@synapse/frontend-test/feature-flags";

describe("Control Tags - Choice", () => {
  describe("Old version", () => {
    beforeEach(() => {
      Synapse.addFeatureFlagsOnPageLoad({
        [FF_DEV_2007]: false,
      });
    });

    it('should show hint for <Choice /> when choice="single"', () => {
      Synapse.params().config(choicesConfig).data(simpleData).withResult([]).init();

      Choices.findChoice("Choice 2").trigger("mouseover");
      Tooltip.hasText("A hint for Choice 2");
    });
    it('should show hint for <Choice /> when choice="multiple"', () => {
      Synapse.params().config(choicesMultipleSelectionConfig).data(simpleData).withResult([]).init();

      Choices.findChoice("Choice 2").trigger("mouseover");
      Tooltip.hasText("A hint for Choice 2");
    });
    it('should show hint for <Choice /> when layout="select"', () => {
      Synapse.params().config(choicesSelectLayoutConfig).data(simpleData).withResult([]).init();

      Choices.toggleSelect();
      Choices.findOption("Choice 2").trigger("mouseover", { force: true });
      Tooltip.hasText("A hint for Choice 2");
    });
  });

  describe("New version", () => {
    beforeEach(() => {
      Synapse.addFeatureFlagsOnPageLoad({
        [FF_DEV_2007]: true,
      });
    });

    it("should show hint for <Choise />", () => {
      Synapse.params().config(choicesConfig).data(simpleData).withResult([]).init();

      Choices.findChoice("Choice 2").trigger("mouseover");
      Tooltip.hasText("A hint for Choice 2");
    });

    it("should show hint for <Choise />", () => {
      Synapse.params().config(choicesMultipleSelectionConfig).data(simpleData).withResult([]).init();

      Choices.findChoice("Choice 2").trigger("mouseover");
      Tooltip.hasText("A hint for Choice 2");
    });
  });
});

