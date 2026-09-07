export const releaseStatus = {
  demo: "DEMO — SYNTHETIC DATA",
  engineeringFixture: "ENGINEERING_FIXTURE",
  internalLive: "INTERNAL_LIVE",
  partialLiveAbstain: "PARTIAL_LIVE — ABSTAIN",
  holdoutForwardRequired: "HOLDOUT VALIDATED — FORWARD REQUIRED",
  forwardInProgress: "FORWARD VALIDATION IN PROGRESS",
  predictivelyValidated: "PREDICTIVELY VALIDATED",
  insufficient: "INSUFFICIENT_EVIDENCE",
  unknown: "UNKNOWN",
  stale: "STALE",
  unavailable: "UNAVAILABLE",
} as const;
