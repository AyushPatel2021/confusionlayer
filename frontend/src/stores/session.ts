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
  department: string;
  profile: Record<string, string>;
  name: string | null;
  org_id: number | null;
  org_name: string | null;
  segment: string | null;
}

export interface InvitationPreview {
  email: string;
  role: string;
  department: string;
  organization_name: string;
}

export interface Subject {
  id: number;
  name: string;
  board: string;
  class_level: string;
}

export interface Classroom {
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
  analogy?: string;
  worked_example: string;
  visual?: string;
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

export interface StudentInsights {
  student_id: number;
  student_name: string;
  average_effective_mastery: number;
  strengths: Array<{ concept_id: number; title: string; chapter_title: string; effective_mastery: number; forecast_risk: number | null }>;
  weaknesses: Array<{ concept_id: number; title: string; chapter_title: string; effective_mastery: number; forecast_risk: number | null }>;
  concepts: Array<{ concept_id: number; title: string; chapter_title: string; effective_mastery: number; forecast_risk: number | null }>;
}
export interface ExamOutcome { days_to_exam: number; outcomes: Array<{ concept_id: number; title: string; chapter_title: string; risk: number; effective_mastery: number }>; }

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
  department: string;
  profile: Record<string, string>;
}

export interface PendingInvite {
  id: number;
  email: string;
  role: string;
  department: string;
}

