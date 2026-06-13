package com.oraldysplasia.ai.ui.screens.library

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Email
import android.content.Intent
import android.net.Uri
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.oraldysplasia.ai.data.repository.AppRepository
import com.oraldysplasia.ai.ui.components.GradeChip

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LibraryScreen(
    repository: AppRepository,
    onNavigateToDetail: (Int) -> Unit
) {
    val viewModel: LibraryViewModel = viewModel(
        factory = LibraryViewModelFactory(repository)
    )

    LaunchedEffect(key1 = true) {
        viewModel.fetchLibrary()
    }

    val grades = listOf("All", "pending", "normal", "mild", "moderate", "severe")
    val statuses = listOf("All", "uploaded", "processing", "ready", "analyzing", "processed", "reviewed", "error")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Biopsy Case Records", fontWeight = FontWeight.ExtraBold, color = Color(0xFF0F172A)) },
                actions = {
                    IconButton(onClick = { viewModel.fetchLibrary() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh", tint = Color(0xFF4F46E5))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFFF8FAFC))
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFFF8FAFC)) // Soft Slate-50 background
                .padding(innerPadding)
        ) {
            // Filters Panel inside a clean header card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                border = BorderStroke(1.dp, Color(0xFFE2E8F0))
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Grade Filter Row
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(
                            text = "Filter by AI Grade Severity",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF64748B),
                            letterSpacing = 0.5.sp
                        )
                        LazyRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            contentPadding = PaddingValues(vertical = 4.dp)
                        ) {
                            items(grades) { grade ->
                                val isSelected = (grade == "All" && viewModel.selectedGradeFilter == null) ||
                                        (grade != "All" && viewModel.selectedGradeFilter == grade)
                                val chipColor = if (isSelected) Color(0xFF4F46E5) else Color(0xFFE2E8F0)
                                val textColor = if (isSelected) Color.White else Color(0xFF475569)

                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(if (isSelected) chipColor else Color.Transparent)
                                        .border(BorderStroke(1.dp, chipColor), RoundedCornerShape(8.dp))
                                        .clickable { viewModel.setGradeFilter(if (grade == "All") null else grade) }
                                        .padding(horizontal = 10.dp, vertical = 6.dp)
                                ) {
                                    Text(
                                        text = grade.uppercase(),
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = textColor
                                    )
                                }
                            }
                        }
                    }

                    Divider(color = Color(0xFFF1F5F9))

                    // Status Filter Row
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(
                            text = "Filter by Workflow Status",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF64748B),
                            letterSpacing = 0.5.sp
                        )
                        LazyRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            contentPadding = PaddingValues(vertical = 4.dp)
                        ) {
                            items(statuses) { status ->
                                val isSelected = (status == "All" && viewModel.selectedStatusFilter == null) ||
                                        (status != "All" && viewModel.selectedStatusFilter == status)
                                val chipColor = if (isSelected) Color(0xFF0F766E) else Color(0xFFE2E8F0) // Teal for status
                                val textColor = if (isSelected) Color.White else Color(0xFF475569)

                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(if (isSelected) chipColor else Color.Transparent)
                                        .border(BorderStroke(1.dp, chipColor), RoundedCornerShape(8.dp))
                                        .clickable { viewModel.setStatusFilter(if (status == "All") null else status) }
                                        .padding(horizontal = 10.dp, vertical = 6.dp)
                                ) {
                                    Text(
                                        text = status.uppercase(),
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = textColor
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Box(modifier = Modifier.fillMaxHeight().weight(1f)) {
                if (viewModel.isLoading && viewModel.slides.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = Color(0xFF4F46E5))
                    }
                } else if (viewModel.errorMessage != null && viewModel.slides.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = viewModel.errorMessage!!, color = MaterialTheme.colorScheme.error)
                            Spacer(modifier = Modifier.height(16.dp))
                            Button(onClick = { viewModel.fetchLibrary() }) {
                                Text("Retry")
                            }
                        }
                    }
                } else if (viewModel.slides.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text(
                            text = "No biopsy cases match active filters.",
                            color = Color.Gray,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(viewModel.slides) { slide ->
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { onNavigateToDetail(slide.id) },
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = Color.White),
                                border = BorderStroke(1.dp, Color(0xFFE2E8F0))
                            ) {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(16.dp)
                                ) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = slide.filename,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 15.sp,
                                            color = Color(0xFF0F172A),
                                            modifier = Modifier.weight(1f),
                                            maxLines = 1
                                        )
                                        GradeChip(grade = slide.current_grade)
                                    }
                                    Spacer(modifier = Modifier.height(10.dp))
                                    Divider(color = Color(0xFFF1F5F9))
                                    Spacer(modifier = Modifier.height(10.dp))

                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.Bottom
                                    ) {
                                        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                            Text(text = "Patient ID: ${slide.patient_id}", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = Color.Gray)
                                            Text(text = "Patient Name: ${slide.patient_name}", fontSize = 12.sp, color = Color.Gray)
                                            Text(text = "Anatomical Site: ${slide.anatomical_site}", fontSize = 12.sp, color = Color.Gray)
                                        }
                                        Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(4.dp)) {
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
                                            Text(
                                                text = "Confidence: ${"%.1f".format(slide.overall_confidence * 100)}%",
                                                fontSize = 12.sp,
                                                fontWeight = FontWeight.ExtraBold,
                                                color = Color(0xFF0F172A)
                                            )
                                        }
                                    }

                                    Spacer(modifier = Modifier.height(10.dp))
                                    Divider(color = Color(0xFFF1F5F9))

                                    val context = androidx.compose.ui.platform.LocalContext.current
                                    val gradeExplanations = remember {
                                        mapOf(
                                            "normal" to "No signs of oral epithelial dysplasia were found (Benign / Normal tissue).",
                                            "mild" to "Mild dysplasia detected. Cell alterations are confined to the lower third of the epithelium. Standard monitoring and follow-up recommended.",
                                            "moderate" to "Moderate dysplasia detected. Cell alterations extend to the middle third of the epithelium. Close clinical observation or intervention may be required.",
                                            "severe" to "Severe dysplasia / Carcinoma in situ detected. Cell alterations occupy the upper third or full thickness of the epithelium. Prompt clinical treatment is required.",
                                            "pending" to "Analysis is pending verification."
                                        )
                                    }
                                    val explanation = gradeExplanations[slide.current_grade.lowercase()] ?: "Verification required by pathologist."
                                    val pathName = repository.tokenManager.getUserName()
                                    val pathRole = repository.tokenManager.getUserRole()
                                    val pathInstitution = repository.tokenManager.getUserInstitution()

                                    val shareText = remember(slide, pathName, pathRole, pathInstitution) {
                                        """
                                            PATIENT DIAGNOSTIC REPORT (OralDysplasia AI)
                                            --------------------------------------------
                                            Patient Name: ${slide.patient_name}
                                            Patient ID: ${slide.patient_id}
                                            Age: ${slide.patient_age ?: "N/A"}
                                            Gender: ${slide.patient_gender ?: "N/A"}
                                            Biopsy Site: ${slide.anatomical_site}
                                            
                                            DIAGNOSTIC ASSESSMENT
                                            Grade: ${slide.current_grade.uppercase()}
                                            Summary: $explanation
                                            Next Steps: Please consult your oral surgeon or primary clinician to discuss these diagnostic findings.
                                            
                                            CERTIFICATION
                                            Verifying Specialist: Dr. $pathName ($pathRole)
                                            Institution: $pathInstitution
                                            Status: ${slide.status.uppercase()}
                                        """.trimIndent()
                                    }

                                    Row(
                                        modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                                        horizontalArrangement = Arrangement.End,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = "Share Report: ",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = Color.Gray,
                                            modifier = Modifier.padding(end = 4.dp)
                                        )
                                        IconButton(
                                            onClick = {
                                                val intent = Intent(Intent.ACTION_SEND).apply {
                                                    type = "text/plain"
                                                    putExtra(Intent.EXTRA_TEXT, shareText)
                                                    setPackage("com.whatsapp")
                                                }
                                                try {
                                                    context.startActivity(intent)
                                                } catch (e: Exception) {
                                                    val chooser = Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                                                        type = "text/plain"
                                                        putExtra(Intent.EXTRA_TEXT, shareText)
                                                    }, "Share via WhatsApp")
                                                    context.startActivity(chooser)
                                                }
                                            },
                                            modifier = Modifier.size(32.dp)
                                        ) {
                                            Icon(
                                                imageVector = Icons.Default.Share,
                                                contentDescription = "Share via WhatsApp",
                                                tint = Color(0xFF25D366),
                                                modifier = Modifier.size(18.dp)
                                            )
                                        }
                                        Spacer(modifier = Modifier.width(8.dp))
                                        IconButton(
                                            onClick = {
                                                val intent = Intent(Intent.ACTION_SENDTO).apply {
                                                    data = Uri.parse("mailto:")
                                                    putExtra(Intent.EXTRA_SUBJECT, "Diagnostic Report for Patient: ${slide.patient_name}")
                                                    putExtra(Intent.EXTRA_TEXT, shareText)
                                                }
                                                try {
                                                    context.startActivity(intent)
                                                } catch (e: Exception) {
                                                    val chooser = Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                                                        type = "text/plain"
                                                        putExtra(Intent.EXTRA_SUBJECT, "Diagnostic Report for Patient: ${slide.patient_name}")
                                                        putExtra(Intent.EXTRA_TEXT, shareText)
                                                    }, "Share via Email")
                                                    context.startActivity(chooser)
                                                }
                                            },
                                            modifier = Modifier.size(32.dp)
                                        ) {
                                            Icon(
                                                imageVector = Icons.Default.Email,
                                                contentDescription = "Share via Email",
                                                tint = Color(0xFF4F46E5),
                                                modifier = Modifier.size(18.dp)
                                            )
                                        }
                                    }
                                }
                            }
                        }
                        item {
                            Spacer(modifier = Modifier.height(24.dp))
                        }
                    }
                }
            }
        }
    }
}
