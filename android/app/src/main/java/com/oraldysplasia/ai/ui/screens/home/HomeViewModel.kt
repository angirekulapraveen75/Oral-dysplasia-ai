package com.oraldysplasia.ai.ui.screens.home

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.remote.DashboardStats
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.launch

class HomeViewModel(private val repository: AppRepository) : ViewModel() {

    var state by mutableStateOf<HomeUiState>(HomeUiState.Loading)
        private set

    val userName: String
        get() = repository.tokenManager.getUserName()

    val institution: String
        get() = repository.tokenManager.getUserInstitution()

    fun loadDashboard() {
        state = HomeUiState.Loading
        viewModelScope.launch {
            val result = repository.getDashboardStats()
            state = if (result.isSuccess) {
                HomeUiState.Success(result.getOrThrow())
            } else {
                HomeUiState.Error(result.exceptionOrNull()?.message ?: "Failed to load dashboard")
            }
        }
    }
}

sealed interface HomeUiState {
    object Loading : HomeUiState
    data class Success(val stats: DashboardStats) : HomeUiState
    data class Error(val message: String) : HomeUiState
}

class HomeViewModelFactory(private val repository: AppRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(HomeViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return HomeViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
