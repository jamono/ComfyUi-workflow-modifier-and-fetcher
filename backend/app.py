from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
from pathlib import Path
import json
import shutil
import os
from workflow_analyzer import WorkflowAnalyzer

app = Flask(__name__)
CORS(app)

# Store dla postępu pobierania
download_progress = {}

def update_progress(model_name, progress, status):
    """Aktualizuje postęp pobierania dla danego modelu"""
    download_progress[model_name] = {
        'progress': progress,
        'status': status
    }

@app.route("/")
def home():
    """Endpoint główny z listą dostępnych endpointów"""
    return jsonify({
        "status": "running",
        "endpoints": [
            "GET / - This list",
            "GET /api/instances - List all instances",
            "POST /api/instances - Create new instance",
            "DELETE /api/instances/{id} - Delete instance",
            "POST /api/analyze-workflow - Analyze workflow file",
            "GET /api/download-progress - Get download progress"
        ]
    })

@app.route("/api/analyze-workflow", methods=["POST"])
def analyze_workflow():
    """Analizuje plik workflow i zwraca wymagane modele"""
    print("Received workflow analysis request")
    
    if "workflow" not in request.files:
        print("No workflow file in request")
        return jsonify({"error": "No workflow file provided"}), 400

    workflow_file = request.files["workflow"]
    print(f"Processing workflow file: {workflow_file.filename}")

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        workflow_file.save(temp_file.name)
        print(f"Saved workflow to temporary file: {temp_file.name}")

        try:
            # Analizuj workflow
            analyzer = WorkflowAnalyzer(Path(temp_file.name))
            required_models = analyzer.analyze()
            print(f"Analysis completed. Found models: {required_models}")

            # Przygotuj odpowiedź
            response = {
                "required_models": [
                    {
                        "name": model.name,
                        "source": model.source,
                        "url": model.url,
                        "type": getattr(model, 'type', 'unknown'),
                        "size": "Unknown"
                    }
                    for model in required_models
                ]
            }
            
            print(f"Sending response: {json.dumps(response, indent=2)}")
            return jsonify(response)

        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
        finally:
            Path(temp_file.name).unlink(missing_ok=True)

@app.route("/api/instances", methods=["GET"])
def list_instances():
    """Zwraca listę wszystkich instancji ComfyUI"""
    try:
        instances_dir = Path("instances")
        if not instances_dir.exists():
            instances_dir.mkdir(parents=True)
        
        instances = []
        for path in instances_dir.iterdir():
            if path.is_dir():
                instances.append({
                    "id": path.name,
                    "path": str(path.absolute()),
                    "status": "active",
                    "models_count": len(list(path.glob('models/**/*')))
                })
        
        return jsonify(instances)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/instances", methods=["POST"])
def create_instance():
    """Tworzy nową instancję ComfyUI"""
    try:
        data = request.json
        instance_id = data.get("instance_id")
        
        if not instance_id:
            return jsonify({"error": "instance_id is required"}), 400

        instance_path = Path("instances") / instance_id
        instance_path.mkdir(parents=True, exist_ok=True)
        
        # Stwórz podstawową strukturę folderów
        (instance_path / "models").mkdir(exist_ok=True)
        
        return jsonify({
            "id": instance_id,
            "path": str(instance_path.absolute()),
            "status": "created"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/instances/<instance_id>", methods=["DELETE"])
def delete_instance(instance_id):
    """Usuwa instancję ComfyUI"""
    try:
        instance_path = Path("instances") / instance_id
        
        if not instance_path.exists():
            return jsonify({"error": "Instance not found"}), 404

        shutil.rmtree(instance_path)
        return jsonify({"status": "deleted"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download-progress", methods=["GET"])
def get_download_progress():
    """Zwraca aktualny postęp pobierania modeli"""
    return jsonify(download_progress)

@app.errorhandler(Exception)
def handle_error(error):
    """Globalny handler błędów"""
    print(f"Error occurred: {str(error)}")
    return jsonify({
        "error": str(error),
        "type": error.__class__.__name__
    }), 500

if __name__ == "__main__":
    print("Starting server on port 3000...")
    app.run(debug=True, port=3000, host='0.0.0.0')