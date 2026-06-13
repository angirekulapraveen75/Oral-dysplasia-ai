package com.oraldysplasia.ai.ui.screens.library

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.remote.SlideResponse
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class LibraryViewModel(private val repository: AppRepository) : ViewModel() {

    var slides by mutableStateOf<List<SlideResponse>>(emptyList())
        private set

    var isLoading by mutableStateOf(false)
        private set

    var errorMessage by mutableStateOf<String?>(null)

    var selectedGradeFilter by mutableStateOf<String?>(null)
    var selectedStatusFilter by mutableStateOf<String?>(null)

    fun fetchLibrary() {
        isLoading = true
        errorMessage = null
        viewModelScope.launch {
            repository.getLibrary(
                page = 1,
                limit = 50,
                grade = selectedGradeFilter,
                statusFilter = selectedStatusFilter
            ).collectLatest { result ->
                isLoading = false
                if (result.isSuccess) {
                    slides = result.getOrThrow()
                } else {
                    errorMessage = result.exceptionOrNull()?.message ?: "Failed to fetch library"
                }
            }
        }
    }

    fun setGradeFilter(grade: String?) {
        selectedGradeFilter = grade
        fetchLibrary()
    }

    fun setStatusFilter(status: String?) {
        selectedStatusFilter = status
        fetchLibrary()
    }
}

class LibraryViewModelFactory(private val repository: AppRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(LibraryViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return LibraryViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
