package com.cardioguard.app.di

import android.content.Context
import androidx.room.Room
import com.cardioguard.app.database.CardioGuardDatabase
import com.cardioguard.app.database.daos.*
import com.cardioguard.app.healthconnect.HealthConnectManager
import com.cardioguard.app.network.CardioGuardApiService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): CardioGuardDatabase {
        return Room.databaseBuilder(
            context,
            CardioGuardDatabase::class.java,
            "cardioguard_local_db"
        ).fallbackToDestructiveMigration().build()
    }

    @Provides
    fun provideUserDao(db: CardioGuardDatabase): UserDao = db.userDao()

    @Provides
    fun provideHealthRecordDao(db: CardioGuardDatabase): HealthRecordDao = db.healthRecordDao()

    @Provides
    fun providePredictionDao(db: CardioGuardDatabase): PredictionDao = db.predictionDao()

    @Provides
    fun provideReportDao(db: CardioGuardDatabase): ReportDao = db.reportDao()

    @Provides
    fun provideNotificationDao(db: CardioGuardDatabase): NotificationDao = db.notificationDao()

    @Provides
    fun provideSettingsDao(db: CardioGuardDatabase): SettingsDao = db.settingsDao()

    @Provides
    @Singleton
    fun provideHealthConnectManager(@ApplicationContext context: Context): HealthConnectManager {
        return HealthConnectManager(context)
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        return OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/api/v1/") // Local API URL for Android emulator
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): CardioGuardApiService {
        return retrofit.create(CardioGuardApiService::class.java)
    }
}
