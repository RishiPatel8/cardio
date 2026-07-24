package com.cardioguard.app.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cardioguard.app.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _authState = MutableStateFlow<AuthState>(AuthState.LoggedOut)
    val authState: StateFlow<AuthState> = _authState

    init {
        val token = authRepository.getAccessToken()
        if (token != null) {
            _authState.value = AuthState.Authenticated
        }
    }

    fun login(firebaseIdToken: String) {
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            val success = authRepository.authenticateWithFirebase(firebaseIdToken)
            if (success) {
                _authState.value = AuthState.Authenticated
            } else {
                _authState.value = AuthState.Error("Authentication failed.")
            }
        }
    }

    fun logout() {
        authRepository.clearTokens()
        _authState.value = AuthState.LoggedOut
    }
}

sealed class AuthState {
    object LoggedOut : AuthState()
    object Loading : AuthState()
    object Authenticated : AuthState()
    data class Error(val message: String) : AuthState()
}
