import React from "react";
import { PayoutPage } from "../Payout";

/**
 * Expert Payout page - uses shared PayoutPage with expert config
 */
export const ExpertPayoutPage: React.FC = () => {
  return (
    <PayoutPage
      userType="expert"
      backRoute="/expert/earnings"
      loginRoute="/annotators/login"
    />
  );
};

export default ExpertPayoutPage;
