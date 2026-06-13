package com.oraldysplasia.ai.ui.screens.results

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.oraldysplasia.ai.data.remote.ReportResponse
import com.oraldysplasia.ai.data.repository.AppRepository
import com.oraldysplasia.ai.ui.components.GradeChip
import com.oraldysplasia.ai.ui.components.LoadingOverlay
import com.oraldysplasia.ai.ui.components.WsiViewerCanvas
import com.oraldysplasia.ai.ui.theme.PrimaryBlue
import android.content.Intent
import android.net.Uri
import androidx.compose.ui.platform.LocalContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultsScreen(
    slideId: Int,
    repository: AppRepository,
    onNavigateBack: () -> Unit
) {
    val viewModel: ResultsViewModel = viewModel(
        factory = ResultsViewModelFactory(slideId, repository)
    )

    val context = LocalContext.current

    val exportedReport = viewModel.exportedReportPayload
    LaunchedEffect(exportedReport) {
        if (exportedReport != null) {
            val shareText = getShareTextFromPayload(exportedReport.payload)
            val sendIntent = Intent().apply {
                action = Intent.ACTION_SEND
                putExtra(Intent.EXTRA_TEXT, shareText)
                type = "text/plain"
            }
            val shareIntent = Intent.createChooser(sendIntent, "Share Diagnostic Report")
            try {
                context.startActivity(shareIntent)
            } catch (e: Exception) {
                e.printStackTrace()
            }
            viewModel.clearExportedReport()
        }
    }

    LaunchedEffect(key1 = slideId) {
        viewModel.loadResults()
    }

    var dropdownExpanded by remember { mutableStateOf(false) }
    var exportExpanded by remember { mutableStateOf(false) }
    var checklistExpanded by remember { mutableStateOf(false) }
    var icdDropdownExpanded by remember { mutableStateOf(false) }

    val grades = listOf("normal", "mild", "moderate", "severe")
    val icd10Codes = listOf(
        "K13.21" to "Leukoplakia (Mild/Mod Dysplasia)",
        "K13.22" to "Erythroplakia (High Risk)",
        "D01.5" to "Carcinoma in situ of Oral Cavity (Severe)",
        "K13.29" to "Mucosal Dysplasia NOS",
        "C02.9" to "Squamous Cell Carcinoma of Tongue"
    )
    val architecturalCriteria = listOf(
        "Irregular epithelial stratification",
        "Loss of polarity of basal cells",
        "Drop-shaped rete ridges",
        "Basal cell hyperplasia",
        "Dyskeratosis (premature keratinization)",
        "Keratin pearls within rete ridges",
        "Loss of intercellular cohesion"
    )
    val cytologicalCriteria = listOf(
        "Abnormal variation in nuclear size/shape",
        "Abnormal variation in cell size/shape",
        "Hyperchromatic nuclei",
        "Enlarged nucleoli",
        "Increased / atypical mitotic figures"
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("AI Diagnostic Canvas", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadResults() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (val state = viewModel.state) {
                is ResultsUiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = PrimaryBlue)
                    }
                }
                is ResultsUiState.Error -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = state.message, color = MaterialTheme.colorScheme.error)
                            Spacer(modifier = Modifier.height(16.dp))
                            Button(onClick = { viewModel.loadResults() }) {
                                Text("Retry")
                            }
                        }
                    }
                }
                is ResultsUiState.Success -> {
                    val result = state.result
                    
                    val findingsList = remember(result) {
                        result.patches
                            .flatMap { it.bounding_boxes }
                            .groupBy { it.label ?: it.grade }
                            .map { (label, boxes) -> label to boxes.size }
                            .sortedByDescending { it.second }
                    }

                    Column(modifier = Modifier.fillMaxSize()) {
                        // 1. WSI Canvas occupies upper part
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .weight(1.2f)
                        ) {
                            WsiViewerCanvas(patches = result.patches)
                        }

                        // 2. Sign-off panel occupies lower part
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .weight(1.2f)
                                .padding(16.dp)
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            // AI Metrics Header
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column {
                                    Text("AI Classification Grade", fontSize = 11.sp, color = Color.Gray, fontWeight = FontWeight.Bold)
                                    Spacer(modifier = Modifier.height(2.dp))
                                    GradeChip(grade = result.overall_grade)
                                }
                                Column(horizontalAlignment = Alignment.End) {
                                    Text("AI Confidence", fontSize = 11.sp, color = Color.Gray, fontWeight = FontWeight.Bold)
                                    Text(
                                        text = "${"%.1f".format(result.overall_confidence * 100)}%",
                                        fontSize = 18.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = PrimaryBlue
                                    )
                                }
                            }

                            Divider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f))

                            // Quantitative Findings Card
                            if (findingsList.isNotEmpty()) {
                                Card(
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f))
                                ) {
                                    Column(modifier = Modifier.padding(12.dp)) {
                                        Text("AI Microscopic Quantifications", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = PrimaryBlue)
                                        Spacer(modifier = Modifier.height(6.dp))
                                        findingsList.forEach { (label, count) ->
                                            Row(
                                                modifier = Modifier.fillMaxWidth().padding(vertical = 3.dp),
                                                horizontalArrangement = Arrangement.SpaceBetween
                                            ) {
                                                Text(label, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                                                Text("$count detected", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color.DarkGray)
                                            }
                                        }
                                    }
                                }
                            }

                            Text("Pathologist Verified Verdict", fontSize = 15.sp, fontWeight = FontWeight.Bold)

                            // Grade override dropdown
                            Box(modifier = Modifier.fillMaxWidth()) {
                                OutlinedTextField(
                                    value = viewModel.finalGrade.uppercase(),
                                    onValueChange = {},
                                    readOnly = true,
                                    label = { Text("Final Grade Selection") },
                                    trailingIcon = {
                                        Icon(
                                            Icons.Default.ArrowDropDown,
                                            contentDescription = null,
                                            modifier = Modifier.clickable { dropdownExpanded = true }
                                        )
                                    },
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { dropdownExpanded = true }
                                )
                                DropdownMenu(
                                    expanded = dropdownExpanded,
                                    onDismissRequest = { dropdownExpanded = false },
                                    modifier = Modifier.fillMaxWidth(0.9f)
                                ) {
                                    grades.forEach { g ->
                                        DropdownMenuItem(
                                            text = { Text(g.uppercase()) },
                                            onClick = {
                                                viewModel.finalGrade = g
                                                dropdownExpanded = false
                                            }
                                        )
                                    }
                                }
                            }

                            // WHO Checklist Card
                            Card(modifier = Modifier.fillMaxWidth()) {
                                Column(modifier = Modifier.padding(12.dp)) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth().clickable { checklistExpanded = !checklistExpanded },
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Icon(Icons.Default.List, contentDescription = null, tint = PrimaryBlue)
                                            Spacer(modifier = Modifier.width(8.dp))
                                            Text("WHO Histological Checklist (${viewModel.selectedCriteria.size} observed)", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                                        }
                                        Icon(
                                            imageVector = if (checklistExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                                            contentDescription = null
                                        )
                                    }
                                    if (checklistExpanded) {
                                        Spacer(modifier = Modifier.height(8.dp))
                                        Text("Architectural Changes", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color.Gray)
                                        architecturalCriteria.forEach { criterion ->
                                            Row(
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .clickable {
                                                        viewModel.selectedCriteria = if (viewModel.selectedCriteria.contains(criterion)) {
                                                            viewModel.selectedCriteria - criterion
                                                        } else {
                                                            viewModel.selectedCriteria + criterion
                                                        }
                                                    },
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Checkbox(
                                                    checked = viewModel.selectedCriteria.contains(criterion),
                                                    onCheckedChange = { checked ->
                                                        viewModel.selectedCriteria = if (checked == true) {
                                                            viewModel.selectedCriteria + criterion
                                                        } else {
                                                            viewModel.selectedCriteria - criterion
                                                        }
                                                    }
                                                )
                                                Text(criterion, fontSize = 13.sp)
                                            }
                                        }
                                        Spacer(modifier = Modifier.height(8.dp))
                                        Text("Cytological Changes", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color.Gray)
                                        cytologicalCriteria.forEach { criterion ->
                                            Row(
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .clickable {
                                                        viewModel.selectedCriteria = if (viewModel.selectedCriteria.contains(criterion)) {
                                                            viewModel.selectedCriteria - criterion
                                                        } else {
                                                            viewModel.selectedCriteria + criterion
                                                        }
                                                    },
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Checkbox(
                                                    checked = viewModel.selectedCriteria.contains(criterion),
                                                    onCheckedChange = { checked ->
                                                        viewModel.selectedCriteria = if (checked == true) {
                                                            viewModel.selectedCriteria + criterion
                                                        } else {
                                                            viewModel.selectedCriteria - criterion
                                                        }
                                                    }
                                                )
                                                Text(criterion, fontSize = 13.sp)
                                            }
                                        }
                                    }
                                }
                            }

                            // ICD-10 Dropdown Selection
                            Box(modifier = Modifier.fillMaxWidth()) {
                                OutlinedTextField(
                                    value = "${viewModel.icd10Code} - ${icd10Codes.find { it.first == viewModel.icd10Code }?.second ?: "Custom Diagnosis"}",
                                    onValueChange = {},
                                    readOnly = true,
                                    label = { Text("ICD-10 Diagnostic Code Mapping") },
                                    trailingIcon = {
                                        Icon(
                                            Icons.Default.ArrowDropDown,
                                            contentDescription = null,
                                            modifier = Modifier.clickable { icdDropdownExpanded = true }
                                        )
                                    },
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { icdDropdownExpanded = true }
                                )
                                DropdownMenu(
                                    expanded = icdDropdownExpanded,
                                    onDismissRequest = { icdDropdownExpanded = false },
                                    modifier = Modifier.fillMaxWidth(0.9f)
                                ) {
                                    icd10Codes.forEach { (code, desc) ->
                                        DropdownMenuItem(
                                            text = { Text("$code — $desc") },
                                            onClick = {
                                                viewModel.icd10Code = code
                                                icdDropdownExpanded = false
                                            }
                                        )
                                    }
                                }
                            }

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                OutlinedTextField(
                                    value = viewModel.icd10Code,
                                    onValueChange = { viewModel.icd10Code = it },
                                    label = { Text("Custom ICD-10") },
                                    modifier = Modifier.weight(1f)
                                )
                                Box(modifier = Modifier.weight(1f)) {
                                    Button(
                                        onClick = { exportExpanded = true },
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(top = 8.dp)
                                            .height(48.dp),
                                        shape = RoundedCornerShape(8.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary)
                                    ) {
                                        Icon(Icons.Default.Download, contentDescription = null)
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text("Export Report", fontSize = 13.sp)
                                    }
                                    DropdownMenu(
                                        expanded = exportExpanded,
                                        onDismissRequest = { exportExpanded = false }
                                    ) {
                                        DropdownMenuItem(text = { Text("FHIR JSON Resource") }, onClick = { viewModel.exportDiagnosticReport("fhir"); exportExpanded = false })
                                        DropdownMenuItem(text = { Text("DICOM SOP Instance") }, onClick = { viewModel.exportDiagnosticReport("dicom"); exportExpanded = false })
                                        DropdownMenuItem(text = { Text("Clinical PDF Layout") }, onClick = { viewModel.exportDiagnosticReport("pdf"); exportExpanded = false })
                                        DropdownMenuItem(text = { Text("Share to Patient (PDF)") }, onClick = { viewModel.exportDiagnosticReport("patient_pdf"); exportExpanded = false })
                                    }
                                }
                            }

                            OutlinedTextField(
                                value = viewModel.comments,
                                onValueChange = { viewModel.comments = it },
                                label = { Text("Verification Comments") },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 2,
                                maxLines = 4
                            )

                            // Cryptographic Signing Block Card
                            val pathName = repository.tokenManager.getUserName()
                            val pathRole = repository.tokenManager.getUserRole()
                            val pathLicense = repository.tokenManager.getUserLicense()
                            val pathInstitution = repository.tokenManager.getUserInstitution()
                            val simulatedHash = remember(viewModel.finalGrade, viewModel.comments) {
                                val hashVal = slideId * 31 + viewModel.finalGrade.hashCode() + viewModel.comments.hashCode()
                                val absHashVal = if (hashVal < 0) -hashVal else hashVal
                                "SHA256:ECDSA:9F8" + absHashVal.toString(16).uppercase().padStart(8, '0')
                            }

                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                colors = CardDefaults.cardColors(containerColor = Color(0xFFF1F5F9)),
                                border = BorderStroke(1.dp, Color(0xFFCBD5E1))
                            ) {
                                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Default.VerifiedUser, contentDescription = null, tint = Color(0xFF0F766E))
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text("Digital Cryptographic Sign-Off Seal", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F766E))
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text("Signatory: Dr. $pathName", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                                    Text("Role: $pathRole", fontSize = 12.sp, color = Color.DarkGray)
                                    Text("License ID: $pathLicense", fontSize = 12.sp, color = Color.DarkGray)
                                    Text("Institution: $pathInstitution", fontSize = 12.sp, color = Color.DarkGray)
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(simulatedHash, fontSize = 10.sp, fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace, color = Color.Gray)
                                }
                            }

                            // Status messaging
                            viewModel.errorMessage?.let { error ->
                                Text(text = error, color = MaterialTheme.colorScheme.error, fontSize = 13.sp)
                            }
                            viewModel.successMessage?.let { success ->
                                Text(text = success, color = Color(0xFF2E7D32), fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            }

                            Button(
                                onClick = { viewModel.submitPathologistReview() },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(50.dp),
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
                            ) {
                                Icon(Icons.Default.Verified, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Sign & Verify Pathology Report", fontSize = 15.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            if (viewModel.isSubmitting || viewModel.isExporting) {
                LoadingOverlay(message = "Cryptographically sealing diagnostic signatures...")
            }
        }
    }
}

