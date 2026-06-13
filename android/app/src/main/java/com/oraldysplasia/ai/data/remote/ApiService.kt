package com.oraldysplasia.ai.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ── Auth Endpoints ──────────────────────────────────────────────────
    @POST("auth/signup")
    suspend fun signup(@Body request: SignUpRequest): Response<AuthResponse>

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>

    @POST("auth/forgot-password")
    suspend fun forgotPassword(@Body request: Map<String, String>): Response<Map<String, String>>

    // ── Slides Endpoints ────────────────────────────────────────────────
    @Multipart
    @POST("slides/upload")
    suspend fun uploadSlide(
        @Part file: MultipartBody.Part,
        @Part("patient_id") patientId: RequestBody,
        @Part("patient_name") patientName: RequestBody,
        @Part("patient_age") patientAge: RequestBody?,
        @Part("patient_gender") patientGender: RequestBody?,
        @Part("anatomical_site") anatomicalSite: RequestBody,
        @Part("clinical_notes") clinicalNotes: RequestBody?
    ): Response<SlideResponse>

    @GET("slides/library")
    suspend fun getLibrary(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("grade") grade: String? = null,
        @Query("status_filter") statusFilter: String? = null
    ): Response<SlideListResponse>

    @GET("slides/{slide_id}")
    suspend fun getSlideDetail(
        @Path("slide_id") slideId: Int
    ): Response<SlideResponse>

    @GET("slides/stats/dashboard")
    suspend fun getDashboardStats(): Response<DashboardStats>

    // ── Analysis Endpoints ──────────────────────────────────────────────
    @POST("analysis/run")
    suspend fun runAnalysis(@Body request: AnalysisRunRequest): Response<AnalysisRunResponse>

    @GET("analysis/{slide_id}/result")
    suspend fun getAnalysisResult(@Path("slide_id") slideId: Int): Response<AnalysisResultResponse>

    @PUT("analysis/{slide_id}/review")
    suspend fun submitReview(
        @Path("slide_id") slideId: Int,
        @Body request: ReviewRequest
    ): Response<ReviewResponse>

    // ── Reports Endpoints ───────────────────────────────────────────────
    @GET("reports/{slide_id}/export")
    suspend fun exportReport(
        @Path("slide_id") slideId: Int,
        @Query("format") format: String = "fhir"
    ): Response<ReportResponse>
}
