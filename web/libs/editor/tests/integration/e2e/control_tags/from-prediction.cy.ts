import {
  Choices,
  DateTime,
  Synapse,
  Number,
  Rating,
  Textarea,
  ToolBar,
  useTextarea,
} from "@synapse/frontend-test/helpers/SF";
import { Hotkeys } from "@synapse/frontend-test/helpers/SF/Hotkeys";
import { FF_DEV_3873 } from "../../../../src/utils/feature-flags";
import { allClassificationsConfig, prediction, textData } from "../../data/control_tags/from-prediction";

describe("Classification from prediction", () => {
  it('by default should have origin "prediction"', () => {
    Synapse.params().config(allClassificationsConfig).data(textData).withPrediction(prediction).init();
    Synapse.waitForObjectsReady();
    Synapse.serialize().then((results) => {
      for (const result of results) {
        expect(result.origin).to.equal("prediction");
      }
    });
  });

  it('should have origin "prediction-changed" after changing prediction', () => {
    const SecondTextarea = useTextarea("&:eq(1)");
    Synapse.addFeatureFlagsOnPageLoad({
      [FF_DEV_3873]: true,
    });
    Synapse.params().config(allClassificationsConfig).data(textData).withPrediction(prediction).init();
    Synapse.waitForObjectsReady();
    ToolBar.clickCopyAnnotationBtn();
    Synapse.waitForObjectsReady();
    Choices.findChoice("Choice 2").click();
    DateTime.type("1999-11-11T11:11:11.111Z");
    Number.type("123");
    Rating.setValue(2);
    Textarea.type("Some other text{Enter}");
    SecondTextarea.clickRowEdit(1);
    SecondTextarea.rowInput(1).dblclick();
    SecondTextarea.rowType(1, " longer at the end{Enter}");
    Synapse.serialize().then((results) => {
      for (const result of results) {
        expect(result.origin).to.equal(
          "prediction-changed",
          `Prediction origin was not updated for "${result.from_name}"`,
        );
      }
    });
  });

  it("should work correctly with undo", () => {
    const SecondTextarea = useTextarea("&:eq(1)");
    Synapse.addFeatureFlagsOnPageLoad({
      [FF_DEV_3873]: true,
    });
    Synapse.params().config(allClassificationsConfig).data(textData).withPrediction(prediction).init();
    Synapse.waitForObjectsReady();
    ToolBar.clickCopyAnnotationBtn();
    Synapse.waitForObjectsReady();
    Choices.findChoice("Choice 2").click();
    DateTime.type("1999-11-11T11:11:11.111Z");
    Number.type("1");
    Rating.setValue(2);
    Textarea.type("Some other text{Enter}");
    SecondTextarea.clickRowEdit(1);
    SecondTextarea.rowInput(1).dblclick();
    SecondTextarea.rowType(1, " longer at the end{Enter}");
    for (let i = 0; i < 6; i++) {
      Hotkeys.undo();
    }
    Synapse.serialize().then((results) => {
      for (const result of results) {
        expect(result.origin).to.equal("prediction");
      }
    });
  });
});

