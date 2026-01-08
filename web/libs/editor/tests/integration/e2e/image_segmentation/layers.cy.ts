import { ImageView, Synapse, Sidebar } from "@synapse/frontend-test/helpers/SF";
import { simpleConfig, simpleImageData, simpleResult } from "../../data/image_segmentation/layers";

describe("Image Segmentation - Layers", () => {
  it("should keep selected region over unselected one", () => {
    Synapse.params().config(simpleConfig).data(simpleImageData).withResult(simpleResult).init();

    ImageView.waitForImage();
    Sidebar.hasRegions(2);
    Sidebar.toggleRegionSelection(0);

    Sidebar.hasSelectedRegions(1);

    // A selected region should be over all unselected regions,
    // so the test should click in it and clear selection
    ImageView.clickAtRelative(0.5, 0.5);

    Sidebar.hasSelectedRegions(0);
  });
});

