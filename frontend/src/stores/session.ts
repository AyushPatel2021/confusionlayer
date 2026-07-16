import { defineStore } from "pinia";

type Role =
  | "admin"
  | "owner"
  | "school_admin"
  | "accountant"
  | "hr"
  | "teacher"
  | "student"
  | "parent"
  | "platform_admin";

interface User {
  id: number;
  email: string;
  role: Role;
  name: string | null;
  org_id: number | null;
  org_name: string | null;
  segment: string | null;
}

export interface InvitationPreview {
  email: string;
  role: string;
  organization_name: string;
}

interface Subject {
  id: number;
  name: string;
  board: string;
  class_level: string;
}

interface Classroom {
  id: number;
  name: string;
  subject: Subject;
}

export interface ConceptSummary {
  id: number;
  title: string;
  order: number;
  locked: boolean;
}

export interface ChapterSummary {
  id: number;
  title: string;
  order: number;
  locked: boolean;
  concepts: ConceptSummary[];
}

interface Syllabus {
  classroom: Classroom;
  chapters: ChapterSummary[];
}

interface ConceptDetail {
  id: number;
  title: string;
  order: number;
  chapter_id: number;
  chapter_title: string;
  subject: Subject;
  taxonomy: Array<{ code: string; description: string }>;
}

interface Tutorial {
  explanation: string;
  worked_example: string;
}

interface ChatMessage {
  role: "student" | "assistant";
  content: string;
  response_type?: string;
}

interface DoubtChatResponse {
  response: string;
  response_type: string;
}

interface QuizGrade {
  is_correct: boolean;
  misconception_code: string | null;
  misconception_summary: string;
  confidence: number;
  follow_up_question: string;
  attempt_id: number;
}

interface TeachBackGrade {
  clarity_score: number;
  accuracy_score: number;
  gap_identified: string;
  encouragement: string;
  attempt_id: number;
}

export interface MisconceptionCluster {
  code: string;
  description: string;
  student_count: number;
}

export interface ConfusionConcept {
  concept_id: number;
  concept_title: string;
  chapter_title: string;
  affected_student_count: number;
  misconceptions: MisconceptionCluster[];
}

export interface ConfusionBrief {
  classroom_id: number;
  total_students: number;
  privacy_threshold: number;
  concepts: ConfusionConcept[];
}

export interface ForecastContributor {
  concept_id: number;
  title: string;
  average_effective_mastery: number;
  mention_count: number;
}

export interface ForecastConcept {
  concept_id: number;
  concept_title: string;
  chapter_title: string;
  at_risk_count: number;
  total_students: number;
  average_difficulty: number;
  top_contributors: ForecastContributor[];
}

export interface ForecastBrief {
  classroom_id: number;
  total_students: number;
  at_risk_threshold: number;
  computed_at: string | null;
  concepts: ForecastConcept[];
}

export interface BriefNarrative {
  concept_id: number;
  concept_title: string;
  summary: string;
  suggested_activity: string;
}

export interface ProgressPoint {
  recorded_at: string;
  mastery: number;
}

export interface ProgressConcept {
  concept_id: number;
  concept_title: string;
  chapter_title: string;
  current_mastery: number;
  effective_mastery: number;
  history: ProgressPoint[];
}

export interface StudentProgress {
  student_name: string;
  mastered_threshold: number;
  summary: {
    concept_count: number;
    mastered_count: number;
    average_effective_mastery: number;
  };
  concepts: ProgressConcept[];
}

export interface CurriculumSubject {
  id: number;
  name: string;
  board: string;
  class_level: string;
  org_id: number | null;
  shared: boolean;
  chapter_count: number;
}

export interface CurriculumConceptNode {
  id: number;
  title: string;
  order: number;
}

export interface CurriculumChapterNode {
  id: number;
  title: string;
  order: number;
  concepts: CurriculumConceptNode[];
}

export interface CurriculumTree {
  id: number;
  name: string;
  board: string;
  class_level: string;
  org_id: number | null;
  chapters: CurriculumChapterNode[];
}

export interface DraftChapter {
  title: string;
  topics: string[];
}

export interface OrgPlan {
  code: string;
  name: string;
  segment: string;
  price_cents: number;
  limits: Record<string, number>;
  features: string[];
}

export interface OrgInfo {
  id: number;
  name: string;
  slug: string;
  segment: string;
  subscription: { status: string; plan: OrgPlan | null } | null;
  usage: { members: number; students: number; classrooms: number };
}

