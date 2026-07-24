package com.cardioguard.app.workers

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.cardioguard.app.repository.AuthRepository
import com.cardioguard.app.repository.HealthRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class WearableSyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val healthRepository: HealthRepository,
    private val authRepository: AuthRepository
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val token = authRepository.getAccessToken() ?: return Result.failure()
        
        val success = healthRepository.syncUnsyncedRecords(token)
        return if (success) {
            Result.success()
        } else {
            Result.retry()
        }
    }
}
