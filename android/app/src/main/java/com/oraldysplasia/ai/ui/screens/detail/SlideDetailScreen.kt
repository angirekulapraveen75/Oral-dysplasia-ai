package com.oraldysplasia.ai.ui.screens.detail

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.oraldysplasia.ai.data.repository.AppRepository
import com.oraldysplasia.ai.ui.components.GradeChip

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SlideDetailScreen(
    slideId: Int,
    repository: AppRepository,
    onNavigateBack: () -> Unit,
    onNavigateToAnalysis: (Int) -> Unit,
    onNavigateToResults: (Int) -> Unit
) {
    val viewModel: SlideDetailViewModel = viewModel(
        factory = SlideDetailViewModelFactory(slideId, repository)
    )

    LaunchedEffect(key1 = slideId) {
        viewModel.loadSlideDetail()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Slide Clinical Dossier", fontWeight = FontWeight.ExtraBold, color = Color(0xFF0F172A)) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = Color(0xFF0F172A))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFFF8FAFC))
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFFF8FAFC)) // Soft Slate-50 background
                .padding(innerPadding)
        ) {
            when (val state = viewModel.state) {
                is DetailUiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = Color(0xFF4F46E5))
                    }
                }
                is DetailUiState.Error -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = state.message, color = MaterialTheme.colorScheme.error)
                            Spacer(modifier = Modifier.height(16.dp))
                            Button(onClick = { viewModel.loadSlideDetail() }) {
                                Text("Retry")
                            }
                        }
                    }
                }
                is DetailUiState.Success -> {
                    val slide = state.slide
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp)
                            .verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(20.dp)
                    ) {
                        // Header info Card
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = Color.White),
                            border = BorderStroke(1.dp, Color(0xFFE2E8F0))
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(20.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = slide.filename,
                                        fontSize = 18.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = Color(0xFF0F172A),
                                        maxLines = 2
                                    )
                                    Spacer(modifier = Modifier.height(6.dp))
                                    val statusColor = when (slide.status) {
                                        "processed" -> Color(0xFF059669)
                                        "reviewed" -> Color(0xFF4F46E5)
                                        "analyzing" -> Color(0xFFD97706)
                                        else -> Color.Gray
                                    }
                                    Text(
                                        text = "STATUS: ${slide.status.uppercase()}",
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = statusColor,
                                        letterSpacing = 0.5.sp
                                    )
                                }
                                GradeChip(grade = slide.current_grade)
                            }
                        }

                        // Patient Data Card
                        Column {
                            Text("Patient Demographics", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color(0xFF475569))
                            Spacer(modifier = Modifier.height(8.dp))
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = Color.White),
                                border = BorderStroke(1.dp, Color(0xFFE2E8F0))
                            ) {
                                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                                    DetailRow(label = "Anonymized Patient ID", value = slide.patient_id, icon = Icons.Default.Badge)
                                    DetailRow(label = "Patient Legal Name", value = slide.patient_name, icon = Icons.Default.Person)
                                    DetailRow(label = "Patient Age", value = slide.patient_age ?: "N/A", icon = Icons.Default.CalendarToday)
                                    DetailRow(label = "Patient Gender", value = slide.patient_gender ?: "N/A", icon = Icons.Default.Person)
                                    DetailRow(label = "Biopsy Anatomical Site", value = slide.anatomical_site, icon = Icons.Default.Place)
                                    DetailRow(label = "Record Created Date", value = slide.created_at, icon = Icons.Default.CalendarToday)
                                }
                            }
                        }

                        // File dimensions
                        Column {
                            Text("WSI Scan Properties", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color(0xFF475569))
                            Spacer(modifier = Modifier.height(8.dp))
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = Color.White),
                                border = BorderStroke(1.dp, Color(0xFFE2E8F0))
                            ) {
                                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                                    DetailRow(label = "Scan Pixel Dimensions", value = "${slide.width} x ${slide.height} pixels", icon = Icons.Default.AspectRatio)
                                    DetailRow(label = "Digital Scan File Size", value = "${"%.2f".format(slide.size_bytes / (1024f * 1024f))} MB", icon = Icons.Default.Save)
                                }
                            }
                        }

                        // Clinical Notes
                        Column {
                            Text("Clinical Anamnesis / History", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Color(0xFF475569))
                            Spacer(modifier = Modifier.height(8.dp))
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = Color.White),
                                border = BorderStroke(1.dp, Color(0xFFE2E8F0))
                            ) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(16.dp)
                                ) {
                                    Text(
                                        text = slide.clinical_notes ?: "No clinical history attached to slide.",
                                        fontSize = 13.sp,
                                        lineHeight = 20.sp,
                                        color = if (slide.clinical_notes == null) Color.Gray else Color(0xFF1E293B)
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        // Action Button
                        if (slide.status in listOf("processed", "reviewed")) {
                            Button(
                                onClick = { onNavigateToResults(slide.id) },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(52.dp),
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4F46E5))
                            ) {
                                Icon(Icons.Default.Analytics, contentDescription = null, tint = Color.White)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Open AI Diagnostics Canvas", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color.White)
                            }
                        } else if (slide.status == "analyzing") {
                            Button(
                                onClick = {},
                                enabled = false,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(52.dp),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                                Spacer(modifier = Modifier.width(12.dp))
                                Text("AI Analysis Running...", fontSize = 15.sp)
                            }
                        } else {
                            Button(
                                onClick = { onNavigateToAnalysis(slide.id) },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(52.dp),
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4F46E5))
                            ) {
                                Icon(Icons.Default.PlayArrow, contentDescription = null, tint = Color.White)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Initialize AI Diagnostic Runner", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color.White)
                            }
                        }
                        
                        Spacer(modifier = Modifier.height(40.dp))
                    }
                }
            }
        }
    }
}

@Composable
fun DetailRow(label: String, value: String, icon: ImageVector) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .background(Color(0xFFF1F5F9), CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = Color(0xFF4F46E5),
                modifier = Modifier.size(18.dp)
            )
        }
        Spacer(modifier = Modifier.width(16.dp))
        Column {
            Text(text = label, fontSize = 11.sp, color = Color.Gray, fontWeight = FontWeight.Bold, letterSpacing = 0.5.sp)
            Text(text = value, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF1E293B))
        }
    }
}
