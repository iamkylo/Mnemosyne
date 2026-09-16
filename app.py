import os
import sys
import uvicorn

# Append backend directory to system path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.append(backend_path)

if __name__ == "__main__":
    # Hugging Face routes port 7860 dynamically
    port = int(os.environ.get("PORT", 7860))
    print(f"Booting Mnemosyne API Server on port {port}...")
    
    # Run the FastAPI app
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