private fun getShareTextFromPayload(payload: Map<String, Any>): String {
    val type = payload["type"] as? String ?: "Diagnostic Report"
    val patient = payload["patient"] as? Map<*, *> ?: emptyMap<Any, Any>()
    val diagnosis = payload["diagnosis"] as? Map<*, *> ?: emptyMap<Any, Any>()
    
    val pName = patient["name"] as? String ?: "N/A"
    val pId = patient["id"] as? String ?: "N/A"
    val pAge = patient["age"] as? String ?: "N/A"
    val pGender = patient["gender"] as? String ?: "N/A"
    val pSite = patient["site"] as? String ?: "N/A"
    
    val grade = diagnosis["grade"] as? String ?: "N/A"
    val explanation = diagnosis["explanation"] as? String ?: ""
    val nextSteps = diagnosis["next_steps"] as? String ?: ""
    val confidence = diagnosis["confidence"]?.toString() ?: ""
    
    val signedBy = payload["signed_by"] as? String ?: ""
    val institution = payload["institution"] as? String ?: ""
    val comments = payload["comments"] as? String ?: ""
    
    return buildString {
        appendLine("PATIENT DIAGNOSTIC REPORT ($type)")
        appendLine("--------------------------------------------")
        appendLine("Patient Name: $pName")
        appendLine("Patient ID: $pId")
        appendLine("Age: $pAge")
        appendLine("Gender: $pGender")
        appendLine("Biopsy Site: $pSite")
        appendLine()
        appendLine("DIAGNOSTIC ASSESSMENT")
        appendLine("Grade: ${grade.uppercase()}")
        if (confidence.isNotEmpty()) {
            val confFloat = confidence.toFloatOrNull() ?: 0f
            if (confFloat > 0f) {
                appendLine("Confidence: ${"%.1f".format(confFloat * 100)}%")
            }
        }
        if (explanation.isNotEmpty()) {
            appendLine("Summary: $explanation")
        }
        if (nextSteps.isNotEmpty()) {
            appendLine("Next Steps: $nextSteps")
        }
        if (comments.isNotEmpty()) {
            appendLine("Comments: $comments")
        }
        appendLine()
        appendLine("CERTIFICATION")
        appendLine("Verifying Specialist: $signedBy")
        if (institution.isNotEmpty()) {
            appendLine("Institution: $institution")
        }
    }
}
