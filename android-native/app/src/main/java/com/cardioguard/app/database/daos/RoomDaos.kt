package com.cardioguard.app.database.daos

import androidx.room.*
import com.cardioguard.app.database.entities.*
import kotlinx.coroutines.flow.Flow

@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE id = :userId LIMIT 1")
    fun getUser(userId: String): Flow<UserEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: UserEntity)

    @Query("DELETE FROM users")
    suspend fun clearUsers()
}

@Dao
interface HealthRecordDao {
    @Query("SELECT * FROM health_records ORDER BY timestamp DESC")
    fun getHealthRecords(): Flow<List<HealthRecordEntity>>

    @Query("SELECT * FROM health_records WHERE isSynced = 0")
    suspend fun getUnsyncedRecords(): List<HealthRecordEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRecord(record: HealthRecordEntity)

    @Query("UPDATE health_records SET isSynced = 1 WHERE localId = :localId")
    suspend fun markSynced(localId: Long)
}

@Dao
interface PredictionDao {
    @Query("SELECT * FROM predictions ORDER BY timestamp DESC")
    fun getPredictions(): Flow<List<PredictionRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPrediction(prediction: PredictionRecordEntity)
}

@Dao
interface ReportDao {
    @Query("SELECT * FROM reports ORDER BY timestamp DESC")
    fun getReports(): Flow<List<ReportRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReport(report: ReportRecordEntity)
}

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notifications ORDER BY timestamp DESC")
    fun getNotifications(): Flow<List<NotificationRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNotification(notification: NotificationRecordEntity)

    @Query("UPDATE notifications SET isRead = 1 WHERE id = :id")
    suspend fun markRead(id: String)
}

@Dao
interface SettingsDao {
    @Query("SELECT * FROM settings WHERE userId = :userId LIMIT 1")
    fun getSettings(userId: String): Flow<SettingsRecordEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSettings(settings: SettingsRecordEntity)
}
