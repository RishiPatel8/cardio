package com.cardioguard.app.repository

import com.cardioguard.app.database.daos.HealthRecordDao
import com.cardioguard.app.database.entities.HealthRecordEntity
import com.cardioguard.app.network.CardioGuardApiService
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.Before
import org.junit.Test
import org.mockito.Mock
import org.mockito.Mockito.*
import org.mockito.MockitoAnnotations

@OptIn(ExperimentalCoroutinesApi::class)
class HealthRepositoryTest {

    @Mock
    private lateinit var healthRecordDao: HealthRecordDao

    @Mock
    private lateinit var apiService: CardioGuardApiService

    private lateinit var healthRepository: HealthRepository

    @Before
    fun setUp() {
        MockitoAnnotations.openMocks(this)
        healthRepository = HealthRepository(healthRecordDao, apiService)
    }

    @Test
    fun testCacheHealthRecord() = runTest {
        val record = HealthRecordEntity(
            avgBpm = 72f,
            sdrrMs = 45f,
            rmssdMs = 32f,
            steps = 5000,
            calories = 200f,
            sleepMinutes = 480,
            timestamp = "2026-07-22T12:00:00Z"
        )
        healthRepository.cacheHealthRecord(record)
        verify(healthRecordDao).insertRecord(record)
    }
}
