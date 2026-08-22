"""
Google Drive Cloud Sync Helper
Supports 1-click upload of dedicated Job Folders directly to Google Drive
via zero-configuration Google Apps Script automation.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Ready-to-use Google Apps Script template for 1-click Google Drive folder upload
GOOGLE_APPS_SCRIPT_TEMPLATE = """
/**
 * Career System - Google Drive Folder Upload Script
 * Paste this in Google Apps Script (script.google.com) -> Deploy as Web App (Access: Anyone)
 */
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;
    
    if (action === "upload_folder") {
      var folderName = data.folder_name || "Job_Application";
      var root = DriveApp.getRootFolder();
      
      // Check if CareerSystem parent folder exists
      var careerFolders = root.getFoldersByName("CareerSystem_Jobs");
      var parent = careerFolders.hasNext() ? careerFolders.next() : root.createFolder("CareerSystem_Jobs");
      
      // Check if specific job folder exists
      var existingFolders = parent.getFoldersByName(folderName);
      var jobFolder = existingFolders.hasNext() ? existingFolders.next() : parent.createFolder(folderName);
      
      // Create / update files inside the folder
      var files = data.files || [];
      for (var i = 0; i < files.length; i++) {
        var f = files[i];
        var existingFiles = jobFolder.getFilesByName(f.name);
        while (existingFiles.hasNext()) {
          existingFiles.next().setTrashed(true);
        }
        
        if (f.is_base64) {
          var decoded = Utilities.base64Decode(f.content);
          var blob = Utilities.newBlob(decoded, f.mime_type || "application/pdf", f.name);
          jobFolder.createFile(blob);
        } else {
          jobFolder.createFile(f.name, f.content, f.mime_type || "text/html");
        }
      }
      
      return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        folder_url: jobFolder.getUrl(),
        folder_id: jobFolder.getId(),
        message: "Folder uploaded to Google Drive"
      }));
    }
    
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: "Unknown action"}));
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: err.toString()}));
  }
}
"""


class GoogleWorkspaceSync:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("GOOGLE_WEBHOOK_URL")

    def upload_job_folder_to_drive(self, folder_path: Path, folder_name: str) -> Dict[str, Any]:
        """Upload all files in a local job folder directly to Google Drive."""
        if not self.webhook_url:
            return {"status": "offline", "message": "Google Drive Webhook not configured"}

        if not folder_path.exists():
            return {"status": "error", "message": "Local folder does not exist"}

        files_payload = []
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                if file_path.suffix.lower() in [".pdf", ".png", ".jpg"]:
                    with open(file_path, "rb") as f:
                        b64_content = base64.b64encode(f.read()).decode("utf-8")
                    files_payload.append({
                        "name": file_path.name,
                        "content": b64_content,
                        "is_base64": True,
                        "mime_type": "application/pdf" if file_path.suffix.lower() == ".pdf" else "image/png",
                    })
                else:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text_content = f.read()
                    mime = "text/html" if file_path.suffix.lower() == ".html" else "application/json" if file_path.suffix.lower() == ".json" else "text/plain"
                    files_payload.append({
                        "name": file_path.name,
                        "content": text_content,
                        "is_base64": False,
                        "mime_type": mime,
                    })

        payload = {
            "action": "upload_folder",
            "folder_name": folder_name,
            "files": files_payload,
        }

        try:
            res = requests.post(self.webhook_url, json=payload, timeout=30)
            return res.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
