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

# Bulletproof Google Apps Script template for 1-click Google Drive folder upload
GOOGLE_APPS_SCRIPT_TEMPLATE = """/**
 * Career System - Google Drive 1-Click Folder Upload Webhook
 * 
 * SETUP INSTRUCTIONS (Takes 1 Minute):
 * 1. Open https://script.google.com and click "+ New Project"
 * 2. Delete existing code and paste this ENTIRE code
 * 3. Click "Save" (disk icon), then click "Deploy" -> "New deployment"
 * 4. Select Type: "Web app"
 *    - Description: CareerSystem Sync
 *    - Execute as: "Me (your_email@gmail.com)"
 *    - Who has access: "Anyone" (CRITICAL: Must be Anyone so your local app can upload)
 * 5. Click "Deploy", click "Authorize access" -> choose your Google Account -> "Advanced" -> "Go to Career System (unsafe)" -> "Allow"
 * 6. Copy the "Web app URL" (ends in /exec) and paste it into Career System Step 1!
 */

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "success",
    message: "Career System Google Drive Webhook is ONLINE and ready!"
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var raw = (e && e.postData) ? e.postData.contents : "";
    var data = raw ? JSON.parse(raw) : {};
    var action = data.action || "upload_folder";
    
    if (action === "upload_folder" || action === "test") {
      var folderName = data.folder_name || "Job_Application";
      var root = DriveApp.getRootFolder();
      
      // 1. Get or create parent 'CareerSystem_Jobs' folder in your Drive
      var careerFolders = root.getFoldersByName("CareerSystem_Jobs");
      var parent = careerFolders.hasNext() ? careerFolders.next() : root.createFolder("CareerSystem_Jobs");
      
      // 2. Get or create specific job folder
      var existingFolders = parent.getFoldersByName(folderName);
      var jobFolder = existingFolders.hasNext() ? existingFolders.next() : parent.createFolder(folderName);
      
      // 3. Upload or update all files inside the folder
      var files = data.files || [];
      for (var i = 0; i < files.length; i++) {
        var f = files[i];
        if (!f || !f.name) continue;
        
        // Remove old version if exists
        var existingFiles = jobFolder.getFilesByName(f.name);
        while (existingFiles.hasNext()) {
          existingFiles.next().setTrashed(true);
        }
        
        // Create new file
        if (f.is_base64) {
          var decoded = Utilities.base64Decode(f.content);
          var blob = Utilities.newBlob(decoded, f.mime_type || "application/pdf", f.name);
          jobFolder.createFile(blob);
        } else {
          jobFolder.createFile(f.name, f.content || "", f.mime_type || "text/plain");
        }
      }
      
      var output = {
        status: "success",
        folder_url: jobFolder.getUrl(),
        folder_id: jobFolder.getId(),
        file_count: files.length,
        message: "Successfully uploaded " + files.length + " files to Google Drive folder: " + folderName
      };
      
      return ContentService.createTextOutput(JSON.stringify(output)).setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: "Unknown action: " + action
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
"""


class GoogleWorkspaceSync:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("GOOGLE_WEBHOOK_URL")

    def clean_webhook_url(self, url: str) -> str:
        """Validate and clean the Google Apps Script Webhook URL."""
        if not url:
            return ""
        url = url.strip()
        if "/edit" in url:
            url = url.split("/edit")[0] + "/exec"
        return url

    def upload_job_folder_to_drive(self, folder_path: Path, folder_name: str) -> Dict[str, Any]:
        """Upload all files in a local job folder directly to Google Drive."""
        cleaned_url = self.clean_webhook_url(self.webhook_url or "")
        if not cleaned_url:
            return {"status": "offline", "message": "Google Drive Webhook URL not configured."}

        if not folder_path.exists():
            return {"status": "error", "message": f"Local folder {folder_path} does not exist"}

        files_payload = []
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in [".pdf", ".png", ".jpg", ".jpeg", ".webp"]:
                    with open(file_path, "rb") as f:
                        b64_content = base64.b64encode(f.read()).decode("utf-8")
                    mime = "application/pdf" if suffix == ".pdf" else "image/png"
                    files_payload.append({
                        "name": file_path.name,
                        "content": b64_content,
                        "is_base64": True,
                        "mime_type": mime,
                    })
                else:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text_content = f.read()
                    mime = "text/html" if suffix == ".html" else "application/json" if suffix == ".json" else "text/plain"
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
            res = requests.post(
                cleaned_url,
                data=json.dumps(payload),
                headers={"Content-Type": "text/plain;charset=utf-8"},
                timeout=45,
                allow_redirects=True,
            )

            # Try to parse response JSON
            try:
                data = res.json()
                return data
            except Exception:
                # If Google Apps Script returned HTML or redirect response
                if res.status_code == 200 and ("drive.google.com" in res.text or "CareerSystem_Jobs" in res.text):
                    return {"status": "success", "message": "Files uploaded to Google Drive successfully."}
                
                # Check for permission or HTML errors
                if "accounts.google.com" in res.text or "Sign in" in res.text:
                    return {
                        "status": "error",
                        "message": "Google Authorization Error: Make sure when deploying your Apps Script, 'Who has access' is set to 'Anyone' (not 'Only myself').",
                    }
                return {
                    "status": "error",
                    "message": f"Google Script Error (HTTP {res.status_code}): {res.text[:200]}",
                }
        except Exception as e:
            return {"status": "error", "message": f"Connection Error: {str(e)}"}
