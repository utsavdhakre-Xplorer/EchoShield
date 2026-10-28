import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import 'dart:typed_data';

class NotificationService {
  static final _plugin = FlutterLocalNotificationsPlugin();

  static Future<void> initialize() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    await _plugin.initialize(settings);
  }

  static Future<void> showThreatAlert({
    required String level,
    required double score,
    required String transcript,
  }) async {
    final androidDetails = AndroidNotificationDetails(
      'echoshield_threats',
      'EchoShield Threat Alerts',
      channelDescription: 'Real-time scam call threat alerts',
      importance: Importance.max,
      priority: Priority.high,
      ticker: 'SCAM ALERT',
      color: const Color(0xFFFF0055),
      enableLights: true,
      ledColor: const Color(0xFFFF0055),
      ledOnMs: 200,
      ledOffMs: 200,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 500, 200, 500]),
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    final snippet = transcript.length > 80
        ? '${transcript.substring(0, 80)}...'
        : transcript;

    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      '⚠️ $level THREAT DETECTED',
      'Score: ${(score * 100).toStringAsFixed(0)}% | "$snippet"',
      details,
    );
  }
}

class AndroidColor {
  final int value;
  const AndroidColor(this.value);
}
