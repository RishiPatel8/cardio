package com.cardioguard.app.repository

import com.cardioguard.app.database.daos.SettingsDao
import com.cardioguard.app.database.entities.SettingsRecordEntity
import com.cardioguard.app.network.CardioGuardApiService
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SettingsRepository @Inject constructor(
    private val settingsDao: SettingsDao,
    private val apiService: CardioGuardApiService
) {
    fun getSettings(userId: String): Flow<SettingsRecordEntity?> {
        return settingsDao.getSettings(userId)
    }

    suspend fun saveSettingsLocal(settings: SettingsRecordEntity) {
        settingsDao.insertSettings(settings)
    }

    suspend fun fetchRemoteSettings(token: String, userId: String): Boolean {
        return try {
            val response = apiService.getSettings("Bearer $token")
            val entity = SettingsRecordEntity(
                userId = userId,
                syncIntervalMinutes = response.sync_interval_minutes,
                enablePush = response.enable_push_notifications,
                enableEmergencyEmails = true
            )
            settingsDao.insertSettings(entity)
            true
        } catch (e: Exception) {
            false
        }
    }
}
