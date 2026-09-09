export interface User {
  id: number;
  email: string;
  name: string;
  role: "admin" | "teacher" | "student";
  active: boolean;
}

export interface Evaluation {
  evaluator_id?: number;
  allocations: Record<string, number>;
  comment: string;
  warnings: string[];
  updated_at?: string;
}

export interface Result {
  user_id: number;
  name: string;
  email: string;
  points: number;
  percentage: number | null;
  raw_grade: number | null;
  grade: number | null;
  mh: boolean;
}

export interface Team {
  id: number;
  name: string;
  token: string;
  grade: number | null;
  members: { id: number; name: string; email?: string }[];
  budget: number;
  own_evaluation: Evaluation | null;
  submitted?: number;
  link?: string;
  results?: { complete: boolean; ready: boolean; rows: Result[] };
  evaluations?: Evaluation[];
  my_result?: Result;
}

export interface Work {
  id: number;
  classroom_id: number;
  classroom_name: string;
  title: string;
  description: string;
  deadline: string;
  closed: boolean;
  expired: boolean;
  published: boolean;
  teams: Team[];
}

export interface Dashboard {
  classes: { id: number; name: string }[];
  works: Work[];
}
