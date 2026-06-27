export interface User {
  id: string;
  email: string;
  full_name: string;
  timezone: string;
  telegram_chat_id: string | null;
  created_at: string;
}

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  daily_minutes: number;
  target_date: string | null;
  status: "active" | "paused" | "completed" | "archived";
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Resource {
  id: string;
  user_id: string;
  goal_id: string | null;
  kind:
    | "youtube_video"
    | "youtube_playlist"
    | "pdf"
    | "article"
    | "note";
  title: string;
  url: string | null;
  storage_path: string | null;
  meta: Record<string, unknown>;
  transcript: string | null;
  content_text: string | null;
  created_at: string;
}

export interface Lesson {
  id: string;
  goal_id: string;
  scheduled_for: string;
  title: string;
  description: string | null;
  duration_minutes: number;
  status: "pending" | "done" | "skipped";
  completed_at: string | null;
  source_resource_ids: string[];
  order_index: number;
  created_at: string;
}

export interface Review {
  id: string;
  lesson_id: string;
  scheduled_for: string;
  interval_days: number;
  repetition_index: number;
  status: "pending" | "done" | "missed";
  completed_at: string | null;
}

export interface QuizQuestion {
  id: string;
  kind: "mcq" | "short_answer" | "flashcard";
  question: string;
  options?: string[];
  answer: string;
  explanation?: string;
}

export interface Quiz {
  id: string;
  goal_id: string;
  lesson_id: string | null;
  title: string | null;
  kind: "mcq" | "short_answer" | "flashcard" | "mixed";
  questions: QuizQuestion[];
  created_at: string;
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  score: number;
  feedback: Record<string, unknown>;
  submitted_at: string;
}

export interface DashboardGoalItem {
  id: string;
  title: string;
  progress_pct: number;
  due_today: number;
  due_reviews: number;
  status: string;
}

export interface Dashboard {
  current_streak_days: number;
  completion_pct_30d: number;
  lessons_completed_total: number;
  study_hours_30d: number;
  quiz_average_pct: number;
  goals: DashboardGoalItem[];
  last_updated: string | null;
}