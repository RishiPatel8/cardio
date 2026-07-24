package com.cardioguard.app.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun OnboardingScreen(
    onFinished: () -> Unit
) {
    var step by remember { mutableStateOf(1) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        when (step) {
            1 -> {
                Text(
                    text = "Welcome to CardioGuard AI",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Research-grade wearable monitoring and arrhythmia detection at your fingertips.",
                    fontSize = 14.sp
                )
                Spacer(modifier = Modifier.height(32.dp))
                Button(onClick = { step = 2 }) {
                    Text("Get Started")
                }
            }
            2 -> {
                Text(
                    text = "Enable Health Connect",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "CardioGuard AI reads heart rates, sleep records, and HRV intervals from Google Health Connect.",
                    fontSize = 14.sp
                )
                Spacer(modifier = Modifier.height(32.dp))
                Button(onClick = { step = 3 }) {
                    Text("Enable Sync")
                }
            }
            3 -> {
                Text(
                    text = "Grant Permissions",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Please allow notification triggers and background battery exclusions to run continuous scans.",
                    fontSize = 14.sp
                )
                Spacer(modifier = Modifier.height(32.dp))
                Button(onClick = onFinished) {
                    Text("Finish Onboarding")
                }
            }
        }
    }
}
