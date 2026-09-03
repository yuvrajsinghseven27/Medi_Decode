import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface ExtractedMedication {
  brand_name?: string;
  generic_molecule?: string;
  dosage_form: string;
  strength: string;
  frequency: 'OD' | 'BD' | 'TID' | 'QID' | 'SOS';
  timing_relation: 'AC' | 'PC' | 'WITH_FOOD';
  duration_days?: number;
  confidence_score: number;
}

export interface PrescriptionExtractionResult {
  doctor_name?: string;
  doctor_specialty?: string;
  medications: ExtractedMedication[];
  unreadable_notes?: string;
  requires_verification: boolean;
}

export interface PrescriptionUploadResponse {
  prescription_id: string;
  user_id: string;
  status: string;
  raw_image_url: string;
  extraction: PrescriptionExtractionResult;
}

export interface SafetyAlertRead {
  id: string;
  user_id: string;
  medication_id?: string;
  alert_type: 'FOOD_INTERACTION' | 'CUMULATIVE_TOXICITY' | 'FASTING_CONFLICT' | 'DUPLICATE_MOLECULE';
  severity: 'INFO' | 'MODERATE' | 'CRITICAL';
  advisory_text: string;
  localized_advisory: Record<string, string>;
  created_at: string;
}

export interface CumulativeToxicityAlert {
  generic_molecule: string;
  cumulative_daily_dose_mg: number;
  max_safe_daily_dose_mg: number;
  is_toxic: boolean;
  contributing_brands: string[];
  prescribing_doctors: string[];
  clinical_risk: string;
}

export interface FastingAdjustment {
  routine_name: string;
  original_timing: string;
  adapted_timing: string;
  rationale: string;
}

export interface ReconciliationResponse {
  prescription_id: string;
  user_id: string;
  status: string;
  alerts: SafetyAlertRead[];
  cumulative_toxicities: CumulativeToxicityAlert[];
  fasting_adjustments: FastingAdjustment[];
  doctor_query_summary?: string;
}

export interface DoseItemDetail {
  id: string;
  medication_id: string;
  brand_name: string;
  generic_molecule?: string;
  form: string;
  strength: string;
  frequency: 'OD' | 'BD' | 'TID' | 'QID' | 'SOS';
  timing_relation: 'AC' | 'PC' | 'WITH_FOOD';
  scheduled_timestamp: string;
  time_str: string;
  status: 'PENDING' | 'TAKEN' | 'SNOOZED' | 'SKIPPED';
  taken_at?: string;
  remaining_pills: number;
  is_low_stock: boolean;
  instructions: string;
}

export interface DailyScheduleView {
  date: string;
  morning: DoseItemDetail[];
  afternoon: DoseItemDetail[];
  evening: DoseItemDetail[];
  bedtime: DoseItemDetail[];
  total_doses: number;
  taken_doses: number;
  adherence_percentage: number;
}

export interface DoseActionResult {
  schedule_item: {
    id: string;
    scheduled_timestamp: string;
    status: 'PENDING' | 'TAKEN' | 'SNOOZED' | 'SKIPPED';
    taken_at?: string;
  };
  action_applied: string;
  remaining_pills: number;
  days_of_supply_remaining: number;
  is_low_stock: boolean;
  low_stock_warning?: string;
}

export interface UserProfile {
  id: string;
  full_name: string;
  phone: string;
  preferred_language: string;
  cultural_dietary_profile?: {
    dietary_type?: string;
    tea_dairy_intake?: string;
    fasting_routines?: string[];
    notes?: string;
  };
  waking_time?: string;
  breakfast_time?: string;
  lunch_time?: string;
  dinner_time?: string;
}

export interface PrescriptionItemSummary {
  id: string;
  brand_name?: string;
  generic_molecule?: string;
  form?: string;
  strength?: string;
  frequency?: string;
  timing_relation?: string;
  duration_days?: number;
  remaining_pills?: number;
  is_active?: boolean;
}

export interface PrescriptionRecord {
  id: string;
  user_id: string;
  raw_image_url: string;
  doctor_name?: string;
  doctor_specialty?: string;
  date_prescribed?: string;
  status: string;
  created_at: string;
  medication_items: PrescriptionItemSummary[];
}

// API Functions
export const api = {
  async checkHealth(): Promise<{ status: string; app: string; version: string }> {
    try {
      const res = await axios.get('/healthz');
      return res.data;
    } catch {
      const res = await axios.get('http://localhost:8000/healthz');
      return res.data;
    }
  },

  async getDefaultUser(): Promise<UserProfile> {
    const res = await apiClient.get<UserProfile>('/users/default');
    return res.data;
  },

  async getPrescriptions(userId?: string): Promise<PrescriptionRecord[]> {
    const params: Record<string, string> = {};
    if (userId) params.user_id = userId;
    const res = await apiClient.get<PrescriptionRecord[]>('/prescriptions', { params });
    return res.data;
  },

  async uploadPrescription(file: File, userId?: string): Promise<PrescriptionUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (userId) {
      formData.append('user_id', userId);
    }
    const res = await apiClient.post<PrescriptionUploadResponse>('/prescriptions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async verifyAndReconcilePrescription(prescriptionId: string): Promise<ReconciliationResponse> {
    const res = await apiClient.post<ReconciliationResponse>(
      `/prescriptions/${prescriptionId}/verify-and-reconcile`
    );
    return res.data;
  },

  async getSafetyAdvisories(
    userId: string,
    severity?: string,
    alertType?: string
  ): Promise<SafetyAlertRead[]> {
    const params: Record<string, string> = { user_id: userId };
    if (severity) params.severity = severity;
    if (alertType) params.alert_type = alertType;
    const res = await apiClient.get<SafetyAlertRead[]>('/safety/advisories', { params });
    return res.data;
  },

  async getTodaySchedule(userId: string, targetDate?: string): Promise<DailyScheduleView> {
    const params: Record<string, string> = { user_id: userId };
    if (targetDate) params.target_date = targetDate;
    const res = await apiClient.get<DailyScheduleView>('/schedule/today', { params });
    return res.data;
  },

  async applyScheduleAction(
    itemId: string,
    action: 'TAKEN' | 'SNOOZED' | 'SKIPPED',
    snoozeMinutes = 30,
    skipReason?: string
  ): Promise<DoseActionResult> {
    const res = await apiClient.post<DoseActionResult>(`/schedule/${itemId}/action`, {
      action,
      snooze_minutes: snoozeMinutes,
      skip_reason: skipReason,
    });
    return res.data;
  },
};
