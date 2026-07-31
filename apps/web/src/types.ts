export type SourceKind = 'upload' | 'youtube' | 'prepared_demo';
export type ProjectStatus = 'DRAFT' | 'SOURCE_PENDING' | 'QUEUED' | 'PREPARING' | 'ANALYZING' | 'GROUNDING' | 'READY' | 'READY_NO_ECHO' | 'FAILED_RETRIABLE' | 'FAILED' | 'CANCELLED';

export interface SourceRecord {
  kind: SourceKind;
  storage_path?: string;
  public_url?: string;
  source_hash?: string;
  title: string;
  duration_seconds?: number;
  content_type?: string;
  original_filename?: string;
  has_audio?: boolean;
  has_video?: boolean;
  prepared_demo: boolean;
}

export interface Project {
  id: string;
  title: string;
  status: ProjectStatus;
  source?: SourceRecord;
  progress: { completed_windows: number; total_windows?: number; stage: string };
  current_job_id?: string;
  failure_code?: string;
  failure_message?: string;
}

export interface Echo {
  id: string;
  project_id: string;
  knowledge_cutoff_seconds: number;
  first_view_interpretation: string;
  after_story_interpretation?: string;
  tension: string;
  scene_context: string;
  scripture_reference?: string;
  bible_version?: string;
  exact_scripture_text?: string;
  copyright_attribution?: string;
  connection_explanation?: string;
  confidence: number;
}

export interface ViewingSession {
  id: string;
  project_id: string;
  watched_ranges: Array<[number, number]>;
  contiguous_frontier_seconds: number;
  story_complete: boolean;
  ended_naturally: boolean;
}

export interface AccountStatus {
  plan: 'FREE' | 'ACCESS';
  max_video_duration_seconds: number;
  analysis_limit: number;
  analyses_used: number;
  analyses_remaining: number;
  usage_period: 'lifetime' | 'day';
  usage_resets_at?: string;
}
