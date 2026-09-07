export type ContentClass = "SYNTHETIC_DEMO" | "INTERNAL_LIVE" | "INTERNAL_RESEARCH";
export type RightsState = "PUBLIC_APPROVED" | "NOT_APPROVED" | "REVIEW_REQUIRED";
export type ValidationState =
  | "DEMO_SYNTHETIC"
  | "HOLDOUT_VALIDATED_FORWARD_REQUIRED"
  | "FORWARD_VALIDATION_IN_PROGRESS"
  | "PREDICTIVELY_VALIDATED";

export type DeliveryEnvelope<T> = Readonly<{
  contentClass: ContentClass;
  rightsState: RightsState;
  validationState: ValidationState;
  stale: boolean;
  mixedFixtureAndLive: boolean;
  payload: T;
}>;

export class PublicDeliveryRejected extends Error {
  readonly reason: string;

  constructor(reason: string) {
    super(`Public delivery rejected: ${reason}`);
    this.name = "PublicDeliveryRejected";
    this.reason = reason;
  }
}

export function assertPublicDelivery<T>(envelope: DeliveryEnvelope<T>): T {
  if (envelope.mixedFixtureAndLive) throw new PublicDeliveryRejected("FIXTURE_LIVE_MIX");
  if (envelope.stale) throw new PublicDeliveryRejected("STALE_DATA");
  if (envelope.contentClass === "INTERNAL_RESEARCH") {
    throw new PublicDeliveryRejected("INTERNAL_RESEARCH");
  }
  if (envelope.rightsState !== "PUBLIC_APPROVED") {
    throw new PublicDeliveryRejected(`RIGHTS_${envelope.rightsState}`);
  }
  if (
    envelope.contentClass === "INTERNAL_LIVE"
    && envelope.validationState !== "PREDICTIVELY_VALIDATED"
  ) {
    throw new PublicDeliveryRejected("LIVE_PREDICTION_NOT_VALIDATED");
  }
  return envelope.payload;
}
