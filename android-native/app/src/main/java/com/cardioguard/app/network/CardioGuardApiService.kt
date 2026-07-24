package com.cardioguard.app.network

import retrofit2.http.*

data class FirebaseLoginRequest(val id_token: String)
data class TokenResponse(val access_token: String, val refresh_token: String, val token_type: String)

data class TimeSeriesPoint(val time_sec: Double, val rr_interval_ms: Double, val bpm: Int)
data class SyncWearableRequest(
    val source: String,
    val avg_bpm: Double,
    val sdrr_ms: Double,
    val rmssd_ms: Double,
    val timeseries_data: List<TimeSeriesPoint>
)

data class PredictionRequest(val avg_bpm: Double, val sdrr_ms: Double, val rmssd_ms: Double)
data class PredictionResponse(
    val id: String,
    val classification: String,
    val confidence_score: Double,
    val timestamp: String
)

data class ReportResponse(val id: String, val title: String, val report_url: String, val created_at: String)
data class UserResponse(val id: String, val email: String, val name: String, val role: String)
data class SettingsResponse(val sync_interval_minutes: Int, val enable_push_notifications: Boolean)

interface CardioGuardApiService {

    @POST("auth/firebase")
    suspend fun loginWithFirebase(@Body request: FirebaseLoginRequest): TokenResponse

    @POST("wearables/sync")
    suspend fun syncWearableData(
        @Header("Authorization") token: String,
        @Body request: SyncWearableRequest
    ): Any

    @POST("prediction")
    suspend fun runPrediction(
        @Header("Authorization") token: String,
        @Body request: PredictionRequest
    ): PredictionResponse

    @GET("reports")
    suspend fun getReports(@Header("Authorization") token: String): List<ReportResponse>

    @GET("users/me")
    suspend fun getMyProfile(@Header("Authorization") token: String): UserResponse

    @GET("settings")
    suspend fun getSettings(@Header("Authorization") token: String): SettingsResponse
}
