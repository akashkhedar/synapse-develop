#!/usr/bin/env python3
# Assign a user to portion of tasks in a project filtered by Inner ID (0..100)

# 1. Go to your account and generate API key (Personal Access Token is recommended)
# 2. Set SYNAPSE_URL and SYNAPSE_API_KEY env vars, SYNAPSE_URL should start with https:// or http://
# 3. Switch your project to the Manual mode (Project settings > Annotation)
# 4. Add your user to project's workspace
# 5. Run the script: python assign_users_to_tasks.py <PROJECT_ID> <USER_EMAIL> [AN|RE]
# (You can get project ID from the URL, e.g. https://app.synapse.io/projects/<PROJECT_ID>)
# (AN - annotator, RE - reviewergit)

import os
import sys
from synapse_sdk.client import Synapse


def main():
    # Required: set env vars or pass args
    base_url = os.getenv("SYNAPSE_URL")
    api_key = os.getenv("SYNAPSE_API_KEY")
    if not api_key or not base_url:
        print("ERROR: set SYNAPSE_API_KEY and SYNAPSE_URL env var")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Usage: script.py <PROJECT_ID> <USER_EMAIL> [AN|RE]")
        sys.exit(1)

    project_id = int(sys.argv[1])
    user_email = sys.argv[2].strip()
    assignment_type = (
        sys.argv[3].strip().upper() if len(sys.argv) > 3 else "AN"
    )  # AN=annotate, RE=review

    client = Synapse(base_url=base_url, api_key=api_key)

    # 1) Get project by ID
    project = client.projects.get(id=project_id)
    print(f"Project: {project.title} (id={project.id})")

    # 2) Get user by email
    users = list(client.users.list())
    user = next(
        (u for u in users if (u.email or "").lower() == user_email.lower()), None
    )
    if not user:
        print(f"ERROR: user with email {user_email} not found")
        sys.exit(1)
    print(f"User: {user.email} (id={user.id})")

    # 3) Assign this user to tasks filtered by Inner ID from 0 to 100 (portion of tasks)
    # Use Data Manager-style filters and select all filtered tasks
    filters = {
        "conjunction": "and",
        "items": [
            {
                "filter": "filter:tasks:inner_id",
                "operator": "greater",
                "value": 0,
                "child_filter": None,
                "type": "Number",
            },
            {
                "filter": "filter:tasks:inner_id",
                "operator": "less",
                "value": 100,
                "child_filter": None,
                "type": "Number",
            },
        ],
    }
    selected_items = {"all": True}

    resp = client.projects.assignments.bulk_assign(
        id=project_id,
        type=assignment_type,  # 'AN' or 'RE'
        users=[user.id],  # list of user IDs
        selected_items=selected_items,  # apply to all tasks matching filters, or you can pass here specific task IDs
        filters=filters,  # Inner ID in (0, 100)
    )

    # Simple summary
    print(f"Bulk assignment done: {resp}")


if __name__ == "__main__":
    main()
