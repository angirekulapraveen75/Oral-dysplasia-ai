package com.oraldysplasia.ai.ui.screens.results

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.remote.AnalysisResultResponse
import com.oraldysplasia.ai.data.remote.ReportResponse
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch

class ResultsViewModel(
    private val slideId: Int,
    private val repository: AppRepository
) : ViewModel() {

    var state by mutableStateOf<ResultsUiState>(ResultsUiState.Loading)
        private set

    var finalGrade by mutableStateOf("normal")
    var comments by mutableStateOf("")
    var icd10Code by mutableStateOf("K13.29")
    var selectedCriteria by mutableStateOf<Set<String>>(emptySet())

    var isSubmitting by mutableStateOf(false)
        private set
    var isExporting by mutableStateOf(false)
        private set

    var errorMessage by mutableStateOf<String?>(null)
    var successMessage by mutableStateOf<String?>(null)
    var exportedReportPayload by mutableStateOf<ReportResponse?>(null)
        private set

    private val _reviewSubmitted = MutableSharedFlow<Boolean>()
    val reviewSubmitted = _reviewSubmitted.asSharedFlow()

    fun loadResults() {
        state = ResultsUiState.Loading
        errorMessage = null
        viewModelScope.launch {
            val result = repository.getAnalysisResult(slideId)
            if (result.isSuccess) {
                val data = result.getOrThrow()
                state = ResultsUiState.Success(data)
                finalGrade = data.overall_grade
            } else {
                state = ResultsUiState.Error(result.exceptionOrNull()?.message ?: "Failed to load analysis results")
            }
        }
    }

    fun submitPathologistReview() {
        isSubmitting = true
        errorMessage = null
        successMessage = null

        viewModelScope.launch {
            val criteriaHeader = if (selectedCriteria.isNotEmpty()) {
                "Checked WHO Diagnostic Criteria:\n" + selectedCriteria.joinToString("\n") { "- $it" } + "\n\n"
            } else {
                ""
            }
            val finalCommentsText = (criteriaHeader + comments).trim()

            val result = repository.submitReview(
                slideId = slideId,
                finalGrade = finalGrade,
                icd10Code = icd10Code,
                comments = finalCommentsText.ifBlank { null },
                annotations = emptyList() // Simplified UI annotations list
            )
            isSubmitting = false
            if (result.isSuccess) {
                successMessage = "Pathology verification signed successfully!"
                _reviewSubmitted.emit(true)
            } else {
                errorMessage = result.exceptionOrNull()?.message ?: "Failed to sign review"
            }
        }
    }

    fun exportDiagnosticReport(format: String) {
        isExporting = true
        errorMessage = null
        successMessage = null

        viewModelScope.launch {
            val result = repository.exportReport(slideId, format)
            isExporting = false
            if (result.isSuccess) {
                exportedReportPayload = result.getOrNull()
                successMessage = "Report exported successfully in ${format.uppercase()} format!"
            } else {
                errorMessage = result.exceptionOrNull()?.message ?: "Failed to export report"
            }
        }
    }

    fun clearExportedReport() {
        exportedReportPayload = null
    }
}

sealed interface ResultsUiState {
    object Loading : ResultsUiState
    data class Success(val result: AnalysisResultResponse) : ResultsUiState
    data class Error(val message: String) : ResultsUiState
}

class ResultsViewModelFactory(
    private val slideId: Int,
    private val repository: AppRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ResultsViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ResultsViewModel(slideId, repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
