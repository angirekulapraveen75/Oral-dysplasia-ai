package com.oraldysplasia.ai

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.List
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.oraldysplasia.ai.data.repository.AppRepository

sealed class Screen(val route: String, val title: String, val icon: ImageVector? = null) {
    object Splash : Screen("splash", "Splash")
    object Login : Screen("login", "Login")
    object SignUp : Screen("signup", "Sign Up")
    object Home : Screen("home", "Home", Icons.Default.Home)
    object Upload : Screen("upload", "Upload", Icons.Default.Add)
    object Library : Screen("library", "Library", Icons.Default.List)
    object Profile : Screen("profile", "Profile", Icons.Default.AccountCircle)
    
    // Screens with arguments
    object Detail : Screen("detail/{slideId}", "Slide Detail") {
        fun createRoute(slideId: Int) = "detail/$slideId"
    }
    object Analysis : Screen("analysis/{slideId}", "AI Analysis") {
        fun createRoute(slideId: Int) = "analysis/$slideId"
    }
    object Results : Screen("results/{slideId}", "Results") {
        fun createRoute(slideId: Int) = "results/$slideId"
    }
}

@Composable
fun OralDysplasiaApp(
    repository: AppRepository,
    navController: NavHostController = rememberNavController()
) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    // Show bottom bar only on core user screens
    val showBottomBar = currentRoute in listOf(
        Screen.Home.route,
        Screen.Upload.route,
        Screen.Library.route,
        Screen.Profile.route
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    val items = listOf(Screen.Home, Screen.Upload, Screen.Library, Screen.Profile)
                    items.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon!!, contentDescription = screen.title) },
                            label = { Text(screen.title) },
                            selected = currentRoute == screen.route,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Splash.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            // Splash
            composable(Screen.Splash.route) {
                com.oraldysplasia.ai.ui.screens.splash.SplashScreen(
                    repository = repository,
                    onNavigateToLogin = {
                        navController.navigate(Screen.Login.route) {
                            popUpTo(Screen.Splash.route) { inclusive = true }
                        }
                    },
                    onNavigateToHome = {
                        navController.navigate(Screen.Home.route) {
                            popUpTo(Screen.Splash.route) { inclusive = true }
                        }
                    }
                )
            }

            // Auth
            composable(Screen.Login.route) {
                com.oraldysplasia.ai.ui.screens.auth.LoginScreen(
                    repository = repository,
                    onNavigateToHome = {
                        navController.navigate(Screen.Home.route) {
                            popUpTo(Screen.Login.route) { inclusive = true }
                        }
                    },
                    onNavigateToSignUp = {
                        navController.navigate(Screen.SignUp.route)
                    }
                )
            }
            composable(Screen.SignUp.route) {
                com.oraldysplasia.ai.ui.screens.auth.SignUpScreen(
                    repository = repository,
                    onNavigateToHome = {
                        navController.navigate(Screen.Home.route) {
                            popUpTo(Screen.SignUp.route) { inclusive = true }
                        }
                    },
                    onNavigateToLogin = {
                        navController.navigate(Screen.Login.route) {
                            popUpTo(Screen.SignUp.route) { inclusive = true }
                        }
                    }
                )
            }

            // Core
            composable(Screen.Home.route) {
                com.oraldysplasia.ai.ui.screens.home.HomeScreen(
                    repository = repository,
                    onNavigateToUpload = { navController.navigate(Screen.Upload.route) },
                    onNavigateToDetail = { id -> navController.navigate(Screen.Detail.createRoute(id)) }
                )
            }
            composable(Screen.Upload.route) {
                com.oraldysplasia.ai.ui.screens.upload.UploadScreen(
                    repository = repository,
                    onNavigateToDetail = { id ->
                        navController.navigate(Screen.Detail.createRoute(id)) {
                            popUpTo(Screen.Upload.route) { inclusive = true }
                        }
                    }
                )
            }
            composable(Screen.Library.route) {
                com.oraldysplasia.ai.ui.screens.library.LibraryScreen(
                    repository = repository,
                    onNavigateToDetail = { id -> navController.navigate(Screen.Detail.createRoute(id)) }
                )
            }
            composable(Screen.Profile.route) {
                com.oraldysplasia.ai.ui.screens.profile.ProfileScreen(
                    repository = repository,
                    onLogout = {
                        navController.navigate(Screen.Login.route) {
                            popUpTo(Screen.Home.route) { inclusive = true }
                        }
                    }
                )
            }

            // Slide Specific
            composable(
                route = Screen.Detail.route,
                arguments = listOf(navArgument("slideId") { type = NavType.IntType })
            ) { backStackEntry ->
                val slideId = backStackEntry.arguments?.getInt("slideId") ?: -1
                com.oraldysplasia.ai.ui.screens.detail.SlideDetailScreen(
                    slideId = slideId,
                    repository = repository,
                    onNavigateBack = { navController.popBackStack() },
                    onNavigateToAnalysis = { id -> navController.navigate(Screen.Analysis.createRoute(id)) },
                    onNavigateToResults = { id -> navController.navigate(Screen.Results.createRoute(id)) }
                )
            }
            composable(
                route = Screen.Analysis.route,
                arguments = listOf(navArgument("slideId") { type = NavType.IntType })
            ) { backStackEntry ->
                val slideId = backStackEntry.arguments?.getInt("slideId") ?: -1
                com.oraldysplasia.ai.ui.screens.analysis.AnalysisScreen(
                    slideId = slideId,
                    repository = repository,
                    onNavigateBack = { navController.popBackStack() }
                )
            }
            composable(
                route = Screen.Results.route,
                arguments = listOf(navArgument("slideId") { type = NavType.IntType })
            ) { backStackEntry ->
                val slideId = backStackEntry.arguments?.getInt("slideId") ?: -1
                com.oraldysplasia.ai.ui.screens.results.ResultsScreen(
                    slideId = slideId,
                    repository = repository,
                    onNavigateBack = { navController.popBackStack() }
                )
            }
        }
    }
}
