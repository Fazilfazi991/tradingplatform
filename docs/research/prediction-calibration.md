# Prediction calibration

V1 preregisters sigmoid and isotonic as candidates and selects sigmoid before holdout. Each class is calibrated one-vs-rest on the historical calibration slice, then normalized to a three-class distribution. Training rows never fit calibration and holdout rows never select or fit it.

Reports retain calibrated and uncalibrated multiclass Brier, log loss, ECE, and reliability information. Calibration that worsens the preregistered primary metrics is a rejection signal. `P(UP)=0.62` means an estimated probability for the defined UP class; it is neither “62% confidence” nor “62% chance of profit.”
