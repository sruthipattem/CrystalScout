
import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.ml_service import predict_from_cif_content

app = FastAPI(
    title="CrystalScout API",
    description="CIF-based ionic conductivity prediction",
    version="1.0.0"
)

MAX_CIF_SIZE_BYTES = 25 * 1024 * 1024

# Allow the existing frontend to communicate with the API
default_origins = (
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CRYSTALSCOUT_CORS_ORIGINS", ",".join(default_origins)).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def home():
    return {
        "message": "CrystalScout API is running",
        "status": "online"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict-cif")
async def predict_cif(file: UploadFile = File(...)):

    filename = file.filename or ""
    if not filename.lower().endswith(".cif"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid CIF file."
        )

    try:
        content = await file.read(MAX_CIF_SIZE_BYTES + 1)

        if len(content) > MAX_CIF_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="CIF file is too large. Maximum size is 25 MB.",
            )

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # CIF text is commonly UTF-8; utf-8-sig also handles a BOM from editors.
        try:
            cif_content = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise HTTPException(
                status_code=400,
                detail="CIF file must contain UTF-8 text.",
            ) from error

        result = predict_from_cif_content(cif_content)

        return {
            "success": True,
            "filename": filename,
            "prediction": result
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail="CIF processing failed. Check that the file contains a valid crystal structure.",
        ) from error
    finally:
        await file.close()
