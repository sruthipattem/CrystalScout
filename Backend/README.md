# CrystalScout Backend

FastAPI service for predicting ionic conductivity from an uploaded CIF file.

## Run locally

From the `Backend` directory, create and activate a virtual environment, install
the dependencies, then start the API:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Serve the frontend over HTTP (for example, from `Frontend` run
`py -m http.server 5500`) and open `http://127.0.0.1:5500/index.html`. The login
page is a frontend demonstration and accepts any non-empty password with a
valid email format.

The trained artifact must be present at
`ML_models/crystalscout_extra_trees.joblib`. The service loads this existing
artifact at startup; it does not train a model.

## API

- `GET /` reports that the API is online.
- `GET /health` reports service health.
- `POST /predict-cif` accepts multipart form data with a `.cif` file in the
  `file` field. A successful response contains the material formula, model,
  feature count, predicted log10 conductivity, and conductivity in S/cm.
- `GET /docs` provides the interactive OpenAPI interface.

By default, CORS allows the local frontend origins on ports 5500 and 5501.
Set `CRYSTALSCOUT_CORS_ORIGINS` to a comma-separated list of allowed origins
when hosting the frontend elsewhere. In `Frontend/dashboard.html`, set the
`crystalscout-api-url` meta tag to the deployed API base URL, without a trailing
slash. For example:

```powershell
$env:CRYSTALSCOUT_CORS_ORIGINS = "https://crystalscout-frontend.onrender.com"
```

Keep the scikit-learn version at 1.6.1 to match the environment used to train
and serialize the model. `.python-version` selects Python 3.12.11 for Render.

## Real de5.cif integration test

This test calls a running API and uses its loaded model; it does not mock
prediction. It uploads `Backend/test_data/de5.cif` directly. Start the backend,
then run the test from the `Backend` directory:

```powershell
python test_de5_integration.py
```

The test checks the health routes, invalid and empty uploads, and the known
de5.cif formula and prediction. Set `CRYSTALSCOUT_API_URL` only when the API is
running somewhere other than `http://127.0.0.1:8000`.

## Render settings

Create a Python Web Service for the backend:

- Root Directory: `Backend`
- Runtime: Python 3 (version selected by `.python-version`)
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`
- Environment variable `CRYSTALSCOUT_CORS_ORIGINS`: the exact public origin of
  the deployed frontend, such as `https://crystalscout-frontend.onrender.com`

Create a Static Site for the frontend:

- Root Directory: `Frontend`
- Build Command: leave empty (the frontend is static HTML/CSS/JavaScript)
- Publish Directory: `.`
- Set the `crystalscout-api-url` meta tag in `dashboard.html` to the public API
  URL, then publish the frontend.

Use the actual `onrender.com` URLs assigned to your services in both settings.
Render's service settings can change as services are created; the configuration
above follows its current [FastAPI deployment](https://render.com/docs/deploy-fastapi),
[Python version](https://render.com/docs/python-version), and
[static site](https://render.com/docs/static-sites) guidance.
