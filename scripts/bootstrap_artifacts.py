"""Copiar evidencia sin ejecutar entrenamiento ni modificar originales."""
import hashlib
import json
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = ROOT.parent / "MantenIA_ML"
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    inventory = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(p in {".venv", ".runtime", "__pycache__"} for p in relative.parts) or not path.is_file():
            continue
        inventory.append({"path": relative.as_posix(), "size_bytes": path.stat().st_size, "sha256": digest(path)})
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/original_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    mapping = {
        "models/mantenia_model.joblib": "edge_service/models/mantenia_model.joblib",
        "models/model_metadata.json": "edge_service/models/model_metadata.json",
        "models/selection_locked.json": "edge_service/models/selection_locked.json",
        "results/metrics/final_test_metrics.json": "edge_service/models/final_test_metrics.json",
        "data/processed/demo_input.csv": "data/demo/demo_input.csv",
        "data/processed/split_manifest.json": "docs/evidence/split_manifest.json",
        "README.md": "docs/evidence/ML_README.md",
        "results/metrics/model_comparison.csv": "docs/evidence/model_comparison.csv",
        "results/metrics/cross_validation_results.csv": "docs/evidence/cross_validation_results.csv",
    }
    for path in (source / "results/figures").glob("*.png"):
        mapping[path.relative_to(source).as_posix()] = "docs/evidence/figures/" + path.name
    copied = []
    for old, new in mapping.items():
        dest = ROOT / new
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / old, dest)
        assert digest(source / old) == digest(dest)
        copied.append({"source": old, "copy": new, "sha256": digest(dest)})
    (ROOT / "docs/artifact_provenance.json").write_text(json.dumps(copied, indent=2), encoding="utf-8")
    print(f"{len(inventory)} archivos originales inventariados; {len(copied)} artefactos copiados, hashes coincidentes.")
if __name__ == "__main__":
    main()
