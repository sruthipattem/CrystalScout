
from pathlib import Path

import pandas as pd
import joblib

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from matminer.featurizers.composition import ElementProperty


# Locate the saved model
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ML_models" / "crystalscout_extra_trees.joblib"

# Load the existing trained model once when the API starts
model_data = joblib.load(MODEL_PATH)

pipeline = model_data["pipeline"]
expected_features = model_data["feature_columns"]
if len(expected_features) != 139:
    raise RuntimeError(
        f"CrystalScout model must have 139 features; found {len(expected_features)}."
    )

# Initialize the Magpie featurizer
featurizer = ElementProperty.from_preset("magpie")


def predict_from_cif_content(cif_content: str):

    # 1. Read the uploaded CIF
    structure = Structure.from_str(cif_content, fmt="cif")
    composition = structure.composition

    # 2. Generate 132 Magpie composition features
    values = featurizer.featurize(composition)
    names = featurizer.feature_labels()

    if len(names) != 132 or len(values) != 132:
        raise RuntimeError(
            f"Expected 132 Magpie composition features; generated {len(values)}."
        )

    features = pd.DataFrame([values], columns=names)

    # 3. Extract the 7 structural features
    analyzer = SpacegroupAnalyzer(structure)

    structural_features = {
        "Space group #": analyzer.get_space_group_number(),
        "a": structure.lattice.a,
        "b": structure.lattice.b,
        "c": structure.lattice.c,
        "alpha": structure.lattice.alpha,
        "beta": structure.lattice.beta,
        "gamma": structure.lattice.gamma
    }

    for column, value in structural_features.items():
        features[column] = value

    if len(features.columns) != 139:
        raise RuntimeError(
            f"Expected 139 total model features; generated {len(features.columns)}."
        )

    # 4. Validate and arrange the 139 features
    missing = [
        col for col in expected_features
        if col not in features.columns
    ]

    if missing:
        raise ValueError(f"Missing model features: {missing}")

    X = features[expected_features]

    # 5. Predict using the existing Extra Trees model
    predicted_log10 = float(pipeline.predict(X)[0])
    predicted_conductivity = float(10 ** predicted_log10)

    return {
        "material": composition.reduced_formula,
        "model": model_data["model_name"],
        "total_features": len(expected_features),
        "structural_features": structural_features,
        "predicted_log10_conductivity": predicted_log10,
        "predicted_conductivity_S_cm": predicted_conductivity
    }
