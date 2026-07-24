package com.cardioguard.app.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ReportsScreen() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "Clinical PDF Reports",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Arrhythmia Diagnostic Report", fontWeight = FontWeight.Bold)
                Text("Generated on 2026-07-22 15:45", fontSize = 12.sp)
                Spacer(modifier = Modifier.height(12.dp))
                Button(onClick = {}) {
                    Text("Download PDF (FastAPI Server)")
                }
            }
        }
    }
}
