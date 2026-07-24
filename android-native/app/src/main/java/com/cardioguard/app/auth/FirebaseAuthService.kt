package com.cardioguard.app.auth

import android.content.Context
import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.GoogleAuthProvider

class FirebaseAuthService(private val context: Context) {
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()

    fun getCurrentUser(): FirebaseUser? {
        return auth.currentUser
    }

    fun getUserIdToken(forceRefresh: Boolean, callback: (String?, Exception?) -> Unit) {
        val user = auth.currentUser
        if (user == null) {
            callback(null, Exception("User is not signed in."))
            return
        }
        
        user.getIdToken(forceRefresh)
            .addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    val token = task.result?.token
                    callback(token, null)
                } else {
                    Log.e("FirebaseAuth", "Failed to retrieve Firebase ID token.", task.exception)
                    callback(null, task.exception)
                }
            }
    }

    fun signOut() {
        auth.signOut()
    }
}
