import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:vibration/vibration.dart';
import 'notification_service.dart';
import 'ws_audio_service.dart';

const String _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.202.181.147:8000', // Your PC's Wi-Fi IP — change if IP changes
);

enum ThreatLevel { low, medium, high, critical }

class ThreatResult {
  final String callLogId;
  final String transcript;
  final bool isDeepfake;
  final double deepfakeConfidence;
  final bool urgencyDetected;
  final double urgencyScore;
  final List<String> urgencyPhrasesFound;
  final double overallThreatScore;
  final ThreatLevel threatLevel;
  final String negotiatorStrategy;
  final bool alertRequired;
  final DateTime timestamp;

  ThreatResult({
    required this.callLogId,
    required this.transcript,
    required this.isDeepfake,
    required this.deepfakeConfidence,
    required this.urgencyDetected,
    required this.urgencyScore,
    required this.urgencyPhrasesFound,
    required this.overallThreatScore,
    required this.threatLevel,
    required this.negotiatorStrategy,
    required this.alertRequired,
    required this.timestamp,
  });

  factory ThreatResult.fromJson(Map<String, dynamic> json) {
    ThreatLevel level;
    switch (json['threat_level']) {
      case 'CRITICAL':
        level = ThreatLevel.critical;
        break;
      case 'HIGH':
        level = ThreatLevel.high;
        break;
      case 'MEDIUM':
        level = ThreatLevel.medium;
        break;
      default:
        level = ThreatLevel.low;
    }
    return ThreatResult(
      callLogId: json['call_log_id'] ?? '',
      transcript: json['transcript'] ?? '',
      isDeepfake: json['is_deepfake'] ?? false,
      deepfakeConfidence: (json['deepfake_confidence'] ?? 0.0).toDouble(),
      urgencyDetected: json['urgency_detected'] ?? false,
      urgencyScore: (json['urgency_score'] ?? 0.0).toDouble(),
      urgencyPhrasesFound: List<String>.from(json['urgency_phrases_found'] ?? []),
      overallThreatScore: (json['overall_threat_score'] ?? 0.0).toDouble(),
      threatLevel: level,
      negotiatorStrategy: json['negotiator_strategy'] ?? '',
      alertRequired: json['alert_required'] ?? false,
      timestamp: DateTime.now(),
    );
  }
}

class CallMonitorService extends ChangeNotifier {
  final AudioRecorder _recorder = AudioRecorder();
  final WsAudioService _wsService = WsAudioService();

  bool _isMonitoring = false;
  bool _isCallActive = false;
  bool _isRecording = false;
  ThreatResult? _latestThreat;
  String? _currentCallId;
  String? _token;
  final List<ThreatResult> _threatHistory = [];
  Timer? _chunkTimer;
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;
  int _chunkIndex = 0;
  String? _error;

  bool get isMonitoring => _isMonitoring;
  bool get isCallActive => _isCallActive;
  bool get isRecording => _isRecording;
  ThreatResult? get latestThreat => _latestThreat;
  List<ThreatResult> get threatHistory => _threatHistory;
  String? get error => _error;

  void setToken(String? token) {
    _token = token;
  }

  Future<bool> requestPermissions() async {
    final statuses = await [
      Permission.microphone,
      Permission.phone,
    ].request();
    return statuses.values.every((s) => s.isGranted);
  }

  Future<void> startMonitoring() async {
    final hasPermissions = await requestPermissions();
    if (!hasPermissions) {
      _error = 'Microphone and phone permissions required';
      notifyListeners();
      return;
    }
    _isMonitoring = true;
    _error = null;
    notifyListeners();
  }

  void stopMonitoring() {
    _isMonitoring = false;
    _stopRecording();
    notifyListeners();
  }

  /// Called when a call is detected (from phone_state plugin or manually)
  Future<void> onCallStarted({String? callerNumber}) async {
    if (!_isMonitoring) return;
    _isCallActive = true;
    _currentCallId = null;
    _chunkIndex = 0;
    notifyListeners();

    // Start real-time WebSocket streaming
    final host = _baseUrl
        .replaceAll('https://', '')
        .replaceAll('http://', '')
        .split(':').first;
    _wsService.startStreaming(
      host: host,
      token: _token ?? '',
    );

    // Cancel any previous WS listener before creating a new one (prevents duplicate listeners)
    await _wsSubscription?.cancel();
    _wsSubscription = _wsService.threatStream.listen((data) {
      final result = ThreatResult.fromJson(data);
      _latestThreat = result;
      _currentCallId ??= result.callLogId;
      if (result.alertRequired) {
        _triggerAlert(result);
      }
      notifyListeners();
    });

    await _startChunkedRecording(callerNumber: callerNumber);
  }

