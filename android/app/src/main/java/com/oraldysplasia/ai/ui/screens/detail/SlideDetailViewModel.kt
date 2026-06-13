package com.oraldysplasia.ai.ui.screens.detail

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.remote.SlideResponse
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class SlideDetailViewModel(
    private val slideId: Int,
    private val repository: AppRepository
) : ViewModel() {

    var state by mutableStateOf<DetailUiState>(DetailUiState.Loading)
        private set

    private var isPolling = false

    fun loadSlideDetail() {
        if (state is DetailUiState.Loading) {
            // only clear state on initial load, not during poll refreshes
            state = DetailUiState.Loading
        }
        viewModelScope.launch {
            val result = repository.getSlideDetail(slideId)
            if (result.isSuccess) {
                val slide = result.getOrThrow()
                state = DetailUiState.Success(slide)
                
                // If it is in transition status, start polling
                if (slide.status in listOf("uploaded", "preprocessing", "analyzing") && !isPolling) {
                    startStatusPolling()
                }
            } else {
                state = DetailUiState.Error(result.exceptionOrNull()?.message ?: "Failed to load slide details")
            }
        }
    }

    private fun startStatusPolling() {
        isPolling = true
        viewModelScope.launch {
            while (isPolling) {
                delay(3000) // Poll every 3 seconds
                val result = repository.getSlideDetail(slideId)
                if (result.isSuccess) {
                    val slide = result.getOrThrow()
                    state = DetailUiState.Success(slide)
                    if (slide.status !in listOf("uploaded", "preprocessing", "analyzing")) {
                        isPolling = false
                    }
                }
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        isPolling = false
    }
}

sealed interface DetailUiState {
    object Loading : DetailUiState
    data class Success(val slide: SlideResponse) : DetailUiState
    data class Error(val message: String) : DetailUiState
}

class SlideDetailViewModelFactory(
    private val slideId: Int,
    private val repository: AppRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(SlideDetailViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return SlideDetailViewModel(slideId, repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
