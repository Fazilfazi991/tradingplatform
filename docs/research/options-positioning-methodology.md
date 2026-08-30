# Options Positioning Methodology

Option chains are point-in-time, underlying- and expiry-specific. Duplicate contract records collapse to
their latest available observation while raw provenance remains upstream. A complete engineering chain
requires calls, puts, spot and at least three strikes.

Volume PCR, OI PCR and change-in-OI PCR equal aggregate put measure divided by the corresponding call
measure; zero denominators return unknown. No PCR value is bullish or bearish by definition.

Skew compares average put and call IV for the selected chain and reports downside-rich, upside-rich,
balanced, extreme or unknown. OI concentration reports top strikes as
`POSITIONING_REFERENCE_NOT_PRICE_BARRIER`; it does not create support or resistance predictions. IV,
term structure, Greeks and corporate-action adjustments require explicit source/methodology provenance.
