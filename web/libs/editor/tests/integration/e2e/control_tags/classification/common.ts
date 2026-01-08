import { Synapse } from "@synapse/frontend-test/helpers/SF";
import { FF_LSDV_4583 } from "../../../../../src/utils/feature-flags";

export const commonBeforeEach = () => {
  Synapse.addFeatureFlagsOnPageLoad({
    [FF_LSDV_4583]: true,
  });
};

