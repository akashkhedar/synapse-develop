import { API } from "apps/synapse/src/providers/ApiProvider";

export const importFiles = async ({
  files,
  body,
  project,
  onUploadStart,
  onUploadFinish,
  onFinish,
  onError,
  dontCommitToProject,
}: {
  files: { name: string }[];
  body: Record<string, any> | FormData;
  project: APIProject;
  onUploadStart?: (files: { name: string }[]) => void;
  onUploadFinish?: (files: { name: string }[]) => void;
  onFinish?: (response: any) => void;
  onError?: (response: any) => void;
  dontCommitToProject?: boolean;
}) => {
  onUploadStart?.(files);

  const query = dontCommitToProject ? { commit_to_project: "false" } : {};

  // IMPORTANT: Don't set Content-Type for FormData!
  // The browser automatically sets it with the correct boundary parameter
  // (e.g., "multipart/form-data; boundary=----WebKitFormBoundary...")
  // Setting it manually breaks multipart parsing on the server
  const headers: Record<string, string> = {};
  if (!(body instanceof FormData)) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  }
  
  // Debug: Log FormData contents
  if (body instanceof FormData) {
    console.log("Uploading FormData with entries:");
    for (const [key, value] of body.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}: ${value}`);
      }
    }
  }
  
  const res = await API.invoke(
    "importFiles",
    { pk: project.id, ...query },
    { headers, body },
  );

  if (res && !res.error) {
    await onFinish?.(res);
  } else {
    onError?.(res?.response);
  }

  onUploadFinish?.(files);
};

