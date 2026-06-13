package com.oraldysplasia.ai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.oraldysplasia.ai.ui.theme.OralDysplasiaAITheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Retrieve repository from the Application subclass
        val repository = (application as OralDysplasiaApplication).repository

        setContent {
            OralDysplasiaAITheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = androidx.compose.material3.MaterialTheme.colorScheme.background
                ) {
                    OralDysplasiaApp(repository = repository)
                }
            }
        }
    }
}
