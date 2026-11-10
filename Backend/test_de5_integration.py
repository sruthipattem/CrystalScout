"""Real HTTP integration checks using the deployed FastAPI app and model.

Start the API, then run from Backend:
    python test_de5_integration.py
The test uploads Backend/test_data/de5.cif and uses no prediction mocks.
"""

import json
import math
import os
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path


API_URL = os.getenv("CRYSTALSCOUT_API_URL", "http://127.0.0.1:8000").rstrip("/")
DE5_CIF = Path(__file__).resolve().parent / "test_data" / "de5.cif"


def api_request(path, method="GET", body=None, headers=None):
    request = urllib.request.Request(
        API_URL + path,
        data=body,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        response_text = error.read().decode("utf-8", errors="replace")
        try:
            response_body = json.loads(response_text)
        except json.JSONDecodeError:
            response_body = {"detail": response_text or "No error detail returned."}
        return error.code, response_body
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError(
            f"Could not reach CrystalScout API at {API_URL}. Start the API and "
            "check its startup logs for missing ML dependencies or a model-loading error. "
            f"Underlying error: {error}"
        ) from error


def multipart_upload(filename, content):
    boundary = "----CrystalScout" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("ascii")
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


class CrystalScoutHTTPIntegration(unittest.TestCase):
    def test_root(self):
        status, body = api_request("/")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "online")

    def test_health(self):
        status, body = api_request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "healthy")

    def test_rejects_invalid_extension(self):
        body, headers = multipart_upload("material.txt", b"not a CIF")
        status, response = api_request("/predict-cif", "POST", body, headers)
        self.assertEqual(status, 400)
        self.assertIn("CIF", response["detail"])

    def test_rejects_empty_cif(self):
        body, headers = multipart_upload("empty.cif", b"")
        status, response = api_request("/predict-cif", "POST", body, headers)
        self.assertEqual(status, 400)
        self.assertIn("empty", response["detail"].lower())

    def test_de5_real_model_prediction(self):
        cif_path = DE5_CIF
        self.assertTrue(cif_path.is_file(), f"CIF file not found: {cif_path}")
        body, headers = multipart_upload(cif_path.name, cif_path.read_bytes())
        status, response = api_request("/predict-cif", "POST", body, headers)

        self.assertEqual(
            status,
            200,
            f"POST /predict-cif failed with HTTP {status}: "
            f"{response.get('detail', response)}. Check API startup/model loading "
            "and CIF parsing logs.",
        )
        self.assertTrue(response["success"])
        self.assertEqual(response["filename"], cif_path.name)

        prediction = response["prediction"]
        self.assertEqual(prediction["material"], "Li6In2.03Cl12")
        self.assertEqual(prediction["model"], "Extra Trees Regressor")
        self.assertEqual(prediction["total_features"], 139)
        self.assertAlmostEqual(
            prediction["predicted_log10_conductivity"],
            -6.292493199044514,
            places=8,
        )
        self.assertTrue(
            math.isclose(
                prediction["predicted_conductivity_S_cm"],
                5.099255828341376e-07,
                rel_tol=1e-6,
            )
        )
        self.assertTrue(
            math.isfinite(prediction["predicted_conductivity_S_cm"])
            and prediction["predicted_conductivity_S_cm"] > 0,
            "Model response must contain a finite positive real conductivity.",
        )
        self.assertEqual(set(prediction["structural_features"]), {
            "Space group #", "a", "b", "c", "alpha", "beta", "gamma"
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
