package com.oraldysplasia.ai.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.oraldysplasia.ai.data.remote.PatchResultDto
import com.oraldysplasia.ai.ui.theme.*

@OptIn(ExperimentalTextApi::class)
@Composable
fun WsiViewerCanvas(
    patches: List<PatchResultDto>,
    modifier: Modifier = Modifier
) {
    var scale by remember { mutableStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    
    val textMeasurer = rememberTextMeasurer()

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFFF9F6F0)) // Pale beige color matching standard digital glass background
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, _ ->
                    scale = (scale * zoom).coerceIn(0.5f, 6.0f)
                    // Panning matches zoom scale
                    offset = if (scale > 0.5f) offset + pan else Offset.Zero
                }
            }
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val canvasWidth = size.width
            val canvasHeight = size.height

            // 1. Draw a simulated H&E stained Whole Slide Tissue in the center
            val tissueWidth = 1024f * scale
            val tissueHeight = 1024f * scale
            val tissueX = (canvasWidth - tissueWidth) / 2f + offset.x
            val tissueY = (canvasHeight - tissueHeight) / 2f + offset.y

            // Draw primary tissue background (pinkish H&E staining simulation)
            drawRect(
                color = Color(0xFFF3E5F5), // Light purple
                topLeft = Offset(tissueX, tissueY),
                size = Size(tissueWidth, tissueHeight)
            )

            // Draw cell/nuclei clusters as small scattered dots for realistic appearance
            val randomPoints = listOf(
                Offset(0.2f, 0.3f), Offset(0.5f, 0.4f), Offset(0.7f, 0.2f),
                Offset(0.3f, 0.7f), Offset(0.6f, 0.8f), Offset(0.8f, 0.6f),
                Offset(0.4f, 0.5f), Offset(0.1f, 0.8f), Offset(0.9f, 0.1f)
            )
            randomPoints.forEach { pt ->
                drawCircle(
                    color = Color(0xFF8E24AA).copy(alpha = 0.3f), // Violet hematoxylin
                    radius = 35f * scale,
                    center = Offset(tissueX + pt.x * tissueWidth, tissueY + pt.y * tissueHeight)
                )
            }

            // 2. Render patches (256x256 tiles)
            val tileSize = 256f * scale
            patches.forEach { patch ->
                val tileX = tissueX + (patch.x_index * tileSize)
                val tileY = tissueY + (patch.y_index * tileSize)

                // Only draw if visible on canvas
                if (tileX + tileSize >= 0 && tileX <= canvasWidth && tileY + tileSize >= 0 && tileY <= canvasHeight) {
                    val tileColor = when (patch.predicted_grade.lowercase()) {
                        "mild" -> GradeMild
                        "moderate" -> GradeModerate
                        "severe" -> GradeSevere
                        else -> Color.Transparent
                    }

                    // Draw colored grid border if dysplastic
                    if (tileColor != Color.Transparent) {
                        drawRect(
                            color = tileColor.copy(alpha = 0.2f),
                            topLeft = Offset(tileX, tileY),
                            size = Size(tileSize, tileSize)
                        )
                        drawRect(
                            color = tileColor.copy(alpha = 0.4f),
                            topLeft = Offset(tileX, tileY),
                            size = Size(tileSize, tileSize),
                            style = Stroke(width = 2f)
                        )
                    }

                    // 3. Draw bounding boxes inside this patch
                    patch.bounding_boxes.forEach { box ->
                        // Bounding boxes are stored relative to a 256x256 patch coordinate space (0-256)
                        val boxXmin = tileX + (box.xmin / 256f * tileSize)
                        val boxYmin = tileY + (box.ymin / 256f * tileSize)
                        val boxXmax = tileX + (box.xmax / 256f * tileSize)
                        val boxYmax = tileY + (box.ymax / 256f * tileSize)

                        val boxW = boxXmax - boxXmin
                        val boxH = boxYmax - boxYmin

                        val boxGradeLower = box.grade.lowercase()
                        val boxColor = when (boxGradeLower) {
                            "severe" -> GradeSevere
                            "moderate" -> GradeModerate
                            "mild" -> GradeMild
                            else -> GradeNormal
                        }

                        // Draw bounding box rectangle
                        drawRect(
                            color = boxColor,
                            topLeft = Offset(boxXmin, boxYmin),
                            size = Size(boxW, boxH),
                            style = Stroke(width = 3f * scale)
                        )

                        // Draw background label badge if zoom scale is big enough
                        if (scale >= 1.2f) {
                            val displayLabel = if (!box.label.isNullOrEmpty()) {
                                "${box.label} (${"%.0f".format(box.confidence * 100)}%)"
                            } else {
                                "${box.grade.uppercase()} ${"%.0f".format(box.confidence * 100)}%"
                            }
                            val textLayoutResult = textMeasurer.measure(
                                text = AnnotatedString(displayLabel),
                                style = TextStyle(
                                    color = Color.White,
                                    fontSize = (9f * scale).coerceAtMost(14f).sp,
                                    fontWeight = FontWeight.Bold
                                )
                            )

                            // Label background
                            drawRect(
                                color = boxColor,
                                topLeft = Offset(boxXmin, boxYmin - textLayoutResult.size.height),
                                size = Size(textLayoutResult.size.width.toFloat() + 8f, textLayoutResult.size.height.toFloat())
                            )

                            // Label text
                            drawText(
                                textLayoutResult = textLayoutResult,
                                topLeft = Offset(boxXmin + 4f, boxYmin - textLayoutResult.size.height)
                            )
                        }
                    }
                }
            }

            // Draw a subtle focus target indicator in the absolute center
            drawCircle(
                color = PrimaryBlue.copy(alpha = 0.2f),
                radius = 12f,
                center = Offset(canvasWidth / 2, canvasHeight / 2),
                style = Stroke(width = 2f)
            )
        }
    }
}
