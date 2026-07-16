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
    loading: "",
    error: "",
  }),
  getters: {
    // Staff-side roles that use the teacher learning views.
    isTeacher: (state) =>
      ["teacher", "owner", "school_admin", "admin"].includes(state.user?.role ?? ""),
    isStudent: (state) => state.user?.role === "student",
    isAdmin: (state) => state.user?.role === "admin" || state.user?.role === "platform_admin",
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
