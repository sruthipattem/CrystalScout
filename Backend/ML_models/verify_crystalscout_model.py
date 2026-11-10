"""Check that the saved CrystalScout model accepts its expected input shape.

The all-zero row below is a software smoke test only. It does not represent a
real material and its prediction must not be interpreted scientifically.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd


MODEL_PATH = Path(__file__).resolve().with_name("crystalscout_extra_trees.joblib")


def main():
    saved_data = joblib.load(MODEL_PATH)
    model = saved_data["pipeline"]
    feature_columns = saved_data["feature_columns"]

    print("Model:", saved_data.get("model_name", "Unknown"))
    print("Pipeline steps:", [name for name, _ in model.steps])
    print("Expected feature count:", len(feature_columns))

    if len(feature_columns) != 139:
        raise ValueError(
            "Expected 139 feature columns, found " + str(len(feature_columns))
        )

    # Placeholder values test pipeline execution only; they are not a material.
    test_input = pd.DataFrame(
        [np.zeros(len(feature_columns))],
        columns=feature_columns,
    )

    log10_prediction = model.predict(test_input)[0]
    conductivity_s_cm = 10 ** log10_prediction

    print("Input shape:", test_input.shape)
    print("Predicted log10 conductivity (smoke test):", log10_prediction)
    print("Converted conductivity in S/cm (smoke test):", conductivity_s_cm)
    print("Note: the placeholder input is not a scientifically valid material.")


if __name__ == "__main__":
    main()
