package com.oraldysplasia.ai.data.local

import android.content.Context
import androidx.room.*

@Dao
interface SlideDao {
    @Query("SELECT * FROM slides ORDER BY createdAt DESC")
    suspend fun getAllSlides(): List<SlideEntity>

    @Query("SELECT * FROM slides WHERE id = :slideId")
    suspend fun getSlideById(slideId: Int): SlideEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSlides(slides: List<SlideEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSlide(slide: SlideEntity)

    @Query("DELETE FROM slides")
    suspend fun clearAll()
}

@Database(entities = [SlideEntity::class], version = 2, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun slideDao(): SlideDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "oraldysplasia_cache_db"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
