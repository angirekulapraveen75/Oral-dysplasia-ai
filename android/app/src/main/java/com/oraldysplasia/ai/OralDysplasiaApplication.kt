package com.oraldysplasia.ai

import android.app.Application
import com.oraldysplasia.ai.data.repository.AppRepository

class OralDysplasiaApplication : Application() {

    lateinit var repository: AppRepository
        private set

    override fun onCreate() {
        super.onCreate()
        repository = AppRepository(this)
    }
}
