package com.oraldysplasia.ai.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "slides")
data class SlideEntity(
    @PrimaryKey val id: Int,
    val userId: Int,
    val patientId: String,
    val patientName: String,
    val patientAge: String?,
    val patientGender: String?,
    val anatomicalSite: String,
    val filename: String,
    val sizeBytes: Long,
    val width: Int,
    val height: Int,
    val status: String,
    val currentGrade: String,
    val overallConfidence: Float,
    val clinicalNotes: String?,
    val createdAt: String
)
