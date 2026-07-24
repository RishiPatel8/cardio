package com.cardioguard.app.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val email: String,
    val name: String,
    val role: String
)

@Entity(tableName = "health_records")
data class HealthRecordEntity(
    @PrimaryKey(autoGenerate = true) val localId: Long = 0,
    val avgBpm: Float,
    val sdrrMs: Float,
    val rmssdMs: Float,
    val steps: Int,
    val calories: Float,
    val sleepMinutes: Int,
    val timestamp: String,
    val isSynced: Boolean = false
)

@Entity(tableName = "predictions")
data class PredictionRecordEntity(
    @PrimaryKey val id: String,
    val avgBpm: Float,
    val classification: String,
    val confidenceScore: Float,
    val timestamp: String
)

@Entity(tableName = "reports")
data class ReportRecordEntity(
    @PrimaryKey val id: String,
    val title: String,
    val reportUrl: String,
    val timestamp: String
)

@Entity(tableName = "notifications")
data class NotificationRecordEntity(
    @PrimaryKey val id: String,
    val title: String,
    val content: String,
    val isRead: Boolean,
    val timestamp: String
)

@Entity(tableName = "settings")
data class SettingsRecordEntity(
    @PrimaryKey val userId: String,
    val syncIntervalMinutes: Int,
    val enablePush: Boolean,
    val enableEmergencyEmails: Boolean
)
