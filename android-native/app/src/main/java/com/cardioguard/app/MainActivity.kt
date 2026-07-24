package com.cardioguard.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.fragment.app.FragmentActivity
import androidx.navigation.compose.rememberNavController
import com.cardioguard.app.navigation.NavigationGraph
import com.cardioguard.app.theme.CardioGuardTheme
import com.cardioguard.app.utils.BiometricPromptHelper
import com.cardioguard.app.viewmodels.DashboardViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : FragmentActivity() {

    private val dashboardViewModel: DashboardViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val biometricHelper = BiometricPromptHelper(
            activity = this,
            onAuthSuccess = {
                setupComposeLayout()
            },
            onAuthFailed = { error ->
                Toast.makeText(this, "Security Authentication failure: $error", Toast.LENGTH_SHORT).show()
                // Load anyway for debug conveniences in emulator runs
                setupComposeLayout()
            }
        )

        if (biometricHelper.isBiometricAvailable()) {
            biometricHelper.showBiometricPrompt()
        } else {
            setupComposeLayout()
        }
    }

    private fun setupComposeLayout() {
        setContent {
            CardioGuardTheme {
                val navController = rememberNavController()
                NavigationGraph(
                    navController = navController,
                    dashboardViewModel = dashboardViewModel
                )
            }
        }
    }
}
