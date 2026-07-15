import { defineStore } from "pinia";

type Role = "admin" | "teacher" | "student";

interface User {
  id: number;
  email: string;
  role: Role;
  name: string;
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
    loading: "",
    error: "",
  }),
  getters: {
    isTeacher: (state) => state.user?.role === "teacher" || state.user?.role === "admin",
    isStudent: (state) => state.user?.role === "student",
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
        await this.loadSyllabus();
      } catch (error) {
        this.error = messageFromError(error);
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
      this.loading = `concept-${concept.id}`;
      this.error = "";
      this.tutorial = null;
      try {
        this.selectedConcept = await api<ConceptDetail>(`/api/concepts/${concept.id}`, { token: this.token });
      } catch (error) {
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
    logout() {
      this.token = "";
      this.user = null;
      this.syllabus = null;
      this.selectedConcept = null;
      this.tutorial = null;
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
