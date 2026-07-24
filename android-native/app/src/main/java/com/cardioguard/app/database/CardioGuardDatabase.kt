package com.cardioguard.app.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.cardioguard.app.database.daos.*
import com.cardioguard.app.database.entities.*

@Database(
    entities = [
        UserEntity::class,
        HealthRecordEntity::class,
        PredictionRecordEntity::class,
        ReportRecordEntity::class,
        NotificationRecordEntity::class,
        SettingsRecordEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class CardioGuardDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun healthRecordDao(): HealthRecordDao
    abstract fun predictionDao(): PredictionDao
    abstract fun reportDao(): ReportDao
    abstract fun notificationDao(): NotificationDao
    abstract fun settingsDao(): SettingsDao
}
