package com.oraldysplasia.ai.ui.screens.auth

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.oraldysplasia.ai.data.remote.SignUpRequest
import com.oraldysplasia.ai.data.repository.AppRepository
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch

class SignUpViewModel(private val repository: AppRepository) : ViewModel() {

    var email by mutableStateOf("")
    var name by mutableStateOf("")
    var licenseId by mutableStateOf("")
    var role by mutableStateOf("Consultant Pathologist")
    var institution by mutableStateOf("")
    var password by mutableStateOf("")

    var isLoading by mutableStateOf(false)
        private set

    var errorMessage by mutableStateOf<String?>(null)

    private val _signUpSuccess = MutableSharedFlow<Boolean>()
    val signUpSuccess = _signUpSuccess.asSharedFlow()

    fun onSignUpClick() {
        if (email.isBlank() || name.isBlank() || licenseId.isBlank() || institution.isBlank() || password.isBlank()) {
            errorMessage = "All fields are required."
            return
        }

        if (password.length < 6) {
            errorMessage = "Password must be at least 6 characters."
            return
        }

        isLoading = true
        errorMessage = null

        viewModelScope.launch {
            val result = repository.signup(
                SignUpRequest(
                    email = email.trim(),
                    name = name.trim(),
                    license_id = licenseId.trim(),
                    role = role,
                    institution = institution.trim(),
                    password = password
                )
            )
            isLoading = false
            if (result.isSuccess) {
                _signUpSuccess.emit(true)
            } else {
                errorMessage = result.exceptionOrNull()?.message ?: "Sign up failed"
            }
        }
    }
}

class SignUpViewModelFactory(private val repository: AppRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(SignUpViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return SignUpViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
