package com.example.echoshield

import android.telecom.Call
import android.telecom.CallScreeningService

/**
 * Platform-feasibility scaffold for Android's user-authorized call screening role.
 * It currently allows calls unchanged; it does not identify, score, or block callers.
 * Screening role approval and device testing are required before enabling protection UX.
 */
class EchoShieldCallScreeningService : CallScreeningService() {
    override fun onScreenCall(callDetails: Call.Details) {
        val response = CallResponse.Builder()
            .setDisallowCall(false)
            .setRejectCall(false)
            .setSkipCallLog(false)
            .setSkipNotification(false)
            .build()
        respondToCall(callDetails, response)
    }
}
