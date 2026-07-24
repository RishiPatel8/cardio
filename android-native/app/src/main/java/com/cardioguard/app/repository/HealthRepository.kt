package com.cardioguard.app.repository

import com.cardioguard.app.database.daos.HealthRecordDao
import com.cardioguard.app.database.entities.HealthRecordEntity
import com.cardioguard.app.network.CardioGuardApiService
import com.cardioguard.app.network.SyncWearableRequest
import com.cardioguard.app.network.TimeSeriesPoint
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HealthRepository @Inject constructor(
    private val healthRecordDao: HealthRecordDao,
    private val apiService: CardioGuardApiService
) {
    val healthRecords: Flow<List<HealthRecordEntity>> = healthRecordDao.getHealthRecords()

    suspend fun cacheHealthRecord(record: HealthRecordEntity) {
        healthRecordDao.insertRecord(record)
    }

    suspend fun syncUnsyncedRecords(token: String): Boolean {
        val unsynced = healthRecordDao.getUnsyncedRecords()
        if (unsynced.isEmpty()) return true

        var success = true
        for (record in unsynced) {
            try {
                val payload = SyncWearableRequest(
                    source = "google_fit",
                    avg_bpm = record.avgBpm.toDouble(),
                    sdrr_ms = record.sdrrMs.toDouble(),
                    rmssd_ms = record.rmssdMs.toDouble(),
                    timeseries_data = listOf(
                        TimeSeriesPoint(
                            time_sec = 0.0,
                            rr_interval_ms = record.rmssdMs.toDouble(),
                            bpm = record.avgBpm.toInt()
                        )
                    )
                )
                apiService.syncWearableData("Bearer $token", payload)
                healthRecordDao.markSynced(record.localId)
            } catch (e: Exception) {
                success = false
            }
        }
        return success
    }
}
