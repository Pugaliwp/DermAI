"""
FastAPI AI Microservice for DermAI Skin Screening Portal
Exposes /health and /predict REST APIs
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from predict import analyze_skin_lesion

app = FastAPI(
    title="DermAI Skin Health Screening API",
    description="Python FastAPI service running CNN AI model for skin condition predictions.",
    version="1.0.0"
)

# Enable CORS for Node.js Express backend and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "DermAI Python AI Service",
        "model_version": "1.0.0-resnet50"
    }

@app.post("/predict")
async def predict_skin_disease(image: UploadFile = File(...)):
    """
    Accepts binary image upload and returns AI disease prediction.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image file too large.")

    result = analyze_skin_lesion(contents)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
