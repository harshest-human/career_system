function careerApp() {
  return {
    activeTab: 'jobs',
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
      await this.loadProfiles();
      await this.loadJobs();
      this.$watch('geminiApiKey', (val) => localStorage.setItem('gemini_api_key', val));
    },

    async loadProfiles() {
      try {
        const res = await fetch('/api/profiles');
        this.profiles = await res.json();
        if (this.profiles.length > 0) {
          this.activeProfileId = this.profiles[0].id;
          await this.loadActiveProfile();
        }
      } catch (err) {
        console.error('Error loading profiles:', err);
      }
    },

    async loadActiveProfile() {
      try {
        const res = await fetch(`/api/profiles/${this.activeProfileId}`);
        const data = await res.json();
        this.profileData = data.data || {};
        this.studioSummary = this.profileData.executive_summary?.[this.studioLang] || '';
      } catch (err) {
        console.error('Error loading active profile:', err);
      }
    },

    async saveProfile() {
      try {
        const res = await fetch(`/api/profiles/${this.activeProfileId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.profileData),
        });
        if (res.ok) {
          alert('Profile saved and synced successfully!');
        }
      } catch (err) {
        alert('Error saving profile: ' + err);
      }
    },

    async loadJobs() {
      try {
        const res = await fetch('/api/jobs');
        this.jobsList = await res.json();
      } catch (err) {
        console.error('Error loading jobs:', err);
      }
    },

    async scrapeJobUrl() {
      if (!this.scrapeUrlInput) return;
      try {
        const res = await fetch('/api/jobs/scrape', {
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
          alert('Scraping error: ' + data.detail);
        }
      } catch (err) {
        alert('Error: ' + err);
      }
    },

    async uploadJobPdf(event) {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/api/jobs/upload', {
          method: 'POST',
          body: formData,
        });
        if (res.ok) {
          await this.loadJobs();
          alert('Job PDF uploaded and parsed successfully!');
        }
      } catch (err) {
        alert('Error uploading PDF: ' + err);
      }
    },

    async updateJobStatus(jobId, status) {
      try {
        await fetch(`/api/jobs/${jobId}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status }),
        });
      } catch (err) {
        console.error('Error updating status:', err);
      }
    },

    async selectJobForAnalysis(job) {
      try {
        const res = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ candidate_id: this.activeProfileId, job_id: job.id }),
        });
        this.analysisResult = await res.json();
        this.activeTab = 'analyzer';
      } catch (err) {
        alert('Error analyzing job: ' + err);
      }
    },

    selectJobForStudio(job) {
      this.studioJob = job;
      this.studioSummary = this.profileData.executive_summary?.[this.studioLang] || '';
      this.outreachForm.company = job.company || '';
      this.outreachForm.role_title = job.role_title || '';
      this.outreachForm.contact_name = 'Hiring Team';

      // Default paragraphs
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
        const res = await fetch('/api/ai/suggest', {
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
      try {
        const res = await fetch('/api/compile', {
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
        if (data.cv_pdf) {
          this.generatedPdfs.cv = data.cv_pdf + '?t=' + Date.now();
          this.generatedPdfs.letter = data.letter_pdf ? data.letter_pdf + '?t=' + Date.now() : null;
        } else {
          alert('LaTeX Compilation finished. Check outputs directory.');
        }
      } catch (err) {
        alert('Compilation error: ' + err);
      }
    },

    async generatePitchMessage() {
      try {
        const res = await fetch('/api/outreach/generate', {
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
