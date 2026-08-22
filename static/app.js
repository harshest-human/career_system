function getApiBase() {
  if (window.location.protocol === 'file:') {
    return 'http://localhost:8000';
  }
  return '';
}

const API_BASE = getApiBase();

function careerApp() {
  return {
    activeTab: 'jobs',
    serverConnected: false,
    profiles: [],
    activeProfileId: 'harsh',
    profileData: { personal: {}, executive_summary: {}, experience: [], education: [], skills: {} },
    jobsList: [],
    scrapeUrlInput: '',
    analysisResult: null,
    
    // Studio state
    studioJob: { company: 'Target Company', role_title: 'Position', location: 'Hamburg, Germany', extracted_skills: [] },
    studioLang: 'en',
    userFitNotes: '',
    studioSummary: '',
    studioLetterParagraphs: ['', '', ''],
    generatedPdfs: { cv: null, letter: null },

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
      this.$watch('geminiApiKey', (val) => localStorage.setItem('gemini_api_key', val));

      // Periodic health check
      setInterval(() => this.checkServer(), 8000);
    },

    async checkServer() {
      try {
        const res = await fetch(`${API_BASE}/api/health`);
        if (res.ok) {
          this.serverConnected = true;
        } else {
          this.serverConnected = false;
        }
      } catch (err) {
        this.serverConnected = false;
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
        alert('Server is offline. Please launch "start_web.bat" on your PC to connect to http://localhost:8000.');
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
          const errData = await res.json().catch(() => ({}));
          alert('Error saving profile: ' + (errData.detail || res.statusText));
        }
      } catch (err) {
        alert('Connection error: Cannot reach the local server at http://localhost:8000.\n\nPlease make sure start_web.bat is running.');
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
      if (!this.serverConnected) {
        alert('Server is offline. Please launch start_web.bat.');
        return;
      }
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
          alert('Job posting scraped and archived successfully!');
        } else {
          alert('Scraping error: ' + (data.detail || 'Failed to scrape URL'));
        }
      } catch (err) {
        alert('Connection error: Make sure start_web.bat is running.');
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
        if (res.ok) {
          await this.loadJobs();
          alert('Job PDF uploaded and parsed successfully!');
        } else {
          alert('Upload failed: ' + res.statusText);
        }
      } catch (err) {
        alert('Connection error: Make sure start_web.bat is running.');
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
          this.activeTab = 'analyzer';
        } else {
          alert('Analysis error: ' + res.statusText);
        }
      } catch (err) {
        alert('Connection error: Make sure start_web.bat is running.');
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
          `I am writing to express my strong interest in the ${job.role_title} position at ${job.company}. My technical background and applied research directly align with your team's mission.`,
          `At ${this.profileData.experience?.[0]?.institution_en || 'my current position'}, I have led initiatives involving ${job.extracted_skills?.slice(0, 3).join(', ') || 'key engineering domains'}, delivering measurable results.`,
          `I hold valid work authorization in Germany and look forward to discussing how my experience will support ${job.company}.`,
        ];
      } else {
        this.studioLetterParagraphs = [
          `mit großem Interesse bewerbe ich mich auf die Position als ${job.role_title} bei ${job.company}. Mein Profil verbindet fundierte Fachkenntnisse mit lösungsorientierter Praxis.`,
          `In meiner bisherigen Tätigkeit bei ${this.profileData.experience?.[0]?.institution_de || 'meinem aktuellen Arbeitgeber'} habe ich Projekte mit Schwerpunkt auf ${job.extracted_skills?.slice(0, 3).join(', ') || 'Schlüsselbereichen'} erfolgreich geleitet.`,
          `Ich verfüge über eine uneingeschränkte Arbeitserlaubnis und freue mich auf ein persönliches Kennenlernen.`,
        ];
      }

      this.activeTab = 'studio';
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
          alert('AI Suggestions generated! Cover letter paragraphs updated.');
        }
      } catch (err) {
        alert('Error requesting suggestions: ' + err);
      }
    },

    async compileDocuments() {
      if (!this.serverConnected) {
        alert('Server is offline. Please launch start_web.bat to connect.');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/compile`, {
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
        if (!res.ok) {
          const errText = await res.text();
          let msg = errText;
          try {
            const errJson = JSON.parse(errText);
            msg = errJson.detail || errJson.message || errText;
          } catch (_) {}
          alert('Compilation error: ' + msg);
          return;
        }
        const data = await res.json();
        if (data.cv_pdf) {
          this.generatedPdfs.cv = (API_BASE ? API_BASE : '') + data.cv_pdf + '?t=' + Date.now();
          this.generatedPdfs.letter = data.letter_pdf ? (API_BASE ? API_BASE : '') + data.letter_pdf + '?t=' + Date.now() : null;
          alert('LaTeX Compilation successful! Preview updated on the right.');
        } else {
          alert('LaTeX Compilation completed without producing PDF files. Check your LaTeX installation.');
        }
      } catch (err) {
        alert('Compilation error: ' + err.message);
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
        alert('Error generating outreach: ' + err);
      }
    },

    copyPitchToClipboard() {
      if (!this.generatedPitchText) return;
      navigator.clipboard.writeText(this.generatedPitchText);
      alert('Copied to clipboard!');
    },
  };
}