export interface OrgMember {
  id: number;
  name: string | null;
  email: string;
  role: string;
  status: string;
}

export interface PendingInvite {
  id: number;
  email: string;
  role: string;
}

export interface AdmissionApplication {
  id: number;
  applicant_name: string;
  applicant_email: string | null;
  grade: string | null;
  notes: string | null;
  status: string;
  student_id: number | null;
  created_at: string;
  updated_at: string;
}

interface AuthResponse {
  access_token: string;
  user: User;
}

const tokenKey = "confusionlayer.token";

export const useSessionStore = defineStore("session", {
  state: () => ({
    token: localStorage.getItem(tokenKey) || "",
    user: null as User | null,
    syllabus: null as Syllabus | null,
    selectedConcept: null as ConceptDetail | null,
    tutorial: null as Tutorial | null,
    activeTool: "tutorial" as "tutorial" | "doubt" | "quiz" | "teach_back",
    chatMessages: [] as ChatMessage[],
    quizGrade: null as QuizGrade | null,
    teachBackGrade: null as TeachBackGrade | null,
    forecastBrief: null as ForecastBrief | null,
    confusionBrief: null as ConfusionBrief | null,
    forecastNarratives: {} as Record<number, BriefNarrative>,
    confusionNarratives: {} as Record<number, BriefNarrative>,
    selfStartTutorial: null as Tutorial | null,
    progress: null as StudentProgress | null,
    curriculumSubjects: [] as CurriculumSubject[],
    curriculumTree: null as CurriculumTree | null,
    importDraft: null as DraftChapter[] | null,
    org: null as OrgInfo | null,
    members: [] as OrgMember[],
    pendingInvites: [] as PendingInvite[],
    plans: [] as OrgPlan[],
    applications: [] as AdmissionApplication[],
    loading: "",
    error: "",
  }),
  getters: {
    // Staff-side roles that use the teacher learning views.
    isTeacher: (state) =>
      ["teacher", "owner", "school_admin", "admin"].includes(state.user?.role ?? ""),
    isStudent: (state) => state.user?.role === "student",
    isAdmin: (state) => state.user?.role === "admin" || state.user?.role === "platform_admin",
    isOrgAdmin: (state) => ["owner", "school_admin", "admin"].includes(state.user?.role ?? ""),
    isOwner: (state) => state.user?.role === "owner" || state.user?.role === "admin",
    roleHome: (state) => (state.user?.role === "student" ? "/app/learn" : "/app/teacher"),
  },
  actions: {
    async demoLogin(role: "teacher" | "student") {
      this.loading = `demo-${role}`;
      this.error = "";
      try {
        const response = await api<AuthResponse>("/api/auth/demo", {
          method: "POST",
          body: JSON.stringify({ role }),
        });
        this.token = response.access_token;
        this.user = response.user;
        localStorage.setItem(tokenKey, response.access_token);
        this.selectedConcept = null;
        this.tutorial = null;
        this.chatMessages = [];
        this.quizGrade = null;
        this.teachBackGrade = null;
        this.forecastBrief = null;
        this.confusionBrief = null;
        this.forecastNarratives = {};
        this.confusionNarratives = {};
        this.selfStartTutorial = null;
        this.progress = null;
        await this.loadSyllabus();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    applyAuth(response: AuthResponse) {
      this.token = response.access_token;
      this.user = response.user;
      localStorage.setItem(tokenKey, response.access_token);
      this.selectedConcept = null;
      this.tutorial = null;
      this.chatMessages = [];
      this.quizGrade = null;
      this.teachBackGrade = null;
      this.forecastBrief = null;
      this.confusionBrief = null;
      this.forecastNarratives = {};
      this.confusionNarratives = {};
      this.selfStartTutorial = null;
      this.progress = null;
    },
    async register(payload: {
      org_name: string;
      segment: string;
      email: string;
      password: string;
      name: string;
    }): Promise<boolean> {
      this.loading = "register";
      this.error = "";
      try {
        const response = await api<AuthResponse>("/api/auth/register", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        this.applyAuth(response);
        await this.loadSyllabus().catch(() => undefined);
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async login(email: string, password: string): Promise<boolean> {
      this.loading = "login";
      this.error = "";
      try {
        const response = await api<AuthResponse>("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        this.applyAuth(response);
        await this.loadSyllabus().catch(() => undefined);
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async forgotPassword(email: string): Promise<boolean> {
      this.loading = "forgot";
      this.error = "";
      try {
        await api("/api/auth/password/forgot", { method: "POST", body: JSON.stringify({ email }) });
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async resetPassword(token: string, password: string): Promise<boolean> {
      this.loading = "reset";
      this.error = "";
      try {
        await api("/api/auth/password/reset", { method: "POST", body: JSON.stringify({ token, password }) });
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async fetchInvitation(token: string): Promise<InvitationPreview | null> {
      this.loading = "invitation";
      this.error = "";
      try {
        return await api<InvitationPreview>(`/api/auth/invitations/${token}`);
      } catch (error) {
        this.error = messageFromError(error);
        return null;
      } finally {
        this.loading = "";
      }
    },
    async acceptInvitation(token: string, password: string, name: string): Promise<boolean> {
      this.loading = "accept";
      this.error = "";
      try {
        const response = await api<AuthResponse>("/api/auth/invitations/accept", {
          method: "POST",
          body: JSON.stringify({ token, password, name }),
        });
        this.applyAuth(response);
        await this.loadSyllabus().catch(() => undefined);
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async restore() {
      if (!this.token || this.user) return;
      this.loading = "restore";
      try {
        const response = await api<AuthResponse>("/api/auth/me", { token: this.token });
        this.token = response.access_token;
        this.user = response.user;
        localStorage.setItem(tokenKey, response.access_token);
        await this.loadSyllabus();
      } catch {
        this.logout();
      } finally {
        this.loading = "";
      }
    },
    async loadSyllabus() {
      this.loading = "syllabus";
      this.error = "";
      try {
        this.syllabus = await api<Syllabus>("/api/student/syllabus", { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async unlockChapter(chapterId: number) {
      if (!this.syllabus) return;
      this.loading = `unlock-${chapterId}`;
      this.error = "";
      try {
        await api(`/api/teacher/classrooms/${this.syllabus.classroom.id}/chapters/${chapterId}/unlock`, {
          method: "POST",
          token: this.token,
        });
        await this.loadSyllabus();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async openConcept(concept: ConceptSummary) {
      if (concept.locked) return;
      await this.loadConceptById(concept.id);
    },
    async loadConceptById(conceptId: number) {
      this.loading = `concept-${conceptId}`;
      this.error = "";
      this.tutorial = null;
      this.chatMessages = [];
      this.quizGrade = null;
      this.teachBackGrade = null;
      this.activeTool = "tutorial";
      try {
        this.selectedConcept = await api<ConceptDetail>(`/api/concepts/${conceptId}`, { token: this.token });
      } catch (error) {
        this.selectedConcept = null;
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async generateTutorial() {
      if (!this.selectedConcept) return;
      this.loading = "tutorial";
      this.error = "";
      try {
        this.tutorial = await api<Tutorial>(`/api/concepts/${this.selectedConcept.id}/tutorial`, {
          method: "POST",
          token: this.token,
          body: JSON.stringify({ reading_level: "Class 10" }),
        });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async sendDoubt(message: string) {
      if (!this.selectedConcept || !message.trim()) return;
      this.loading = "doubt";
      this.error = "";
      const studentMessage: ChatMessage = { role: "student", content: message.trim() };
      const history = [...this.chatMessages, studentMessage].map((item) => ({ role: item.role, content: item.content }));
      this.chatMessages.push(studentMessage);
      try {
        const response = await api<DoubtChatResponse>(`/api/concepts/${this.selectedConcept.id}/doubt-chat`, {
          method: "POST",
          token: this.token,
          body: JSON.stringify({
            message: message.trim(),
            history,
            turn_count: this.chatMessages.filter((item) => item.role === "student").length,
          }),
        });
        this.chatMessages.push({ role: "assistant", content: response.response, response_type: response.response_type });
      } catch (error) {
        this.chatMessages.pop();
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async submitQuiz(question: string, studentAnswer: string, rubric: string) {
      if (!this.selectedConcept || !question.trim() || !studentAnswer.trim() || !rubric.trim()) return;
      this.loading = "quiz";
      this.error = "";
      this.quizGrade = null;
      try {
        this.quizGrade = await api<QuizGrade>(`/api/concepts/${this.selectedConcept.id}/quiz/grade`, {
          method: "POST",
          token: this.token,
          body: JSON.stringify({
            question: question.trim(),
            student_answer: studentAnswer.trim(),
            rubric: rubric.trim(),
          }),
        });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async submitTeachBack(studentExplanation: string, correctSummary: string) {
      if (!this.selectedConcept || !studentExplanation.trim() || !correctSummary.trim()) return;
      this.loading = "teach-back";
      this.error = "";
      this.teachBackGrade = null;
      try {
        this.teachBackGrade = await api<TeachBackGrade>(`/api/concepts/${this.selectedConcept.id}/teach-back/grade`, {
          method: "POST",
          token: this.token,
          body: JSON.stringify({
            student_explanation: studentExplanation.trim(),
            correct_summary: correctSummary.trim(),
          }),
        });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadForecastBrief() {
      if (!this.syllabus) return;
      this.loading = "forecast-brief";
      this.error = "";
      try {
        this.forecastBrief = await api<ForecastBrief>(
          `/api/teacher/classrooms/${this.syllabus.classroom.id}/forecast-brief`,
          { token: this.token },
        );
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadConfusionBrief() {
      if (!this.syllabus) return;
      this.loading = "confusion-brief";
      this.error = "";
      try {
        this.confusionBrief = await api<ConfusionBrief>(
          `/api/teacher/classrooms/${this.syllabus.classroom.id}/confusion-brief`,
          { token: this.token },
        );
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async recomputeForecasts() {
      if (!this.syllabus) return;
      this.loading = "recompute";
      this.error = "";
      try {
        await api(`/api/teacher/classrooms/${this.syllabus.classroom.id}/forecasts/recompute`, {
          method: "POST",
          token: this.token,
        });
        await this.loadForecastBrief();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async generateForecastNarrative(conceptId: number) {
      if (!this.syllabus) return;
      this.loading = `forecast-narrative-${conceptId}`;
      this.error = "";
      try {
        const narrative = await api<BriefNarrative>(
          `/api/teacher/classrooms/${this.syllabus.classroom.id}/forecast-brief/narrative`,
          { method: "POST", token: this.token, body: JSON.stringify({ concept_id: conceptId }) },
        );
        this.forecastNarratives = { ...this.forecastNarratives, [conceptId]: narrative };
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async generateConfusionNarrative(conceptId: number) {
      if (!this.syllabus) return;
      this.loading = `confusion-narrative-${conceptId}`;
      this.error = "";
      try {
        const narrative = await api<BriefNarrative>(
          `/api/teacher/classrooms/${this.syllabus.classroom.id}/confusion-brief/narrative`,
          { method: "POST", token: this.token, body: JSON.stringify({ concept_id: conceptId }) },
        );
        this.confusionNarratives = { ...this.confusionNarratives, [conceptId]: narrative };
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async generateSelfStart(topic: string, readingLevel = "Class 10") {
      if (!topic.trim()) return;
      this.loading = "self-start";
      this.error = "";
      this.selfStartTutorial = null;
      try {
        this.selfStartTutorial = await api<Tutorial>("/api/self-start/tutorial", {
          method: "POST",
          token: this.token,
          body: JSON.stringify({ topic: topic.trim(), reading_level: readingLevel }),
        });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadProgress() {
      this.loading = "progress";
      this.error = "";
      try {
        this.progress = await api<StudentProgress>("/api/student/progress", { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadCurriculumSubjects() {
      this.loading = "curriculum";
      this.error = "";
      try {
        this.curriculumSubjects = await api<CurriculumSubject[]>("/api/curriculum/subjects", { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadSubjectTree(subjectId: number) {
      this.loading = "curriculum-tree";
      this.error = "";
      try {
        this.curriculumTree = await api<CurriculumTree>(`/api/curriculum/subjects/${subjectId}`, { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async createSubject(payload: { name: string; board?: string; class_level?: string }): Promise<CurriculumSubject | null> {
      this.loading = "create-subject";
      this.error = "";
      try {
        const subject = await api<CurriculumSubject>("/api/curriculum/subjects", {
          method: "POST",
          token: this.token,
          body: JSON.stringify(payload),
        });
        await this.loadCurriculumSubjects();
        return subject;
      } catch (error) {
        this.error = messageFromError(error);
        return null;
      } finally {
        this.loading = "";
      }
    },
    async createChapter(subjectId: number, title: string) {
      this.loading = "create-chapter";
      this.error = "";
      try {
        await api(`/api/curriculum/subjects/${subjectId}/chapters`, { method: "POST", token: this.token, body: JSON.stringify({ title }) });
        await this.loadSubjectTree(subjectId);
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async createConcept(subjectId: number, chapterId: number, title: string) {
      this.loading = `create-concept-${chapterId}`;
      this.error = "";
      try {
        await api(`/api/curriculum/chapters/${chapterId}/concepts`, { method: "POST", token: this.token, body: JSON.stringify({ title }) });
        await this.loadSubjectTree(subjectId);
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async importPdf(file: File): Promise<boolean> {
      this.loading = "import";
      this.error = "";
      this.importDraft = null;
      try {
        const form = new FormData();
        form.append("file", file);
        const headers = new Headers();
        if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
        const response = await fetch("/api/curriculum/import", { method: "POST", headers, body: form });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || `Import failed with ${response.status}`);
        }
        const data = (await response.json()) as { chapters: DraftChapter[] };
        this.importDraft = data.chapters;
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async commitImport(payload: { name: string; board?: string; class_level?: string; chapters: DraftChapter[] }): Promise<CurriculumTree | null> {
      this.loading = "commit-import";
      this.error = "";
      try {
        const tree = await api<CurriculumTree>("/api/curriculum/import/commit", { method: "POST", token: this.token, body: JSON.stringify(payload) });
        this.importDraft = null;
        return tree;
      } catch (error) {
        this.error = messageFromError(error);
        return null;
      } finally {
        this.loading = "";
      }
    },
    async loadOrg() {
      this.loading = "org";
      this.error = "";
      try {
        this.org = await api<OrgInfo>("/api/org", { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadMembers() {
      this.loading = "members";
      this.error = "";
      try {
        const data = await api<{ members: OrgMember[]; pending: PendingInvite[] }>("/api/org/members", { token: this.token });
        this.members = data.members;
        this.pendingInvites = data.pending;
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async inviteMember(email: string, role: string): Promise<boolean> {
      this.loading = "invite-member";
      this.error = "";
      try {
        await api("/api/org/invitations", { method: "POST", token: this.token, body: JSON.stringify({ email, role }) });
        await this.loadMembers();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async changeMemberRole(userId: number, role: string) {
      this.loading = `member-role-${userId}`;
      this.error = "";
      try {
        await api(`/api/org/members/${userId}/role`, { method: "POST", token: this.token, body: JSON.stringify({ role }) });
        await this.loadMembers();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadPlans() {
      this.loading = "plans";
      this.error = "";
      try {
        this.plans = await api<OrgPlan[]>("/api/plans", { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async changePlan(planCode: string) {
      this.loading = `plan-${planCode}`;
      this.error = "";
      try {
        await api("/api/org/subscription", { method: "POST", token: this.token, body: JSON.stringify({ plan_code: planCode }) });
        await this.loadOrg();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadApplications() {
      this.loading = "admissions";
      this.error = "";
      try {
        this.applications = await api<AdmissionApplication[]>("/api/admissions/applications", { token: this.token });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async createApplication(payload: { applicant_name: string; applicant_email?: string; grade?: string; notes?: string }): Promise<boolean> {
      this.loading = "create-application";
      this.error = "";
      try {
        await api("/api/admissions/applications", { method: "POST", token: this.token, body: JSON.stringify(payload) });
        await this.loadApplications();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async setApplicationStatus(id: number, statusValue: string) {
      this.loading = `application-${id}`;
      this.error = "";
      try {
        await api(`/api/admissions/applications/${id}/status`, { method: "POST", token: this.token, body: JSON.stringify({ status: statusValue }) });
        await this.loadApplications();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async enrollApplication(id: number) {
      this.loading = `application-${id}`;
      this.error = "";
      try {
        await api(`/api/admissions/applications/${id}/enroll`, { method: "POST", token: this.token });
        await this.loadApplications();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    logout() {
      this.token = "";
      this.user = null;
      this.syllabus = null;
      this.selectedConcept = null;
      this.tutorial = null;
      this.activeTool = "tutorial";
      this.chatMessages = [];
      this.quizGrade = null;
      this.teachBackGrade = null;
      this.forecastBrief = null;
      this.confusionBrief = null;
      this.forecastNarratives = {};
      this.confusionNarratives = {};
      this.selfStartTutorial = null;
      this.progress = null;
      this.error = "";
      localStorage.removeItem(tokenKey);
    },
  },
});

async function api<T>(path: string, options: RequestInit & { token?: string } = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

function messageFromError(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}
