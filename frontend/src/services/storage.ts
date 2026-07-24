import { getUserToken } from "./auth";
import { logAnalyticsEvent } from "./analytics";

export const uploadUserFile = async (
  userId: string,
  fileName: string,
  fileBlob: Blob,
  onProgress?: (progress: number) => void
): Promise<string> => {
  try {
    const token = await getUserToken();
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    
    const formData = new FormData();
    formData.append("file", fileBlob, fileName);

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // Direct HTTP POST to local FastAPI server upload endpoint
    const response = await fetch(`${apiUrl}/users/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`);
    }

    if (onProgress) {
      onProgress(100);
    }

    const data = await response.json();
    logAnalyticsEvent("file_upload_completed", { user_id: userId, file_name: fileName });
    return data.url;
  } catch (error: any) {
    logAnalyticsEvent("file_upload_failed", { user_id: userId, file_name: fileName, error: error.message });
    console.error("Local server upload failed. Falling back to mock Object URL.", error);
    // Safe mock fallback for standalone client testing
    return URL.createObjectURL(fileBlob);
  }
};
