const cifInput = document.getElementById("cifFile");
const dropArea = document.getElementById("dropArea");
const selectedFile = document.getElementById("selectedFile");
const message = document.getElementById("message");
const uploadButton = document.getElementById("uploadButton");
const predictionResult = document.getElementById("predictionResult");
const historyList = document.getElementById("historyList");
const historyEmpty = document.getElementById("historyEmpty");

const configuredApiUrl = document.querySelector('meta[name="crystalscout-api-url"]')?.content;
const apiBaseUrl = (configuredApiUrl || "http://127.0.0.1:8000").replace(/\/$/, "");
const maxCifSize = 25 * 1024 * 1024;

function setMessage(text, isError = false) {
    message.textContent = text;
    message.style.color = isError ? "#a32929" : "#16734a";
}

function showSelectedFile(file) {
    selectedFile.textContent = file ? `Selected file: ${file.name}` : "No file selected";
    message.textContent = "";
    predictionResult.hidden = true;
}

function formatValue(value, decimals = 3) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(decimals) : "Unavailable";
}

function displayPrediction(response) {
    const prediction = response.prediction;
    const structure = prediction.structural_features;

    document.getElementById("resultMaterial").textContent = prediction.material;
    document.getElementById("resultModel").textContent = prediction.model;
    document.getElementById("resultFeatureCount").textContent = prediction.total_features;
    document.getElementById("resultSpaceGroup").textContent = structure["Space group #"] ?? "Unavailable";
    document.getElementById("resultLattice").textContent =
        `${formatValue(structure.a)} Å, ${formatValue(structure.b)} Å, ${formatValue(structure.c)} Å`;
    document.getElementById("resultAngles").textContent =
        `${formatValue(structure.alpha, 2)}°, ${formatValue(structure.beta, 2)}°, ${formatValue(structure.gamma, 2)}°`;
    document.getElementById("resultLogConductivity").textContent =
        formatValue(prediction.predicted_log10_conductivity, 6);

    const conductivity = Number(prediction.predicted_conductivity_S_cm);
    document.getElementById("resultConductivity").textContent =
        Number.isFinite(conductivity) ? `${conductivity.toExponential(4)} S/cm` : "Unavailable";

    predictionResult.hidden = false;
    historyEmpty.hidden = true;
    const historyEntry = document.createElement("li");
    historyEntry.textContent = `${response.filename}: ${prediction.material} — ${conductivity.toExponential(4)} S/cm`;
    historyList.prepend(historyEntry);
}

async function uploadFile() {
    const file = cifInput.files[0];

    if (!file) {
        setMessage("Please select a CIF file first.", true);
        return;
    }

    if (!file.name.toLowerCase().endsWith(".cif")) {
        setMessage("Please choose a file with the .cif extension.", true);
        return;
    }

    if (file.size === 0) {
        setMessage("The selected file is empty. Choose a CIF file with content.", true);
        return;
    }

    if (file.size > maxCifSize) {
        setMessage("CIF files must be 25 MB or smaller.", true);
        return;
    }

    uploadButton.disabled = true;
    uploadButton.textContent = "Predicting…";
    setMessage("Uploading CIF and calculating conductivity…");

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${apiBaseUrl}/predict-cif`, {
            method: "POST",
            body: formData,
        });
        const payload = await response.json().catch(() => ({}));

        if (!response.ok) {
            const detail = typeof payload.detail === "string"
                ? payload.detail
                : "The API could not process this CIF file.";
            throw new Error(detail);
        }

        if (!payload.success || !payload.prediction) {
            throw new Error("The API response did not contain a prediction.");
        }

        displayPrediction(payload);
        setMessage("Prediction complete.");
    } catch (error) {
        setMessage(
            error instanceof TypeError
                ? "Could not reach the CrystalScout API. Check that the backend is running and the API URL is correct."
                : error.message,
            true,
        );
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "Predict conductivity";
    }
}

cifInput.addEventListener("change", () => showSelectedFile(cifInput.files[0]));

dropArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropArea.classList.add("drag-over");
});

dropArea.addEventListener("dragleave", () => dropArea.classList.remove("drag-over"));

dropArea.addEventListener("drop", (event) => {
    event.preventDefault();
    dropArea.classList.remove("drag-over");

    if (event.dataTransfer.files.length > 0) {
        cifInput.files = event.dataTransfer.files;
        showSelectedFile(cifInput.files[0]);
    }
});

uploadButton.addEventListener("click", uploadFile);
