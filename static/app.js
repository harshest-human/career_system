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
    activeProfileId: 'harsh',
    profileData: { personal: {}, executive_summary: {}, experience: [], education: [], skills: {} },
    jobsList: [],
    scrapeUrlInput: '',
    analysisResult: null,

    // Google Sync
    googleWebhookUrl: localStorage.getItem('google_webhook_url') || '',
    showGoogleScriptModal: false,
    googleScriptCode: '',

    // Studio state
    studioJob: { company: 'Target Company', role_title: 'Position', location: 'Hamburg, Germany', extracted_skills: [] },
    studioDocType: 'cv',
    studioLang: 'en',
    userFitNotes: '',
    studioSummary: '',
    studioLetterParagraphs: ['', '', ''],
    currentHtmlContent: '',

    // Outreach state
    outreachForm: { company: '', contact_name: 'Hiring Team', role_title: '', outreach_type: 'connection' },
    generatedPitchText: '',

    // Settings
    showSettingsModal: false,
    geminiApiKey: localStorage.getItem('gemini_api_key') || '',

    async init() {
      await this.checkServer();
      await this.loadProfiles();
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
      try {
        const res = await fetch(`${API_BASE}/api/jobs/scrape`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: this.scrapeUrlInput }),
        });
        const data = await res.json();
        if (res.ok) {
          this.scrapeUrlInput = '';
          await this.loadJobs();
          if (data.data) {
            await this.selectJobForAnalysis(data.data);
          }
          alert('Job scraped and analyzed successfully!');
        } else {
          alert('Scraping error: ' + (data.detail || 'Failed'));
        }
      } catch (err) {
        alert('Error: ' + err.message);
      }
    },

    async uploadJobPdf(event) {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch(`${API_BASE}/api/jobs/upload`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (res.ok) {
          await this.loadJobs();
          if (data.data) {
            await this.selectJobForAnalysis(data.data);
          }
          alert('Job PDF uploaded and analyzed!');
        }
      } catch (err) {
        alert('Upload error: ' + err.message);
      }
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
          body: JSON.stringify({ candidate_id: this.activeProfileId, job_id: job.id }),
        });
        if (res.ok) {
          this.analysisResult = await res.json();
        }
      } catch (err) {
        alert('Analysis error: ' + err.message);
      }
    },

    selectJobForStudio(job) {
      this.studioJob = job;
      this.studioSummary = this.profileData.executive_summary?.[this.studioLang] || '';
      this.outreachForm.company = job.company || '';
      this.outreachForm.role_title = job.role_title || '';
      this.outreachForm.contact_name = 'Hiring Team';

      if (this.studioLang === 'en') {
        this.studioLetterParagraphs = [
          `I am writing to express my strong interest in the ${job.role_title} position at ${job.company}. My technical background and practical execution directly match your team's objectives.`,
          `In my previous projects, I have led key initiatives involving ${job.extracted_skills?.slice(0, 3).join(', ') || 'core engineering workflows'}, delivering measurable results and seamless collaboration.`,
          `I hold valid work authorization in Germany and look forward to discussing how my experience will support ${job.company}.`,
        ];
      } else {
        this.studioLetterParagraphs = [
          `mit großem Interesse bewerbe ich mich auf die Position als ${job.role_title} bei ${job.company}. Mein Profil verbindet fundierte Fachkenntnisse mit lösungsorientierter Praxis.`,
          `In meiner bisherigen Tätigkeit habe ich Projekte mit Schwerpunkt auf ${job.extracted_skills?.slice(0, 3).join(', ') || 'Schlüsselbereichen'} erfolgreich geleitet.`,
          `Ich verfüge über eine uneingeschränkte Arbeitserlaubnis und freue mich auf ein persönliches Kennenlernen.`,
        ];
      }

      this.renderHtmlPreview();
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
          alert('AI suggestions applied to cover letter and rendered in preview!');
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

    async copyFormattedForGoogleDocs() {
      try {
        const res = await fetch(`${API_BASE}/api/export/google-docs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            company: this.studioJob.company,
            lang: this.studioLang,
          }),
        });
        const data = await res.json();
        if (data.text) {
          navigator.clipboard.writeText(data.text);
          alert('Formatted CV copied to clipboard! You can now paste directly into Google Docs or Word (Ctrl+V).');
        }
      } catch (err) {
        alert('Error copying for Google Docs: ' + err.message);
      }
    },

    async exportToGoogleDriveDoc() {
      if (!this.googleWebhookUrl) {
        alert('Google Webhook URL not set. Please configure it in Step 1 (Profile & Drive).');
        this.currentStep = 1;
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/export/google-docs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            company: this.studioJob.company,
            webhook_url: this.googleWebhookUrl,
            lang: this.studioLang,
          }),
        });
        const data = await res.json();
        if (data.doc_url) {
          window.open(data.doc_url, '_blank');
        } else {
          alert('Document created in Google Drive!');
        }
      } catch (err) {
        alert('Error saving to Google Drive: ' + err.message);
      }
    },

    async syncActiveJobToGoogleSheet() {
      if (!this.googleWebhookUrl) {
        alert('Google Webhook URL not set. Please configure it in Step 1 (Profile & Drive).');
        this.currentStep = 1;
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/export/google-sheets`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            webhook_url: this.googleWebhookUrl,
            job_data: this.studioJob,
            candidate_name: this.profileData.personal?.full_name || 'Applicant',
            fit_score: this.analysisResult?.match_result?.match_score ? `${this.analysisResult.match_result.match_score}%` : '',
          }),
        });
        const data = await res.json();
        alert('Job logged to your Google Sheet Tracker successfully!');
      } catch (err) {
        alert('Error syncing to Google Sheet: ' + err.message);
      }
    },

    async testGoogleSync() {
      if (!this.googleWebhookUrl) {
        alert('Please enter a Google Apps Script Webhook URL first.');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/export/google-sheets`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            webhook_url: this.googleWebhookUrl,
            job_data: { company: 'Test Company', role_title: 'Test Position', location: 'Hamburg' },
            candidate_name: this.profileData.personal?.full_name || 'Test User',
            fit_score: '100%',
          }),
        });
        const data = await res.json();
        if (data.status === 'success' || data.message) {
          alert('Google Sheets & Drive connection verified successfully!');
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
            company: this.outreachForm.company,
            contact_name: this.outreachForm.contact_name,
            role_title: this.outreachForm.role_title,
            outreach_type: this.outreachForm.outreach_type,
          }),
        });
        const data = await res.json();
        this.generatedPitchText = data.pitch;
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
