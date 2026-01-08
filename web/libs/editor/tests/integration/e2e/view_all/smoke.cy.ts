import { FF_DEV_3391 } from "@synapse/frontend-test/feature-flags";
import { Synapse } from "@synapse/frontend-test/helpers/SF";
import { FF_LSDV_4583 } from "../../../../src/utils/feature-flags";
import { allTagsSampleData, configAllTags } from "../../data/view_all/smoke";

beforeEach(() => {
  Synapse.addFeatureFlagsOnPageLoad({
    [FF_DEV_3391]: true,
    [FF_LSDV_4583]: true,
  });
});

describe("View All Interactive - Smoke test", () => {
  it("Should render", () => {
    Synapse.params().config(configAllTags).data(allTagsSampleData).withResult([]).init();

    // @TODO: Check more things
  });
});

