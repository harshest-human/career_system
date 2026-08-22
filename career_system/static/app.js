function getApiBase() {
  if (window.location.protocol === 'file:') {
    return 'http://localhost:8000';
  }
  return '';
}

const API_BASE = getApiBase();

function careerApp() {
  return {
    currentStep: 1,
    serverConnected: false,
    profiles: [],
    activeProfileId: 'default',
    profileData: { personal: {}, executive_summary: {}, experience: [], education: [], skills: {} },
    jobsList: [],

    // Account Creation Modal
    showNewAccountModal: false,
    newAccountName: '',

    // Portal Connectors
    portalsList: [],
    showPortalModal: false,
    newPortalForm: { portal_name: '', portal_url: '', username: '', password: '' },

    // Ingestion state
    ingestMode: 'url',
    scrapeUrlInput: '',
    rawJobTextInput: '',
    isLoadingBreakdown: false,
    analysisResult: null,
    jobFilesList: [],

    // PDF / File Viewer Modal
    showPdfViewerModal: false,
    activePdfViewerUrl: '',
    activePdfViewerTitle: 'Document Viewer',

    // Google Sync
    googleWebhookUrl: localStorage.getItem('google_webhook_url') || '',
    showGoogleScriptModal: false,
    googleScriptCode: '',

    // Studio state
    studioJob: { company: 'Target Company', role_title: 'Position', location: 'Location', extracted_skills: [] },
    studioDocType: 'cv',
    studioLang: 'en',
    userFitNotes: '',
    studioSummary: '',
    studioLetterParagraphs: ['', '', ''],
    currentHtmlContent: '',
    jobPhotoSrc: null,
    isUploadingPhoto: false,

    // Outreach state
    outreachForm: { company: '', contact_name: 'Hiring Team', role_title: '', outreach_type: 'connection' },
    generatedPitchText: '',

    // Settings
    showSettingsModal: false,
    geminiApiKey: localStorage.getItem('gemini_api_key') || '',

    async init() {
      await this.checkServer();
      await this.loadProfiles();
      await this.loadPortals();
      await this.loadJobs();
      await this.loadGoogleScriptTemplate();

      this.$watch('geminiApiKey', (val) => localStorage.setItem('gemini_api_key', val));
      this.$watch('googleWebhookUrl', (val) => localStorage.setItem('google_webhook_url', val));

      setInterval(() => this.checkServer(), 8000);
    },

    async checkServer() {
      try {
        const res = await fetch(`${API_BASE}/api/health`);
        this.serverConnected = res.ok;
      } catch (err) {
        this.serverConnected = false;
      }
    },

    async loadGoogleScriptTemplate() {
      try {
        const res = await fetch(`${API_BASE}/api/google/script-template`);
        const data = await res.json();
        this.googleScriptCode = data.script || '';
      } catch (err) {
        console.warn('Could not load script template:', err);
      }
    },

    async loadProfiles() {
      try {
        const res = await fetch(`${API_BASE}/api/profiles`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        this.profiles = await res.json();
        if (this.profiles.length > 0) {
          if (!this.profiles.some(p => p.id === this.activeProfileId)) {
            this.activeProfileId = this.profiles[0].id;
          }
          await this.loadActiveProfile();
        }
        this.serverConnected = true;
      } catch (err) {
        console.warn('Error loading profiles:', err);
        this.serverConnected = false;
      }
    },

    async createNewAccount() {
      if (!this.newAccountName.trim()) {
        alert('Please enter a candidate name.');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/profiles/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: this.newAccountName }),
        });
        const data = await res.json();
        if (res.ok) {
          this.newAccountName = '';
          this.showNewAccountModal = false;
          await this.loadProfiles();
          this.activeProfileId = data.profile_id;
          await this.loadActiveProfile();
          alert('New candidate account created!');
        }
      } catch (err) {
        alert('Error creating account: ' + err.message);
      }
    },

    async loadActiveProfile() {
      try {
        const res = await fetch(`${API_BASE}/api/profiles/${this.activeProfileId}`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        this.profileData = data.data || {};
        this.studioSummary = this.profileData.executive_summary?.[this.studioLang] || '';
      } catch (err) {
        console.warn('Error loading active profile:', err);
      }
    },

    async saveProfile() {
      if (!this.serverConnected) {
        alert('Server is offline. Please launch start_web.bat to connect.');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/profiles/${this.activeProfileId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.profileData),
        });
        if (res.ok) {
          alert('Profile saved and synced successfully!');
          await this.loadProfiles();
        } else {
          alert('Error saving profile.');
        }
      } catch (err) {
        alert('Connection error: ' + err.message);
      }
    },

    // --- Portal Credential Methods ---
    async loadPortals() {
      try {
        const res = await fetch(`${API_BASE}/api/portals`);
        if (res.ok) {
          this.portalsList = await res.json();
        }
      } catch (err) {
        console.warn('Error loading portals:', err);
      }
    },

    async savePortalCredential() {
      if (!this.newPortalForm.portal_name || !this.newPortalForm.username) {
        alert('Please provide portal name and login email/username.');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/portals`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.newPortalForm),
        });
        if (res.ok) {
          this.newPortalForm = { portal_name: '', portal_url: '', username: '', password: '' };
          this.showPortalModal = false;
          await this.loadPortals();
          alert('Portal credentials saved locally in database!');
        }
      } catch (err) {
        alert('Error saving portal: ' + err.message);
      }
    },

    async deletePortal(portalId) {
      if (!confirm('Are you sure you want to remove this portal connection?')) return;
      try {
        await fetch(`${API_BASE}/api/portals/${portalId}`, { method: 'DELETE' });
        await this.loadPortals();
      } catch (err) {
        alert('Error removing portal: ' + err.message);
      }
    },

    saveApiKey() {
      if (!this.geminiApiKey) {
        alert('Please enter a valid Gemini API key.');
        return;
      }
      localStorage.setItem('gemini_api_key', this.geminiApiKey);
      alert('Gemini API key saved!');
    },

    async loadJobs() {
      try {
        const res = await fetch(`${API_BASE}/api/jobs`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        this.jobsList = await res.json();
        this.serverConnected = true;
      } catch (err) {
        console.warn('Error loading jobs:', err);
      }
    },

    async scrapeJobUrl() {
      if (!this.scrapeUrlInput) return;
      this.isLoadingBreakdown = true;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/scrape`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: this.scrapeUrlInput,
            gemini_api_key: this.geminiApiKey || null,
          }),
        });
        const data = await res.json();
        if (res.ok && data.data) {
          this.scrapeUrlInput = '';
          await this.loadJobs();
          await this.selectJobForAnalysis(data.data);
          alert('Job analyzed with Gemini & local job folder created!');
        } else {
          alert('Scraping error: ' + (data.detail || 'Failed'));
        }
      } catch (err) {
        alert('Error: ' + err.message);
      } finally {
        this.isLoadingBreakdown = false;
      }
    },

    async uploadJobPdf(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.isLoadingBreakdown = true;
      const formData = new FormData();
      formData.append('file', file);
      if (this.geminiApiKey) {
        formData.append('gemini_api_key', this.geminiApiKey);
      }
      try {
        const res = await fetch(`${API_BASE}/api/jobs/upload`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.data) {
          await this.loadJobs();
          await this.selectJobForAnalysis(data.data);
          alert('Job PDF parsed & local job folder created!');
        } else {
          alert('Upload error: ' + (data.detail || res.statusText));
        }
      } catch (err) {
        alert('Upload error: ' + err.message);
      } finally {
        this.isLoadingBreakdown = false;
      }
    },

    async parseRawJobText() {
      if (!this.rawJobTextInput) return;
      this.isLoadingBreakdown = true;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/parse-text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            raw_text: this.rawJobTextInput,
            gemini_api_key: this.geminiApiKey || null,
          }),
        });
        const data = await res.json();
        if (res.ok && data.data) {
          this.rawJobTextInput = '';
          await this.loadJobs();
          await this.selectJobForAnalysis(data.data);
          alert('Job description analyzed with Gemini & breakdown ready below!');
        } else {
          alert('Parsing error: ' + (data.detail || 'Failed'));
        }
      } catch (err) {
        alert('Error: ' + err.message);
      } finally {
        this.isLoadingBreakdown = false;
      }
    },

    async importJobPackage(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.isLoadingBreakdown = true;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch(`${API_BASE}/api/jobs/import-zip`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (res.ok) {
          await this.loadJobs();
          const job = this.jobsList.find(j => j.id === data.job_id);
          if (job) {
            await this.selectJobForAnalysis(job);
          }
          alert('Job Package (.zip) imported and restored successfully!');
        } else {
          alert('Import error: ' + (data.detail || 'Failed to extract package'));
        }
      } catch (err) {
        alert('Import error: ' + err.message);
      } finally {
        this.isLoadingBreakdown = false;
      }
    },

    async saveJobChanges() {
      if (!this.analysisResult || !this.analysisResult.job) return;
      const job = this.analysisResult.job;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${job.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(job),
        });
        if (res.ok) {
          await this.loadJobs();
          await this.loadJobFiles(job.id);
          alert('Job details and metadata saved successfully!');
        } else {
          alert('Error saving job details.');
        }
      } catch (err) {
        alert('Error: ' + err.message);
      }
    },

    async deleteJob(jobId) {
      if (!confirm('Are you sure you want to delete this job and its local folder?')) return;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
          method: 'DELETE',
        });
        if (res.ok) {
          if (this.analysisResult?.job?.id === jobId) {
            this.analysisResult = null;
            this.jobFilesList = [];
          }
          await this.loadJobs();
          alert('Job and its files deleted successfully.');
        } else {
          alert('Error deleting job.');
        }
      } catch (err) {
        alert('Error: ' + err.message);
      }
    },

    async openJobLocalFolder(jobId) {
      if (!jobId) return;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/open-folder`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          console.log('Opened folder:', data.path);
        } else {
          alert('Folder path: ' + data.path);
        }
      } catch (err) {
        alert('Could not open folder automatically: ' + err.message);
      }
    },

    downloadJobZip(jobId) {
      window.location.href = `${API_BASE}/api/jobs/${jobId}/export-zip`;
    },

    async loadJobFiles(jobId) {
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/files`);
        if (res.ok) {
          const data = await res.json();
          this.jobFilesList = data.files || [];
        }
      } catch (err) {
        console.warn('Could not load job files:', err);
      }
    },

    openFileViewer(filePath, title) {
      this.activePdfViewerUrl = (API_BASE ? API_BASE : '') + filePath;
      this.activePdfViewerTitle = title || 'Document Viewer';
      this.showPdfViewerModal = true;
    },

    openPdfViewer(pdfPath, roleTitle) {
      this.activePdfViewerUrl = (API_BASE ? API_BASE : '') + pdfPath;
      this.activePdfViewerTitle = roleTitle || 'Job Advertisement PDF';
      this.showPdfViewerModal = true;
    },

    async updateJobStatus(jobId, status) {
      try {
        await fetch(`${API_BASE}/api/jobs/${jobId}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status }),
        });
      } catch (err) {
        console.warn('Error updating status:', err);
      }
    },

    async selectJobForAnalysis(job) {
      try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            job_id: job.id,
            gemini_api_key: this.geminiApiKey || null,
          }),
        });
        if (res.ok) {
          this.analysisResult = await res.json();
          await this.loadJobFiles(job.id);
        }
      } catch (err) {
        alert('Analysis error: ' + err.message);
      }
    },

    onLanguageChange() {
      this.studioSummary = this.profileData.executive_summary?.[this.studioLang] || '';
      this.selectJobForStudio(this.studioJob);
    },

    selectJobForStudio(job) {
      this.studioJob = job;
      this.studioSummary = this.profileData.executive_summary?.[this.studioLang] || '';
      this.outreachForm.company = job.company || '';
      this.outreachForm.role_title = job.role_title || '';
      this.outreachForm.contact_name = job.metadata?.hiring_manager_contact || job.hiring_manager_contact || 'Hiring Team';
      this.jobPhotoSrc = job.photo_path ? ((API_BASE ? API_BASE : '') + job.photo_path) : null;

      if (this.studioLang === 'en') {
        this.studioLetterParagraphs = [
          `I am writing to express my strong interest in the ${job.role_title} position at ${job.company}. My professional background and proven technical execution directly align with your team's current operational goals.`,
          `In my previous work, I have successfully led key initiatives, streamlined analytical workflows, and collaborated cross-functionally to achieve measurable results.`,
          `I hold valid work authorization in Germany and look forward to discussing how my experience can support ${job.company}'s ongoing success.`,
        ];
      } else {
        this.studioLetterParagraphs = [
          `mit großem Interesse bewerbe ich mich auf die Position als ${job.role_title} bei ${job.company}. Mein Profil verbindet fundierte Fachkenntnisse mit einer lösungsorientierten und strukturierten Arbeitsweise.`,
          `In meinen bisherigen Projekten und Verantwortungsbereichen habe ich maßgebliche Aufgaben erfolgreich gesteuert, datengestützte Prozesse optimiert und eng mit interdisziplinären Teams zusammengearbeitet.`,
          `Ich verfüge über eine uneingeschränkte Arbeitserlaubnis in Deutschland und freue mich auf die Gelegenheit, mich Ihnen in einem persönlichen Gespräch vorzustellen.`,
        ];
      }

      this.renderHtmlPreview();
    },

    async uploadJobPhoto(event) {
      const file = event.target.files[0];
      if (!file) return;
      if (!this.studioJob || !this.studioJob.id) {
        alert('Please select or analyze a job from Step 2 first so the photo can be saved into its dedicated folder.');
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      this.isUploadingPhoto = true;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${this.studioJob.id}/photo`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (data.status === 'success') {
          this.jobPhotoSrc = data.photo_base64 || data.photo_url;
          if (this.studioJob) {
            this.studioJob.photo_path = data.photo_url;
          }
          await this.renderHtmlPreview();
          await this.loadJobFiles(this.studioJob.id);
        } else {
          alert('Photo upload error: ' + (data.detail || 'Failed'));
        }
      } catch (err) {
        alert('Error uploading photo: ' + err.message);
      } finally {
        this.isUploadingPhoto = false;
      }
    },

    async removeJobPhoto() {
      if (!this.studioJob || !this.studioJob.id) {
        this.jobPhotoSrc = null;
        await this.renderHtmlPreview();
        return;
      }
      try {
        await fetch(`${API_BASE}/api/jobs/${this.studioJob.id}/photo`, { method: 'DELETE' });
        this.jobPhotoSrc = null;
        if (this.studioJob) {
          this.studioJob.photo_path = '';
        }
        await this.renderHtmlPreview();
        await this.loadJobFiles(this.studioJob.id);
      } catch (err) {
        console.warn('Error removing photo:', err);
      }
    },

    async renderHtmlPreview() {
      const endpoint = this.studioDocType === 'cv' ? '/api/render/html-cv' : '/api/render/html-letter';
      try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            job_data: this.studioJob,
            lang: this.studioLang,
            custom_summary: this.studioSummary,
            custom_letter_paragraphs: this.studioLetterParagraphs,
            photo_src: this.jobPhotoSrc || null,
          }),
        });
        const data = await res.json();
        if (data.html) {
          this.currentHtmlContent = data.html;
          const iframe = document.getElementById('previewIframe');
          if (iframe) {
            const doc = iframe.contentWindow.document;
            doc.open();
            doc.write(data.html);
            doc.close();
          }
          if (this.studioJob.id) {
            await this.loadJobFiles(this.studioJob.id);
          }
        }
      } catch (err) {
        console.error('Error rendering HTML preview:', err);
      }
    },

    async requestAiSuggestions() {
      try {
        const res = await fetch(`${API_BASE}/api/ai/suggest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            job_data: this.studioJob,
            user_notes: this.userFitNotes,
            lang: this.studioLang,
            gemini_api_key: this.geminiApiKey || null,
          }),
        });
        const data = await res.json();
        if (data.cover_letter_paragraphs) {
          this.studioLetterParagraphs = data.cover_letter_paragraphs;
          this.studioDocType = 'letter';
          await this.renderHtmlPreview();
          alert('AI suggestions applied to cover letter and saved in your job folder!');
        }
      } catch (err) {
        alert('Error requesting AI suggestions: ' + err.message);
      }
    },

    printHtmlDocument() {
      const iframe = document.getElementById('previewIframe');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      }
    },

    isUploadingDrive: false,

    async uploadJobToGoogleDrive(jobId) {
      if (!jobId) {
        alert('Please select or analyze a job first.');
        return;
      }
      if (!this.googleWebhookUrl) {
        alert('Google Drive Webhook URL not configured. Please paste your Webhook URL in Step 1 (Account & Connectors).');
        this.currentStep = 1;
        return;
      }
      this.isUploadingDrive = true;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/upload-to-drive`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ webhook_url: this.googleWebhookUrl }),
        });
        const data = await res.json();
        if (data.status === 'success') {
          if (data.folder_url) {
            if (confirm('Job folder and files successfully uploaded to Google Drive! Open Google Drive folder now?')) {
              window.open(data.folder_url, '_blank');
            }
          } else {
            alert('Job folder uploaded to Google Drive successfully!');
          }
        } else {
          alert('Upload failed: ' + (data.message || 'Check your Google Script deployment'));
        }
      } catch (err) {
        alert('Error uploading to Google Drive: ' + err.message);
      } finally {
        this.isUploadingDrive = false;
      }
    },

    async testGoogleSync() {
      if (!this.googleWebhookUrl) {
        alert('Please enter a Google Apps Script Webhook URL first.');
        return;
      }
      try {
        const res = await fetch(this.googleWebhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'text/plain' },
          body: JSON.stringify({
            action: 'upload_folder',
            folder_name: 'Test_Connection',
            files: [{ name: 'test_sync.txt', content: 'Connection successful!', is_base64: false }],
          }),
        });
        const data = await res.json();
        if (data.status === 'success') {
          alert('Google Drive connection verified successfully! Folder created in your Google Drive.');
        } else {
          alert('Google responded: ' + JSON.stringify(data));
        }
      } catch (err) {
        alert('Connection error: ' + err.message);
      }
    },

    async generatePitchMessage() {
      try {
        const res = await fetch(`${API_BASE}/api/outreach/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            job_id: this.studioJob.id || null,
            company: this.outreachForm.company,
            contact_name: this.outreachForm.contact_name,
            role_title: this.outreachForm.role_title,
            outreach_type: this.outreachForm.outreach_type,
          }),
        });
        const data = await res.json();
        this.generatedPitchText = data.pitch;
        if (this.studioJob.id) {
          await this.loadJobFiles(this.studioJob.id);
        }
      } catch (err) {
        alert('Error generating outreach: ' + err.message);
      }
    },

    copyPitchToClipboard() {
      if (!this.generatedPitchText) return;
      navigator.clipboard.writeText(this.generatedPitchText);
      alert('Outreach pitch copied to clipboard!');
    },
  };
}