export interface AdmissionApplication {
  id: number;
  applicant_name: string;
  applicant_email: string | null;
  grade: string | null;
  source: string | null;
  date_of_birth: string | null;
  notes: string | null;
  status: string;
  student_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Invoice {
  id: number;
  recipient_name: string;
  description: string | null;
  amount_cents: number;
  paid_cents: number;
  status: string;
  voided: boolean;
  due_date: string | null;
  created_at: string;
}

export interface FeesSummary {
  billed_cents: number;
  collected_cents: number;
  outstanding_cents: number;
  invoice_count: number;
}

export interface Employee {
  id: number;
  name: string;
  email: string | null;
  designation: string | null;
  phone: string | null;
  join_date: string | null;
  salary_cents: number;
  status: string;
}

export interface PayrollRun {
  id: number;
  period: string;
  status: string;
  payslip_count: number;
  total_net_cents: number;
  created_at: string;
}

export interface Child {
  student_id: number;
  name: string;
  admission_status: string | null;
  outstanding_cents: number;
  average_mastery: number | null;
}

export interface AdminOrg {
  id: number;
  name: string;
  slug: string;
  segment: string;
  plan_code: string | null;
  member_count: number;
}

export interface AdminUsage {
  orgs: number;
  users: number;
  students: number;
  invoices: number;
  employees: number;
  applications: number;
}

export interface ClassroomMember {
  id: number;
  name: string;
}

export interface ManagedClassroom extends Classroom {
  teacher: ClassroomMember;
  students: ClassroomMember[];
}

export interface Dashboard {
  role: string;
  title: string;
  metrics: Array<{ label: string; value: string; note: string | null }>;
  chart: { label: string; labels: string[]; values: number[] };
  classrooms: ManagedClassroom[];
}

export interface OrganizationSettings { id: number; name: string; slug: string; segment: string; logo_url: string | null; timezone: string; currency: string; }
export interface SearchResult { kind: string; title: string; subtitle: string; href: string; }
export interface NotificationItem { id: number; title: string; body: string | null; href: string | null; read: boolean; created_at: string; }
export interface StudentReport { student_id: number; student_name: string; learning: Array<{ concept: string; chapter: string; mastery: number }>; fees: { outstanding_cents: number }; attendance: Record<string, number>; }
export interface AttendanceStudent { id: number; name: string; status: "present" | "absent" | "late" | "excused" | null; note: string | null; }
export interface TimetableEntry { id: number; classroom_id: number; classroom: string; weekday: number; starts_at: string; ends_at: string; room: string | null; }
export interface LibraryBook { id: number; title: string; author: string | null; isbn: string | null; copies_total: number; copies_available: number; }
export interface TransportRoute { id: number; name: string; vehicle_label: string | null; driver_name: string | null; stops: string[]; student_count: number; }

export interface ClassroomOptions {
  subjects: Subject[];
  teachers: ClassroomMember[];
  students: ClassroomMember[];
}

interface AuthResponse {
  user: User;
}

export const useSessionStore = defineStore("session", {
  state: () => ({
    user: null as User | null,
    authReady: false,
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
    studentInsights: null as StudentInsights | null,
    examOutcome: null as ExamOutcome | null,
    curriculumSubjects: [] as CurriculumSubject[],
    curriculumTree: null as CurriculumTree | null,
    importDraft: null as DraftChapter[] | null,
    org: null as OrgInfo | null,
    members: [] as OrgMember[],
    pendingInvites: [] as PendingInvite[],
    plans: [] as OrgPlan[],
    applications: [] as AdmissionApplication[],
    invoices: [] as Invoice[],
    feesSummary: null as FeesSummary | null,
    employees: [] as Employee[],
    payrollRuns: [] as PayrollRun[],
    children: [] as Child[],
    adminOrgs: [] as AdminOrg[],
    adminUsage: null as AdminUsage | null,
    dashboard: null as Dashboard | null,
    classrooms: [] as ManagedClassroom[],
    classroomOptions: null as ClassroomOptions | null,
    orgSettings: null as OrganizationSettings | null,
    searchResults: [] as SearchResult[],
    notifications: [] as NotificationItem[],
    notificationUnread: 0,
    studentReport: null as StudentReport | null,
    attendance: [] as AttendanceStudent[],
    timetable: [] as TimetableEntry[],
    libraryBooks: [] as LibraryBook[],
    transportRoutes: [] as TransportRoute[],
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
    isParent: (state) => state.user?.role === "parent",
    isPlatformAdmin: (state) => state.user?.role === "platform_admin",
    isAuthenticated: (state) => !!state.user,
    roleHome: (state) =>
      state.user?.role === "platform_admin" ? "/admin" : "/app/dashboard",
  },
  actions: {
    async demoLogin(role: "owner" | "school_admin" | "accountant" | "hr" | "teacher" | "student" | "parent") {
      this.loading = `demo-${role}`;
      this.error = "";
      try {
        const response = await api<AuthResponse>("/api/auth/demo", {
          method: "POST",
          body: JSON.stringify({ role }),
        });
        this.user = response.user;
        this.authReady = true;
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
      this.user = response.user;
      this.authReady = true;
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
    async acceptInvitation(token: string, password: string, name: string, profile: Record<string, string> = {}): Promise<boolean> {
      this.loading = "accept";
      this.error = "";
      try {
        const response = await api<AuthResponse>("/api/auth/invitations/accept", {
          method: "POST",
          body: JSON.stringify({ token, password, name, profile }),
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
      if (this.authReady) return;
      this.loading = "restore";
      try {
        const response = await api<AuthResponse>("/api/auth/me");
        this.user = response.user;
        await this.loadSyllabus();
      } catch {
        void this.logout();
      } finally {
        this.authReady = true;
        this.loading = "";
      }
    },
    async loadSyllabus() {
      this.loading = "syllabus";
      this.error = "";
      try {
        this.syllabus = await api<Syllabus>("/api/student/syllabus", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadDashboard() {
      this.loading = "dashboard";
      this.error = "";
      try {
        this.dashboard = await api<Dashboard>("/api/dashboard");
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async searchWorkspace(query: string) {
      if (query.trim().length < 2) { this.searchResults = []; return; }
      try { this.searchResults = (await api<{ results: SearchResult[] }>(`/api/search?q=${encodeURIComponent(query.trim())}`)).results; }
      catch { this.searchResults = []; }
    },
    async loadNotifications() {
      try { const data = await api<{ unread: number; items: NotificationItem[] }>("/api/notifications"); this.notifications = data.items; this.notificationUnread = data.unread; }
      catch { this.notifications = []; this.notificationUnread = 0; }
    },
    async readNotification(id: number) {
      try { await api(`/api/notifications/${id}/read`, { method: "POST" }); const item = this.notifications.find((row) => row.id === id); if (item && !item.read) { item.read = true; this.notificationUnread = Math.max(0, this.notificationUnread - 1); } } catch { /* non-blocking */ }
    },
    async loadOrgSettings() { this.loading = "org-settings"; this.error = ""; try { this.orgSettings = await api<OrganizationSettings>("/api/org/settings"); } catch (error) { this.error = messageFromError(error); } finally { this.loading = ""; } },
    async saveOrgSettings(payload: Omit<OrganizationSettings, "id" | "slug" | "segment">): Promise<boolean> { this.loading = "org-settings"; this.error = ""; try { this.orgSettings = await api<OrganizationSettings>("/api/org/settings", { method: "PATCH", body: JSON.stringify(payload) }); if (this.user) this.user.org_name = this.orgSettings.name; return true; } catch (error) { this.error = messageFromError(error); return false; } finally { this.loading = ""; } },
    async loadStudentReport(studentId: number) { this.loading = "student-report"; this.error = ""; try { this.studentReport = await api<StudentReport>(`/api/students/${studentId}/report-card`); } catch (error) { this.error = messageFromError(error); } finally { this.loading = ""; } },
    async loadAttendance(classroomId: number, value: string) { this.loading = "attendance"; this.error = ""; try { this.attendance = (await api<{ students: AttendanceStudent[] }>(`/api/attendance/classrooms/${classroomId}?attendance_date=${value}`)).students; } catch (error) { this.error = messageFromError(error); } finally { this.loading = ""; } },
    async saveAttendance(classroomId: number, attendance_date: string, entries: Array<{ student_id: number; status: string; note?: string | null }>) { this.loading = "attendance"; this.error = ""; try { await api(`/api/attendance/classrooms/${classroomId}`, { method: "PUT", body: JSON.stringify({ attendance_date, entries }) }); } catch (error) { this.error = messageFromError(error); } finally { this.loading = ""; } },
    async loadOperations() { this.loading = "operations"; this.error = ""; try { const [timetable, libraryBooks, transportRoutes] = await Promise.all([api<TimetableEntry[]>("/api/timetable"), api<LibraryBook[]>("/api/library"), api<TransportRoute[]>("/api/transport")]); this.timetable = timetable; this.libraryBooks = libraryBooks; this.transportRoutes = transportRoutes; } catch (error) { this.error = messageFromError(error); } finally { this.loading = ""; } },
    async createTimetable(payload: { classroom_id: number; weekday: number; starts_at: string; ends_at: string; room?: string }) { try { await api("/api/timetable", { method: "POST", body: JSON.stringify(payload) }); await this.loadOperations(); } catch (error) { this.error = messageFromError(error); } },
    async deleteTimetable(id: number) { try { await api(`/api/timetable/${id}`, { method: "DELETE" }); await this.loadOperations(); } catch (error) { this.error = messageFromError(error); } },
    async createLibraryBook(payload: { title: string; author?: string; isbn?: string; copies_total: number }) { try { await api("/api/library", { method: "POST", body: JSON.stringify(payload) }); await this.loadOperations(); } catch (error) { this.error = messageFromError(error); } },
    async createTransportRoute(payload: { name: string; vehicle_label?: string; driver_name?: string; stops: string[] }) { try { await api("/api/transport", { method: "POST", body: JSON.stringify(payload) }); await this.loadOperations(); } catch (error) { this.error = messageFromError(error); } },
    async loadClassrooms() {
      this.loading = "classrooms";
      this.error = "";
      try {
        this.classrooms = await api<ManagedClassroom[]>("/api/classrooms");
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadClassroomOptions() {
      try {
        this.classroomOptions = await api<ClassroomOptions>("/api/classrooms/options");
      } catch (error) {
        this.error = messageFromError(error);
      }
    },
    async createClassroom(payload: { name: string; subject_id: number; teacher_id: number }): Promise<boolean> {
      this.loading = "create-classroom";
      this.error = "";
      try {
        await api("/api/classrooms", { method: "POST", body: JSON.stringify(payload) });
        await this.loadClassrooms();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async updateClassroom(classroomId: number, payload: { name: string; subject_id: number; teacher_id: number }): Promise<boolean> {
      this.loading = `update-classroom-${classroomId}`;
      this.error = "";
      try {
        await api(`/api/classrooms/${classroomId}`, { method: "PATCH", body: JSON.stringify(payload) });
        await this.loadClassrooms();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async deleteClassroom(classroomId: number): Promise<boolean> {
      this.loading = `delete-classroom-${classroomId}`;
      this.error = "";
      try {
        await api(`/api/classrooms/${classroomId}`, { method: "DELETE" });
        await this.loadClassrooms();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async enrollClassroomStudent(classroomId: number, studentId: number) {
      this.loading = `enroll-${classroomId}`;
      this.error = "";
      try {
        await api(`/api/classrooms/${classroomId}/students`, { method: "POST", body: JSON.stringify({ student_id: studentId }) });
        await this.loadClassrooms();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async removeClassroomStudent(classroomId: number, studentId: number) {
      this.loading = `enroll-${classroomId}`;
      this.error = "";
      try {
        await api(`/api/classrooms/${classroomId}/students/${studentId}`, { method: "DELETE" });
        await this.loadClassrooms();
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
        this.selectedConcept = await api<ConceptDetail>(`/api/concepts/${conceptId}`, { });
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
    async submitQuiz(question: string, studentAnswer: string, rubric: string, mode: "quiz" | "exam" = "quiz") {
      if (!this.selectedConcept || !question.trim() || !studentAnswer.trim() || !rubric.trim()) return;
      this.loading = "quiz";
      this.error = "";
      this.quizGrade = null;
      try {
        this.quizGrade = await api<QuizGrade>(`/api/concepts/${this.selectedConcept.id}/quiz/grade`, {
          method: "POST",
          body: JSON.stringify({
            question: question.trim(),
            student_answer: studentAnswer.trim(),
            rubric: rubric.trim(),
            mode,
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
          { },
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
          { },
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
          { method: "POST", body: JSON.stringify({ concept_id: conceptId }) },
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
          { method: "POST", body: JSON.stringify({ concept_id: conceptId }) },
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
        this.progress = await api<StudentProgress>("/api/student/progress", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadStudentInsights(classroomId: number, studentId: number) {
      this.loading = "student-insights";
      this.error = "";
      try {
        this.studentInsights = await api<StudentInsights>(`/api/teacher/classrooms/${classroomId}/students/${studentId}/insights`);
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadExamOutcome() { this.loading = "exam-outcome"; this.error = ""; try { this.examOutcome = await api<ExamOutcome>("/api/student/exam-outcome"); } catch (error) { this.error = messageFromError(error); } finally { this.loading = ""; } },
    async loadCurriculumSubjects() {
      this.loading = "curriculum";
      this.error = "";
      try {
        this.curriculumSubjects = await api<CurriculumSubject[]>("/api/curriculum/subjects", { });
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
        this.curriculumTree = await api<CurriculumTree>(`/api/curriculum/subjects/${subjectId}`, { });
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
        await api(`/api/curriculum/subjects/${subjectId}/chapters`, { method: "POST", body: JSON.stringify({ title }) });
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
        await api(`/api/curriculum/chapters/${chapterId}/concepts`, { method: "POST", body: JSON.stringify({ title }) });
        await this.loadSubjectTree(subjectId);
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async updateCurriculumItem(path: string, payload: { title?: string; name?: string; board?: string; class_level?: string }, subjectId: number) {
      this.loading = "curriculum-edit"; this.error = "";
      try { await api(path, { method: "PATCH", body: JSON.stringify(payload) }); await this.loadCurriculumSubjects(); await this.loadSubjectTree(subjectId); }
      catch (error) { this.error = messageFromError(error); }
      finally { this.loading = ""; }
    },
    async deleteCurriculumItem(path: string, subjectId?: number) {
      this.loading = "curriculum-edit"; this.error = "";
      try { await api(path, { method: "DELETE" }); await this.loadCurriculumSubjects(); if (subjectId) await this.loadSubjectTree(subjectId); else this.curriculumTree = null; }
      catch (error) { this.error = messageFromError(error); }
      finally { this.loading = ""; }
    },
    async importPdf(file: File): Promise<boolean> {
      this.loading = "import";
      this.error = "";
      this.importDraft = null;
      if (file.size > 5 * 1024 * 1024) {
        this.error = "Choose a PDF smaller than 5MB.";
        this.loading = "";
        return false;
      }
      try {
        const form = new FormData();
        form.append("file", file);
        const response = await fetch("/api/curriculum/import", { method: "POST", body: form, credentials: "same-origin" });
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
        const tree = await api<CurriculumTree>("/api/curriculum/import/commit", { method: "POST", body: JSON.stringify(payload) });
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
        this.org = await api<OrgInfo>("/api/org", { });
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
        const data = await api<{ members: OrgMember[]; pending: PendingInvite[] }>("/api/org/members", { });
        this.members = data.members;
        this.pendingInvites = data.pending;
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async inviteMember(email: string, role: string, department: string): Promise<boolean> {
      this.loading = "invite-member";
      this.error = "";
      try {
        await api("/api/org/invitations", { method: "POST", body: JSON.stringify({ email, role, department }) });
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
        await api(`/api/org/members/${userId}/role`, { method: "POST", body: JSON.stringify({ role }) });
        await this.loadMembers();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async changeMemberStatus(userId: number, status: "active" | "inactive") {
      this.loading = `member-status-${userId}`;
      this.error = "";
      try {
        await api(`/api/org/members/${userId}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
        await this.loadMembers();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async changeMemberDepartment(userId: number, department: string) {
      this.loading = `member-department-${userId}`; this.error = "";
      try { await api(`/api/org/members/${userId}/department`, { method: "PATCH", body: JSON.stringify({ department }) }); await this.loadMembers(); }
      catch (error) { this.error = messageFromError(error); }
      finally { this.loading = ""; }
    },
    async removeMember(userId: number) {
      this.loading = `member-remove-${userId}`; this.error = "";
      try { await api(`/api/org/members/${userId}`, { method: "DELETE" }); await this.loadMembers(); }
      catch (error) { this.error = messageFromError(error); }
      finally { this.loading = ""; }
    },
    async loadPlans() {
      this.loading = "plans";
      this.error = "";
      try {
        this.plans = await api<OrgPlan[]>("/api/plans", { });
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
        await api("/api/org/subscription", { method: "POST", body: JSON.stringify({ plan_code: planCode }) });
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
        this.applications = await api<AdmissionApplication[]>("/api/admissions/applications", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async createApplication(payload: { applicant_name: string; applicant_email?: string; grade?: string; source?: string; date_of_birth?: string; notes?: string }): Promise<boolean> {
      this.loading = "create-application";
      this.error = "";
      try {
        await api("/api/admissions/applications", { method: "POST", body: JSON.stringify(payload) });
        await this.loadApplications();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async updateApplication(id: number, payload: { applicant_name: string; applicant_email?: string; grade?: string; source?: string; date_of_birth?: string; notes?: string }): Promise<boolean> {
      this.loading = `application-${id}`;
      this.error = "";
      try { await api(`/api/admissions/applications/${id}`, { method: "PATCH", body: JSON.stringify(payload) }); await this.loadApplications(); return true; }
      catch (error) { this.error = messageFromError(error); return false; }
      finally { this.loading = ""; }
    },
    async deleteApplication(id: number): Promise<boolean> {
      this.loading = `application-${id}`;
      this.error = "";
      try { await api(`/api/admissions/applications/${id}`, { method: "DELETE" }); await this.loadApplications(); return true; }
      catch (error) { this.error = messageFromError(error); return false; }
      finally { this.loading = ""; }
    },
    async setApplicationStatus(id: number, statusValue: string) {
      this.loading = `application-${id}`;
      this.error = "";
      try {
        await api(`/api/admissions/applications/${id}/status`, { method: "POST", body: JSON.stringify({ status: statusValue }) });
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
        await api(`/api/admissions/applications/${id}/enroll`, { method: "POST", });
        await this.loadApplications();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadFees() {
      this.loading = "fees";
      this.error = "";
      try {
        this.invoices = await api<Invoice[]>("/api/fees/invoices", { });
        this.feesSummary = await api<FeesSummary>("/api/fees/summary", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async createInvoice(payload: { recipient_name: string; amount_cents: number; description?: string }): Promise<boolean> {
      this.loading = "create-invoice";
      this.error = "";
      try {
        await api("/api/fees/invoices", { method: "POST", body: JSON.stringify(payload) });
        await this.loadFees();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async updateInvoice(invoiceId: number, payload: { recipient_name: string; amount_cents: number; description?: string }): Promise<boolean> {
      this.loading = `invoice-${invoiceId}`;
      this.error = "";
      try { await api(`/api/fees/invoices/${invoiceId}`, { method: "PATCH", body: JSON.stringify(payload) }); await this.loadFees(); return true; }
      catch (error) { this.error = messageFromError(error); return false; }
      finally { this.loading = ""; }
    },
    async recordPayment(invoiceId: number, amountCents: number, method?: string) {
      this.loading = `invoice-${invoiceId}`;
      this.error = "";
      try {
        await api(`/api/fees/invoices/${invoiceId}/payments`, { method: "POST", body: JSON.stringify({ amount_cents: amountCents, method }) });
        await this.loadFees();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async voidInvoice(invoiceId: number) {
      this.loading = `invoice-${invoiceId}`;
      this.error = "";
      try {
        await api(`/api/fees/invoices/${invoiceId}/void`, { method: "POST", });
        await this.loadFees();
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async loadEmployees() {
      this.loading = "employees";
      this.error = "";
      try {
        this.employees = await api<Employee[]>("/api/hr/employees", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async createEmployee(payload: { name: string; email?: string; designation?: string; phone?: string; join_date?: string; salary_cents: number }): Promise<boolean> {
      this.loading = "create-employee";
      this.error = "";
      try {
        await api("/api/hr/employees", { method: "POST", body: JSON.stringify(payload) });
        await this.loadEmployees();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async updateEmployee(employeeId: number, payload: { name: string; email?: string; designation?: string; phone?: string; join_date?: string; salary_cents: number }): Promise<boolean> {
      this.loading = `employee-${employeeId}`;
      this.error = "";
      try { await api(`/api/hr/employees/${employeeId}`, { method: "PATCH", body: JSON.stringify(payload) }); await this.loadEmployees(); return true; }
      catch (error) { this.error = messageFromError(error); return false; }
      finally { this.loading = ""; }
    },
    async loadPayrollRuns() {
      this.loading = "payroll";
      this.error = "";
      try {
        this.payrollRuns = await api<PayrollRun[]>("/api/hr/payroll", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async runPayroll(period: string): Promise<boolean> {
      this.loading = "run-payroll";
      this.error = "";
      try {
        await api("/api/hr/payroll", { method: "POST", body: JSON.stringify({ period }) });
        await this.loadPayrollRuns();
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async loadChildren() {
      this.loading = "children";
      this.error = "";
      try {
        this.children = await api<Child[]>("/api/family/children", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async linkGuardian(parentEmail: string, studentId: number): Promise<boolean> {
      this.loading = "link-guardian";
      this.error = "";
      try {
        await api("/api/family/links", { method: "POST", body: JSON.stringify({ parent_email: parentEmail, student_id: studentId }) });
        return true;
      } catch (error) {
        this.error = messageFromError(error);
        return false;
      } finally {
        this.loading = "";
      }
    },
    async loadAdmin() {
      this.loading = "admin";
      this.error = "";
      try {
        this.adminOrgs = await api<AdminOrg[]>("/api/admin/orgs", { });
        this.adminUsage = await api<AdminUsage>("/api/admin/usage", { });
      } catch (error) {
        this.error = messageFromError(error);
      } finally {
        this.loading = "";
      }
    },
    async logout() {
      this.user = null;
      this.authReady = true;
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
      await api("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    },
  },
});

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

function messageFromError(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}