  Future<void> onCallEnded() async {
    _isCallActive = false;
    await _wsSubscription?.cancel();
    _wsSubscription = null;
    await _stopRecording();
    await _wsService.stopStreaming();
    notifyListeners();
  }

  Future<void> _startChunkedRecording({String? callerNumber}) async {
    _isRecording = true;
    notifyListeners();

    // Record and send audio every 5 seconds
    _chunkTimer = Timer.periodic(const Duration(seconds: 5), (_) async {
      await _recordAndSendChunk(callerNumber: callerNumber);
    });
  }

  Future<void> _recordAndSendChunk({String? callerNumber}) async {
    // Use the app's proper temp directory — /tmp/ does not exist on real Android devices
    final tmpDir = await getTemporaryDirectory();
    final tmpPath = '${tmpDir.path}/echoshield_chunk_$_chunkIndex.wav';

    try {
      if (await _recorder.isRecording()) {
        await _recorder.stop();
      }

      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        ),
        path: tmpPath,
      );

      // Record for 4 seconds
      await Future.delayed(const Duration(seconds: 4));
      await _recorder.stop();

      // Send to backend
      final file = File(tmpPath);
      if (!file.existsSync()) return;

      final result = await _sendAudioChunk(
        file,
        callId: _currentCallId,
        chunkIndex: _chunkIndex,
        callerNumber: callerNumber,
      );

      if (result != null) {
        _currentCallId ??= result.callLogId;
        _latestThreat = result;
        _threatHistory.insert(0, result);

        if (result.alertRequired) {
          await _triggerAlert(result);
        }
        notifyListeners();
      }

      _chunkIndex++;
      file.deleteSync();
    } catch (e) {
      debugPrint('Recording chunk error: $e');
    }
  }

  Future<ThreatResult?> _sendAudioChunk(
    File audioFile, {
    String? callId,
    int chunkIndex = 0,
    String? callerNumber,
  }) async {
    if (_token == null) return null;

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/stream-audio'),
      );
      request.headers['Authorization'] = 'Bearer $_token';
      request.files.add(await http.MultipartFile.fromPath('audio', audioFile.path));
      if (callId != null) request.fields['call_id'] = callId;
      request.fields['chunk_index'] = chunkIndex.toString();
      if (callerNumber != null) request.fields['caller_number'] = callerNumber;

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);

      if (response.statusCode == 200) {
        return ThreatResult.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      debugPrint('API send error: $e');
    }
    return null;
  }

  Future<void> _stopRecording() async {
    _chunkTimer?.cancel();
    _chunkTimer = null;
    await _wsSubscription?.cancel();
    _wsSubscription = null;
    if (await _recorder.isRecording()) {
      await _recorder.stop();
    }
    _isRecording = false;
    notifyListeners();
  }

  Future<void> _triggerAlert(ThreatResult result) async {
    // Vibrate
    if (await Vibration.hasVibrator() ?? false) {
      final pattern = result.threatLevel == ThreatLevel.critical
          ? [0, 500, 200, 500, 200, 500]
          : [0, 300, 200, 300];
      Vibration.vibrate(pattern: pattern);
    }

    // Push notification
    await NotificationService.showThreatAlert(
      level: result.threatLevel.name.toUpperCase(),
      score: result.overallThreatScore,
      transcript: result.transcript,
    );
  }

  /// Simulate a scam call for testing
  Future<void> simulateScamCall() async {
    _isCallActive = true;
    notifyListeners();

    if (_token == null) return;

    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/analyze'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
        body: jsonEncode({
          'transcript':
              'This is the IRS calling. Your account will be blocked unless you send money immediately. Don\'t hang up. Transfer funds now to avoid arrest.',
        }),
      );

      if (response.statusCode == 200) {
        final result = ThreatResult.fromJson(jsonDecode(response.body));
        _latestThreat = result;
        _threatHistory.insert(0, result);
        if (result.alertRequired) {
          await _triggerAlert(result);
        }
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Simulate call error: $e');
    }

    await Future.delayed(const Duration(seconds: 2));
    _isCallActive = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _chunkTimer?.cancel();
    _recorder.dispose();
    super.dispose();
  }
}
