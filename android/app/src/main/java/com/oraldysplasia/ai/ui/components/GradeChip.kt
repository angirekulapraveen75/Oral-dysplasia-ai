package com.oraldysplasia.ai.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.oraldysplasia.ai.ui.theme.*

@Composable
fun GradeChip(
    grade: String,
    modifier: Modifier = Modifier
) {
    val cleanGrade = grade.lowercase().trim()
    val (backgroundColor, textColor, label) = when (cleanGrade) {
        "mild" -> Triple(GradeMild.copy(alpha = 0.12f), GradeMild, "MILD DYSPLASIA")
        "moderate" -> Triple(GradeModerate.copy(alpha = 0.12f), GradeModerate, "MODERATE DYSPLASIA")
        "severe" -> Triple(GradeSevere.copy(alpha = 0.12f), GradeSevere, "SEVERE DYSPLASIA")
        "normal" -> Triple(GradeNormal.copy(alpha = 0.12f), GradeNormal, "NORMAL / BENIGN")
        else -> Triple(GradePending.copy(alpha = 0.12f), GradePending, "PENDING DIAGNOSIS")
    }

    Text(
        text = label,
        color = textColor,
        fontSize = 11.sp,
        fontWeight = FontWeight.Bold,
        modifier = modifier
            .clip(RoundedCornerShape(6.dp))
            .background(backgroundColor)
            .border(1.dp, textColor.copy(alpha = 0.3f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp)
    )
}
