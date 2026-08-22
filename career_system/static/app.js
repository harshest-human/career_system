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
    profileData: {
      personal: {
        full_name: '',
        title_en: '',
        title_de: '',
        email: '',
        phone: '',
        city_en: '',
        linkedin_url: '',
        github_url: '',
        residence_status: 'Full Work Authorization in Germany / EU'
      },
      executive_summary: { en: '', de: '' },
      experience: [],
      education: [],
      skills: { domains: [], software_tools: [], hardware_instruments: [], languages: [] },
      leadership_awards: []
    },
    jobsList: [],

    // Account Creation Modal
    showNewAccountModal: false,
    newAccountName: '',

    // Google Sync
    googleWebhookUrl: localStorage.getItem('google_webhook_url') || '',
    showGoogleScriptModal: false,
    googleScriptCode: '',

    // Gemini API Connection
    geminiApiKey: localStorage.getItem('gemini_api_key') || '',
    geminiConnected: false,
    geminiStatusText: 'Offline Mode',
    isTestingGemini: false,
    geminiTestMessage: '',

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

    // Studio state
    studioJob: {
      id: null,
      company: 'Target Company',
      role_title: 'Position',
      location: 'Hamburg, Germany',
      extracted_skills: []
    },
    studioDocType: 'cv',
    studioLang: 'en',
    userFitNotes: '',
    studioSummary: '',
    studioLetterParagraphs: [
      'I am writing to express my enthusiastic application for this role...',
      'My technical background directly aligns with your core requirements...',
      'I look forward to discussing how my experience will support your goals.'
    ],
    studioProfile: null,
    currentHtmlContent: '',
    isTailoring: false,
    cvEditorTab: 'summary',
    cvSkillsString: { domains: '', software: '', hardware: '', languages: '' },
    cvCredentialsString: '',

    // Outreach state
    outreachPitches: {
      linkedin_connection: '',
      linkedin_inmail: '',
      cold_email_subject: '',
      cold_email_body: ''
    },

    // Settings
    showSettingsModal: false,

    async init() {
      await this.checkServer();
      await this.loadProfiles();
      await this.loadJobs();
      await this.loadGoogleScriptTemplate();
      await this.testGeminiConnection(false);

      this.$watch('geminiApiKey', (val) => {
        localStorage.setItem('gemini_api_key', val);
      });
      this.$watch('googleWebhookUrl', (val) => {
        localStorage.setItem('google_webhook_url', val);
      });

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

    async testGeminiConnection(showNotice = true) {
      const key = this.geminiApiKey ? this.geminiApiKey.trim() : '';
      if (!key) {
        this.geminiConnected = false;
        this.geminiStatusText = 'Offline Mode';
        if (showNotice) {
          this.geminiTestMessage = 'No Gemini API key provided. System is operating in offline mode.';
        }
        return;
      }

      this.isTestingGemini = true;
      try {
        const res = await fetch(`${API_BASE}/api/ai/test-key`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: key })
        });
        if (res.ok) {
          const data = await res.json();
          this.geminiConnected = data.connected;
          if (data.connected) {
            this.geminiStatusText = `Gemini Active (${data.model})`;
            this.geminiTestMessage = `✓ ${data.message}`;
          } else {
            this.geminiStatusText = 'Key Error';
            this.geminiTestMessage = data.message;
          }
        }
      } catch (err) {
        this.geminiConnected = false;
        this.geminiStatusText = 'Offline Mode';
        this.geminiTestMessage = `Could not reach server: ${err.message}`;
      } finally {
        this.isTestingGemini = false;
      }
    },

    async testAndSaveGeminiKey() {
      await this.testGeminiConnection(true);
      if (this.geminiConnected) {
        localStorage.setItem('gemini_api_key', this.geminiApiKey);
      }
    },

    async loadGoogleScriptTemplate() {
      try {
        const res = await fetch(`${API_BASE}/api/google/script-template`);
        if (res.ok) {
          const data = await res.json();
          this.googleScriptCode = data.script || '';
        }
      } catch (err) {
        console.warn('Could not load script template:', err);
      }
    },

    async testGoogleSync() {
      if (!this.googleWebhookUrl) {
        alert('Please enter your Google Apps Script Webhook URL first.');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/google/test-sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ webhook_url: this.googleWebhookUrl })
        });
        const data = await res.json();
        if (data.status === 'success') {
          alert('✓ Google Drive sync successful! Test file created in Drive.');
        } else {
          alert(`Sync error: ${data.message || 'Check Apps Script deployment.'}`);
        }
      } catch (err) {
        alert(`Failed to test Google Sync: ${err.message}`);
      }
    },

    async loadProfiles() {
      try {
        const res = await fetch(`${API_BASE}/api/profiles`);
        if (res.ok) {
          this.profiles = await res.json();
          if (this.profiles.length > 0) {
            const hasActive = this.profiles.some((p) => p.id === this.activeProfileId);
            if (!hasActive) {
              this.activeProfileId = this.profiles[0].id;
            }
            await this.loadActiveProfile();
          }
        }
      } catch (err) {
        console.error('Error loading profiles:', err);
      }
    },

    async loadActiveProfile() {
      try {
        const res = await fetch(`${API_BASE}/api/profiles/${this.activeProfileId}`);
        if (res.ok) {
          const data = await res.json();
          this.profileData = data.data || this.profileData;
          this.syncMasterProfileToStrings();
          if (!this.studioProfile) {
            this.studioProfile = JSON.parse(JSON.stringify(this.profileData));
          }
        }
      } catch (err) {
        console.error('Error loading active profile:', err);
      }
    },

    syncMasterProfileToStrings() {
      const skills = this.profileData.skills || {};
      this.cvSkillsString = {
        domains: (skills.domains || []).join(', '),
        software: (skills.software_tools || []).join(', '),
        hardware: (skills.hardware_instruments || []).join(', '),
        languages: (skills.languages || []).join(', ')
      };
      this.cvCredentialsString = (this.profileData.leadership_awards || []).join('\n');
    },

    syncSkillsToMasterProfile() {
      if (!this.profileData.skills) this.profileData.skills = {};
      this.profileData.skills.domains = this.cvSkillsString.domains.split(',').map((s) => s.trim()).filter(Boolean);
      this.profileData.skills.software_tools = this.cvSkillsString.software.split(',').map((s) => s.trim()).filter(Boolean);
      this.profileData.skills.hardware_instruments = this.cvSkillsString.hardware.split(',').map((s) => s.trim()).filter(Boolean);
      this.profileData.skills.languages = this.cvSkillsString.languages.split(',').map((s) => s.trim()).filter(Boolean);
      this.profileData.leadership_awards = this.cvCredentialsString.split('\n').map((s) => s.trim()).filter(Boolean);
    },

    syncSkillsToStudioProfile() {
      if (!this.studioProfile) return;
      if (!this.studioProfile.skills) this.studioProfile.skills = {};
      this.studioProfile.skills.domains = this.cvSkillsString.domains.split(',').map((s) => s.trim()).filter(Boolean);
      this.studioProfile.skills.software_tools = this.cvSkillsString.software.split(',').map((s) => s.trim()).filter(Boolean);
      this.studioProfile.skills.hardware_instruments = this.cvSkillsString.hardware.split(',').map((s) => s.trim()).filter(Boolean);
      this.studioProfile.skills.languages = this.cvSkillsString.languages.split(',').map((s) => s.trim()).filter(Boolean);
      this.renderHtmlPreview();
    },

    async saveProfile() {
      this.syncSkillsToMasterProfile();
      try {
        const res = await fetch(`${API_BASE}/api/profiles/${this.activeProfileId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.profileData)
        });
        if (res.ok) {
          alert('✓ Master CV saved successfully!');
        } else {
          alert('Failed to save Master CV.');
        }
      } catch (err) {
        alert(`Error saving profile: ${err.message}`);
      }
    },

    async createNewProfile() {
      if (!this.newAccountName.trim()) return;
      try {
        const res = await fetch(`${API_BASE}/api/profiles`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: this.newAccountName.trim() })
        });
        if (res.ok) {
          const created = await res.json();
          this.showNewAccountModal = false;
          this.newAccountName = '';
          await this.loadProfiles();
          this.activeProfileId = created.id;
          await this.loadActiveProfile();
        }
      } catch (err) {
        alert(`Error creating profile: ${err.message}`);
      }
    },

    addMasterExperience() {
      if (!this.profileData.experience) this.profileData.experience = [];
      this.profileData.experience.unshift({
        role_en: 'Position Title',
        role_de: 'Positionsbezeichnung',
        institution_en: 'Company Name',
        institution_de: 'Company Name',
        period_en: '2023 - Present',
        period_de: '2023 - Heute',
        affiliation: 'Location',
        bullets: ['Accomplished key project deliverable with measurable outcome.']
      });
    },

    removeMasterExperience(idx) {
      if (confirm('Delete this position from your Master CV?')) {
        this.profileData.experience.splice(idx, 1);
      }
    },

    addMasterExperienceBullet(expIdx) {
      if (!this.profileData.experience[expIdx].bullets) {
        this.profileData.experience[expIdx].bullets = [];
      }
      this.profileData.experience[expIdx].bullets.push('New accomplishment or methodology bullet.');
    },

    removeMasterExperienceBullet(expIdx, bIdx) {
      this.profileData.experience[expIdx].bullets.splice(bIdx, 1);
    },

    addMasterEducation() {
      if (!this.profileData.education) this.profileData.education = [];
      this.profileData.education.push({
        degree_en: 'Master of Science (M.Sc.)',
        degree_de: 'Master of Science (M.Sc.)',
        institution: 'University Name',
        period_en: '2020 - 2022',
        period_de: '2020 - 2022',
        notes_en: 'Graduated with Distinction'
      });
    },

    removeMasterEducation(idx) {
      this.profileData.education.splice(idx, 1);
    },

    async loadJobs() {
      try {
        const res = await fetch(`${API_BASE}/api/jobs`);
        if (res.ok) {
          this.jobsList = await res.json();
        }
      } catch (err) {
        console.error('Error loading jobs:', err);
      }
    },

    async updateJobStatus(jobId, newStatus) {
      try {
        await fetch(`${API_BASE}/api/jobs/${jobId}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
      } catch (err) {
        console.error('Error updating status:', err);
      }
    },

    async deleteJob(jobId) {
      if (!confirm('Are you sure you want to delete this job and its files?')) return;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, { method: 'DELETE' });
        if (res.ok) {
          if (this.analysisResult && this.analysisResult.job.id === jobId) {
            this.analysisResult = null;
          }
          await this.loadJobs();
        }
      } catch (err) {
        alert(`Error deleting job: ${err.message}`);
      }
    },

    async scrapeJobUrl() {
      if (!this.scrapeUrlInput.trim()) return;
      this.isLoadingBreakdown = true;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/scrape`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: this.scrapeUrlInput.trim(),
            candidate_id: this.activeProfileId,
            gemini_api_key: this.geminiApiKey
          })
        });
        if (!res.ok) {
          const errText = await res.text();
          throw new Error(errText);
        }
        const data = await res.json();
        await this.loadJobs();
        this.scrapeUrlInput = '';
        this.handleIngestionSuccess(data);
      } catch (err) {
        alert(`Error scraping job: ${err.message}`);
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
      formData.append('candidate_id', this.activeProfileId);

      try {
        const res = await fetch(`${API_BASE}/api/jobs/upload`, {
          method: 'POST',
          body: formData
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        await this.loadJobs();
        this.handleIngestionSuccess(data);
      } catch (err) {
        alert(`Error uploading PDF: ${err.message}`);
      } finally {
        this.isLoadingBreakdown = false;
      }
    },

    async parseRawJobText() {
      if (!this.rawJobTextInput.trim()) return;
      this.isLoadingBreakdown = true;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/parse-text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            raw_text: this.rawJobTextInput.trim(),
            candidate_id: this.activeProfileId,
            gemini_api_key: this.geminiApiKey
          })
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        await this.loadJobs();
        this.rawJobTextInput = '';
        this.handleIngestionSuccess(data);
      } catch (err) {
        alert(`Error parsing job text: ${err.message}`);
      } finally {
        this.isLoadingBreakdown = false;
      }
    },

    handleIngestionSuccess(res) {
      const jobData = res.data;
      jobData.id = res.job_id;
      this.analysisResult = { job: jobData };
      this.selectJobForStudio(jobData);

      if (res.tailored) {
        if (res.tailored.tailored_profile) {
          this.studioProfile = JSON.parse(JSON.stringify(res.tailored.tailored_profile));
        }
        if (res.tailored.cover_letter_paragraphs) {
          this.studioLetterParagraphs = res.tailored.cover_letter_paragraphs[this.studioLang] || res.tailored.cover_letter_paragraphs.en;
        }
        if (res.tailored.outreach) {
          this.outreachPitches = res.tailored.outreach;
        }
      }

      this.loadJobFiles(res.job_id);
    },

    async selectJobForAnalysis(job) {
      this.analysisResult = { job: job };
      await this.loadJobFiles(job.id);
    },

    async selectJobForStudio(job) {
      this.studioJob = JSON.parse(JSON.stringify(job));
      if (!this.studioProfile) {
        this.studioProfile = JSON.parse(JSON.stringify(this.profileData));
      }
      this.onLanguageChange();
      await this.loadJobFiles(job.id);
      await this.renderHtmlPreview();
    },

    async loadJobFiles(jobId) {
      if (!jobId) return;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/files`);
        if (res.ok) {
          this.jobFilesList = await res.json();
        }
      } catch (err) {
        console.error('Error loading job files:', err);
      }
    },

    onLanguageChange() {
      if (!this.studioProfile) {
        this.studioProfile = JSON.parse(JSON.stringify(this.profileData));
      }
      const summaryObj = this.studioProfile.executive_summary || {};
      this.studioSummary = summaryObj[this.studioLang] || summaryObj.en || '';
      this.renderHtmlPreview();
    },

    resetToMasterCv() {
      if (confirm('Reset this job studio back to your baseline Master CV?')) {
        this.studioProfile = JSON.parse(JSON.stringify(this.profileData));
        this.onLanguageChange();
      }
    },

    async tailorWithGemini() {
      this.isTailoring = true;
      try {
        const res = await fetch(`${API_BASE}/api/ai/tailor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            job_data: this.studioJob,
            user_notes: this.userFitNotes,
            lang: this.studioLang,
            gemini_api_key: this.geminiApiKey
          })
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();

        if (data.tailored_profile) {
          this.studioProfile = data.tailored_profile;
          this.onLanguageChange();
        }
        if (data.cover_letter_paragraphs) {
          this.studioLetterParagraphs = data.cover_letter_paragraphs[this.studioLang] || data.cover_letter_paragraphs.en || this.studioLetterParagraphs;
        }
        if (data.outreach) {
          this.outreachPitches = data.outreach;
        }

        await this.renderHtmlPreview();
        if (this.studioJob.id) {
          await this.loadJobFiles(this.studioJob.id);
        }
        alert('✓ Gemini successfully tailored your application documents & pitches!');
      } catch (err) {
        alert(`Tailoring error: ${err.message}`);
      } finally {
        this.isTailoring = false;
      }
    },

    addStudioExperience() {
      if (!this.studioProfile.experience) this.studioProfile.experience = [];
      this.studioProfile.experience.unshift({
        role_en: 'Tailored Position Title',
        role_de: 'Positionsbezeichnung',
        institution_en: 'Company Name',
        institution_de: 'Company Name',
        period_en: '2023 - Present',
        period_de: '2023 - Heute',
        affiliation: 'Location',
        bullets: ['Tailored accomplishment bullet aligning directly with job requirements.']
      });
      this.renderHtmlPreview();
    },

    removeStudioExperience(idx) {
      this.studioProfile.experience.splice(idx, 1);
      this.renderHtmlPreview();
    },

    addStudioExperienceBullet(expIdx) {
      if (!this.studioProfile.experience[expIdx].bullets) {
        this.studioProfile.experience[expIdx].bullets = [];
      }
      this.studioProfile.experience[expIdx].bullets.push('Tailored bullet matching job description.');
      this.renderHtmlPreview();
    },

    removeStudioExperienceBullet(expIdx, bIdx) {
      this.studioProfile.experience[expIdx].bullets.splice(bIdx, 1);
      this.renderHtmlPreview();
    },

    async renderHtmlPreview() {
      if (!this.studioProfile) return;
      if (!this.studioProfile.executive_summary) this.studioProfile.executive_summary = {};
      this.studioProfile.executive_summary[this.studioLang] = this.studioSummary;

      try {
        const res = await fetch(`${API_BASE}/api/generate-html`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: this.activeProfileId,
            job_data: this.studioJob,
            lang: this.studioLang,
            custom_summary: this.studioSummary,
            custom_letter_paragraphs: this.studioLetterParagraphs,
            custom_profile: this.studioProfile
          })
        });
        if (res.ok) {
          const data = await res.json();
          this.currentHtmlContent = this.studioDocType === 'cv' ? data.cv_html : data.cover_letter_html;
        }
      } catch (err) {
        console.error('Error rendering HTML preview:', err);
      }
    },

    printHtmlDocument() {
      const iframe = document.getElementById('previewIframe');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } else {
        window.print();
      }
    },

    async openJobLocalFolder(jobId) {
      if (!jobId) return;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/open-folder`, { method: 'POST' });
        const data = await res.json();
        if (data.status !== 'success') {
          alert('Could not open folder automatically. Please navigate to the job folder in Windows Explorer.');
        }
      } catch (err) {
        alert(`Failed to open folder: ${err.message}`);
      }
    },

    async uploadJobToGoogleDrive(jobId) {
      if (!jobId) return;
      if (!this.googleWebhookUrl) {
        alert('Please configure your Google Apps Script Webhook URL in Step 1 first.');
        this.currentStep = 1;
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/sync-drive`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ webhook_url: this.googleWebhookUrl })
        });
        const data = await res.json();
        if (data.status === 'success') {
          alert(`✓ Folder successfully synced to Google Drive!\nURL: ${data.folder_url || 'Google Drive'}`);
        } else {
          alert(`Sync error: ${data.message || 'Check Apps Script deployment.'}`);
        }
      } catch (err) {
        alert(`Failed to upload to Google Drive: ${err.message}`);
      }
    },

    openPdfViewer(path, title) {
      this.activePdfViewerUrl = path;
      this.activePdfViewerTitle = title || 'Job Description PDF';
      this.showPdfViewerModal = true;
    },

    openFileViewer(path, name) {
      this.activePdfViewerUrl = path;
      this.activePdfViewerTitle = name;
      this.showPdfViewerModal = true;
    },

    async saveJobChanges() {
      if (!this.analysisResult || !this.analysisResult.job.id) return;
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${this.analysisResult.job.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.analysisResult.job)
        });
        if (res.ok) {
          alert('✓ Job details saved.');
          await this.loadJobs();
        }
      } catch (err) {
        alert(`Error saving job: ${err.message}`);
      }
    },

    copyToClipboard(text) {
      if (!text) return;
      navigator.clipboard.writeText(text).then(
        () => alert('✓ Copied to clipboard!'),
        () => alert('Could not copy to clipboard.')
      );
    }
  };
}
