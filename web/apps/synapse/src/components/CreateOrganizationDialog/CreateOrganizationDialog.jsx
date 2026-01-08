import { useState } from "react";
import { Button } from "@synapse/ui";
import { Modal } from "../Modal/ModalPopup";
import { Input } from "../Form";
import { cn } from "../../utils/bem";
import "./CreateOrganizationDialog.scss";

export const CreateOrganizationDialog = ({ isOpen, onClose, onSuccess }) => {
  const [organizationName, setOrganizationName] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState(null);

  const rootClass = cn("create-organization-dialog");

  const handleCreate = async () => {
    if (!organizationName.trim()) {
      setError("Organization name is required");
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch('/api/organizations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title: organizationName.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create organization');
      }

      const newOrg = await response.json();
      
      // Switch to the new organization
      const switchResponse = await fetch('/api/organizations/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          organization_id: newOrg.id,
        }),
      });

      if (!switchResponse.ok) {
        throw new Error('Failed to switch to new organization');
      }

      onSuccess?.(newOrg);
      // Redirect to projects page with new organization context
      window.location.href = '/projects';
    } catch (err) {
      console.error("Failed to create organization:", err);
      setError(err.message || "Failed to create organization");
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    if (!isCreating) {
      setOrganizationName("");
      setError(null);
      onClose();
    }
  };

  return (
    <Modal
      visible={isOpen}
      onHide={handleClose}
      title="Create New Organization"
      style={{ width: 480 }}
      body={
        <div className={rootClass.toString()}>
          <div className={rootClass.elem("content")}>
            <p className={rootClass.elem("description")}>
              Create a new organization to manage projects and collaborate with team members.
            </p>

            <div className={rootClass.elem("form")}>
              <label className={rootClass.elem("label")}>
                Organization Name <span className={rootClass.elem("required")}>*</span>
              </label>
              <Input
                value={organizationName}
                onChange={(e) => {
                  setOrganizationName(e.target.value);
                  setError(null);
                }}
                placeholder="Enter organization name"
                disabled={isCreating}
                autoFocus
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !isCreating) {
                    handleCreate();
                  }
                }}
              />
              {error && (
                <div className={rootClass.elem("error")}>
                  {error}
                </div>
              )}
            </div>
          </div>
        </div>
      }
      footer={
        <div className={rootClass.elem("actions")}>
          <Button
            look="outlined"
            onClick={handleClose}
            disabled={isCreating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={isCreating || !organizationName.trim()}
            waiting={isCreating}
          >
            Create Organization
          </Button>
        </div>
      }
    />
  );
};

