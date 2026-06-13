package com.oraldysplasia.ai.data.remote

import com.google.gson.annotations.SerializedName

// ── Auth DTOs ──────────────────────────────────────────────────────
data class SignUpRequest(
    val email: String,
    val name: String,
    val license_id: String,
    val role: String,
    val institution: String,
    val password: String
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class UserBrief(
    val id: Int,
    val name: String,
    val email: String,
    val role: String,
    val institution: String,
    val license_id: String
)

data class AuthResponse(
    val access_token: String,
    val token_type: String,
    val user: UserBrief
)

// ── Slide DTOs ─────────────────────────────────────────────────────
data class SlideResponse(
    val id: Int,
    val user_id: Int,
    val patient_id: String,
    val patient_name: String,
    val patient_age: String?,
    val patient_gender: String?,
    val anatomical_site: String,
    val filename: String,
    val size_bytes: Long,
    val width: Int,
    val height: Int,
    val status: String,
    val current_grade: String,
    val overall_confidence: Float,
    val clinical_notes: String?,
    val created_at: String
)

data class SlideListResponse(
    val slides: List<SlideResponse>,
    val total: Int,
    val page: Int,
    val limit: Int
)

// ── Bounding Box & Patch DTOs ──────────────────────────────────────
data class BoundingBoxDto(
    val xmin: Float,
    val ymin: Float,
    val xmax: Float,
    val ymax: Float,
    val grade: String,
    val confidence: Float,
    val label: String? = null
)

data class PatchResultDto(
    val id: Int,
    val slide_id: Int,
    val x_index: Int,
    val y_index: Int,
    val confidence_mild: Float,
    val confidence_moderate: Float,
    val confidence_severe: Float,
    val confidence_normal: Float,
    val predicted_grade: String,
    val bounding_boxes: List<BoundingBoxDto>
)

// ── Analysis DTOs ──────────────────────────────────────────────────
data class AnalysisRunRequest(
    val slide_id: Int,
    val model_version: String = "Swin-T Hybrid v2.1",
    val confidence_threshold: Float = 0.5f
)

data class AnalysisRunResponse(
    val slide_id: Int,
    val status: String,
    val model_version: String,
    val confidence_threshold: Float
)

data class AnalysisResultResponse(
    val slide_id: Int,
    val overall_grade: String,
    val overall_confidence: Float,
    val total_patches: Int,
    val patches: List<PatchResultDto>
)

// ── Review DTOs ────────────────────────────────────────────────────
data class ReviewRequest(
    val annotations: List<Map<String, Any>> = emptyList(),
    val final_grade: String,
    val comments: String?,
    val icd_10_code: String = "K13.29"
)

data class ReviewResponse(
    val status: String,
    val slide_id: Int,
    val final_grade: String,
    val icd_10_code: String,
    val signed_by: String
)

// ── Report DTOs ────────────────────────────────────────────────────
data class ReportResponse(
    val report_id: Int,
    val format: String,
    val payload: Map<String, Any>
)

// ── Dashboard DTOs ─────────────────────────────────────────────────
data class DashboardStats(
    val total_slides: Int,
    val pending_review: Int,
    val severe_count: Int,
    val mild_count: Int,
    val moderate_count: Int,
    val recent_slides: List<SlideResponse>
)
