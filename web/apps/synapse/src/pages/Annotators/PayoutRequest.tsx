import React from "react";
import { PayoutPage } from "../Payout";

/**
 * Annotator Payout wrapper - uses shared PayoutPage with annotator config
 */
export const AnnotatorPayoutPage: React.FC = () => {
  return (
    <PayoutPage
      userType="annotator"
      backRoute="/annotators/earnings"
      loginRoute="/annotators/login"
    />
  );
};

// Keep PayoutRequest as an alias for backwards compatibility
export const PayoutRequest = AnnotatorPayoutPage;

export default AnnotatorPayoutPage;
