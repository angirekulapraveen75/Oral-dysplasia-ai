package com.oraldysplasia.ai.ui.screens.upload

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.remote.SlideResponse
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import java.io.File

class UploadViewModel(private val repository: AppRepository) : ViewModel() {

    var patientId by mutableStateOf("")
    var patientName by mutableStateOf("")
    var patientAge by mutableStateOf("")
    var patientGender by mutableStateOf("")
    var anatomicalSite by mutableStateOf("Lateral Tongue")
    var clinicalNotes by mutableStateOf("")

    var selectedFile by mutableStateOf<File?>(null)
    var selectedFileName by mutableStateOf<String>("No WSI file selected")

    var isLoading by mutableStateOf(false)
        private set

    var errorMessage by mutableStateOf<String?>(null)

    private val _uploadSuccess = MutableSharedFlow<SlideResponse>()
    val uploadSuccess = _uploadSuccess.asSharedFlow()

    fun selectMockFile(context: Context, filename: String) {
        val cacheDir = context.cacheDir
        val file = File(cacheDir, filename)
        if (!file.exists()) {
            file.createNewFile()
            // Write some dummy bytes
            file.writeText("Dummy virtual Whole Slide Image diagnostic slide content")
        }
        selectedFile = file
        selectedFileName = file.name
    }

    fun selectRealFile(context: Context, uri: android.net.Uri) {
        try {
            val contentResolver = context.contentResolver
            var fileName = "uploaded_slide"
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                if (nameIndex != -1 && cursor.moveToFirst()) {
                    fileName = cursor.getString(nameIndex)
                }
            }
            
            val cacheFile = File(context.cacheDir, fileName)
            contentResolver.openInputStream(uri)?.use { inputStream ->
                cacheFile.outputStream().use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            selectedFile = cacheFile
            selectedFileName = cacheFile.name
            errorMessage = null
        } catch (e: Exception) {
            errorMessage = "Failed to load file: ${e.localizedMessage}"
        }
    }

    fun onUploadClick() {
        if (patientId.isBlank() || patientName.isBlank() || patientAge.isBlank() || patientGender.isBlank() || selectedFile == null) {
            errorMessage = "Patient ID, Name, Age, Gender, and Slide file are required."
            return
        }

        isLoading = true
        errorMessage = null

        viewModelScope.launch {
            val result = repository.uploadSlide(
                file = selectedFile!!,
                patientId = patientId.trim(),
                patientName = patientName.trim(),
                patientAge = patientAge.trim(),
                patientGender = patientGender.trim(),
                anatomicalSite = anatomicalSite.trim(),
                clinicalNotes = clinicalNotes.trim().ifBlank { null }
            )
            isLoading = false
            if (result.isSuccess) {
                _uploadSuccess.emit(result.getOrThrow())
                resetForm()
            } else {
                errorMessage = result.exceptionOrNull()?.message ?: "Upload failed"
            }
        }
    }

    private fun resetForm() {
        patientId = ""
        patientName = ""
        patientAge = ""
        patientGender = ""
        clinicalNotes = ""
        selectedFile = null
        selectedFileName = "No WSI file selected"
    }
}

class UploadViewModelFactory(private val repository: AppRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(UploadViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return UploadViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
