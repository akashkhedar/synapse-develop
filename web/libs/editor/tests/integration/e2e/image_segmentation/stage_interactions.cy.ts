import { ImageView, Synapse, Sidebar } from "@synapse/frontend-test/helpers/SF";
import { Hotkeys } from "@synapse/frontend-test/helpers/SF/Hotkeys";
import { imageData, imageToolsConfig } from "../../data/image_segmentation/stage_interactions";
import { TWO_FRAMES_TIMEOUT } from "../utils/constants";

beforeEach(() => {
  Synapse.addFeatureFlagsOnPageLoad({
    fflag_fix_front_leap_32_zoom_perf_190923_short: true,
    fflag_fix_front_dev_3793_relative_coords_short: true,
  });
});

describe("Image Segmentation Stage Interactions", () => {
  it("should not be able to draw outside of image's boundaries", () => {
    Synapse.params().config(imageToolsConfig).data(imageData).withResult([]).init();
    Synapse.waitForObjectsReady();

    // Check all interactions at space between

    ImageView.selectRectangleToolByButton();
    // two clicks
    ImageView.clickAtRelative(1.1, 0.4);
    ImageView.clickAtRelative(1.3, 0.5);
    // drag and drop
    ImageView.drawRectRelative(1.1, 0.4, 0.2, 0.2);
    // dblclick
    ImageView.dblClickAtRelative(1.1, 0.4);

    ImageView.selectEllipseToolByButton();
    // two clicks
    ImageView.clickAtRelative(1.1, 0.4);
    ImageView.clickAtRelative(1.3, 0.5);
    // drag and drop
    ImageView.drawRectRelative(1.1, 0.4, 0.2, 0.2);
    // dblclick
    ImageView.dblClickAtRelative(1.1, 0.4);

    ImageView.selectPolygonToolByButton();
    // draw triangle
    ImageView.drawPolygonRelative(
      [
        [1.1, 0.4],
        [1.3, 0.5],
        [1.1, 0.6],
      ],
      true,
    );
    // dblclick
    ImageView.dblClickAtRelative(1.1, 0.4);

    ImageView.selectKeypointToolByButton();
    // click
    ImageView.clickAtRelative(1.1, 0.4);

    ImageView.selectBrushToolByButton();
    // click
    ImageView.clickAtRelative(1.1, 0.4);
    // draw
    ImageView.drawRectRelative(1.1, 0.4, 0.2, 0.2);

    Sidebar.hasRegions(0);
  });

  it("should be able to draw outside of initial image boundaries after zoom (Rectangle)", () => {
    Synapse.params().config(imageToolsConfig).data(imageData).withResult([]).init();
    Synapse.waitForObjectsReady();

    for (let i = 0; i < 10; i++) {
      ImageView.zoomInWithHotkey();
    }

    ImageView.selectRectangleToolByButton();
    // two clicks
    ImageView.clickAtRelative(0.8, 0.1);
    ImageView.clickAtRelative(0.9, 0.2);
    Sidebar.hasRegions(1);
    // drag and drop
    ImageView.drawRectRelative(0.8, 0.3, 0.1, 0.1);
    Sidebar.hasRegions(2);
    // dblclick
    ImageView.dblClickAtRelative(0.8, 0.5);
    Sidebar.hasRegions(3);
  });
  it("should be able to draw outside of initial image boundaries after zoom (Ellipse)", () => {
    Synapse.params().config(imageToolsConfig).data(imageData).withResult([]).init();
    Synapse.waitForObjectsReady();

    for (let i = 0; i < 10; i++) {
      ImageView.zoomInWithHotkey();
    }

    ImageView.selectEllipseToolByButton();
    // two clicks
    ImageView.clickAtRelative(0.8, 0.1);
    ImageView.clickAtRelative(0.9, 0.2);
    Sidebar.hasRegions(1);
    // drag and drop
    ImageView.drawRectRelative(0.8, 0.3, 0.1, 0.1);
    Sidebar.hasRegions(2);
    // dblclick
    ImageView.dblClickAtRelative(0.8, 0.5);
    Sidebar.hasRegions(3);
  });
  it("should be able to draw outside of initial image boundaries after zoom (Polygon)", () => {
    Synapse.params().config(imageToolsConfig).data(imageData).withResult([]).init();
    Synapse.waitForObjectsReady();

    for (let i = 0; i < 10; i++) {
      ImageView.zoomInWithHotkey();
    }

    ImageView.selectPolygonToolByButton();
    // draw triangle
    ImageView.drawPolygonRelative(
      [
        [0.8, 0.1],
        [0.9, 0.2],
        [0.8, 0.3],
      ],
      false,
    );
    cy.wait(TWO_FRAMES_TIMEOUT); // Two frames to be sure
    ImageView.clickAtRelative(0.8, 0.1);
    Sidebar.hasRegions(1);
    // dblclick
    ImageView.dblClickAtRelative(0.8, 0.4);
    Sidebar.hasRegions(2);
  });
  it("should be able to draw outside of initial image boundaries after zoom (KeyPoint)", () => {
    Synapse.params().config(imageToolsConfig).data(imageData).withResult([]).init();
    Synapse.waitForObjectsReady();

    for (let i = 0; i < 10; i++) {
      ImageView.zoomInWithHotkey();
    }

    ImageView.selectKeypointToolByButton();
    // click
    ImageView.clickAtRelative(0.8, 0.4);
    Sidebar.hasRegions(1);
  });
  it("should be able to draw outside of initial image boundaries after zoom (Brush)", () => {
    Synapse.params().config(imageToolsConfig).data(imageData).withResult([]).init();
    Synapse.waitForObjectsReady();

    for (let i = 0; i < 10; i++) {
      ImageView.zoomInWithHotkey();
    }

    ImageView.selectBrushToolByButton();
    // click
    ImageView.clickAtRelative(0.8, 0.1);
    Sidebar.hasRegions(1);
    // draw
    Hotkeys.unselectAllRegions();
    ImageView.drawRectRelative(0.8, 0.4, 0.1, 0.2);
    Sidebar.hasRegions(2);
  });
});

