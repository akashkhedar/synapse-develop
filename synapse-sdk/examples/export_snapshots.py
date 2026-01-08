"""
Export a snapshot with tasks filtered by the first available view
"""

import os
from pathlib import Path

from synapse_sdk.client import Synapse

SYNAPSE_URL = os.getenv("SYNAPSE_URL", default="http://localhost:8080")
API_KEY = os.getenv("SYNAPSE_API_KEY")
PROJECT_ID = int(os.getenv("SYNAPSE_PROJECT_ID", "1"))


def main() -> None:
    client = Synapse(base_url=SYNAPSE_URL, api_key=API_KEY)

    # Ensure project exists and try to use the first view as a filter (if any)
    _ = client.projects.get(id=PROJECT_ID)
    views = ls.views.list(project=PROJECT_ID)
    task_filter_options = {"view": views[0].id} if views else None

    # Create export snapshot and download JSON
    out_dir = Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    # If a view exists, pass it via create_kwargs. Otherwise export all annotated tasks.
    create_kwargs = {
        "title": "Export SDK Snapshot",
        "task_filter_options": task_filter_options,
    }
    # Remove None to avoid sending it
    create_kwargs = {k: v for k, v in create_kwargs.items() if v is not None}

    data = client.projects.exports.as_json(
        PROJECT_ID,
        create_kwargs=create_kwargs,
    )

    out_path = out_dir / f"project_{PROJECT_ID}_export.json"
    with open(out_path, "w", encoding="utf-8") as f:
        import json

        json.dump(data, f)
    print(f"Export completed. File saved to: {out_path}")


if __name__ == "__main__":
    main()
