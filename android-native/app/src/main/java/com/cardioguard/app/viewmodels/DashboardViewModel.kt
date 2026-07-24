package com.cardioguard.app.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cardioguard.app.database.entities.HealthRecordEntity
import com.cardioguard.app.repository.HealthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.Instant
import javax.inject.Inject

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val healthRepository: HealthRepository
) : ViewModel() {

    val healthRecords: StateFlow<List<HealthRecordEntity>> = healthRepository.healthRecords
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun logVitals(avgBpm: Float, sdrr: Float, rmssd: Float, steps: Int, calories: Float, sleepMinutes: Int) {
        viewModelScope.launch {
            val record = HealthRecordEntity(
                avgBpm = avgBpm,
                sdrrMs = sdrr,
                rmssdMs = rmssd,
                steps = steps,
                calories = calories,
                sleepMinutes = sleepMinutes,
                timestamp = Instant.now().toString()
            )
            healthRepository.cacheHealthRecord(record)
        }
    }
}
