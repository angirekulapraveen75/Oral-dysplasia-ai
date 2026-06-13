package com.oraldysplasia.ai.ui.screens.analysis

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch

class AnalysisViewModel(
    private val slideId: Int,
    private val repository: AppRepository
) : ViewModel() {

    var confidenceThreshold by mutableStateOf(0.5f)
    var isRunning by mutableStateOf(false)
        private set

    var errorMessage by mutableStateOf<String?>(null)

    private val _analysisStarted = MutableSharedFlow<Boolean>()
    val analysisStarted = _analysisStarted.asSharedFlow()

    fun runAnalysis() {
        isRunning = true
        errorMessage = null

        viewModelScope.launch {
            val result = repository.runAnalysis(slideId, confidenceThreshold)
            isRunning = false
            if (result.isSuccess) {
                _analysisStarted.emit(true)
            } else {
                errorMessage = result.exceptionOrNull()?.message ?: "Failed to start analysis"
            }
        }
    }
}

class AnalysisViewModelFactory(
    private val slideId: Int,
    private val repository: AppRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(AnalysisViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return AnalysisViewModel(slideId, repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
