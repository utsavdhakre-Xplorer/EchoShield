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
  defaultValue: 'https://echoshield-api-9lg0.onrender.com',
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
  bool _chunkInProgress = false;
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
    debugPrint('[AUTH] Call monitor token ${token == null || token.isEmpty ? 'missing' : 'loaded'}');
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
    if (_token == null || _token!.isEmpty) {
      _error = 'Session expired. Please log out and log in again.';
      notifyListeners();
      return;
    }
    _isMonitoring = true;
    _error = null;
    notifyListeners();
  }

  Future<void> stopMonitoring() async {
    _isMonitoring = false;
    _isCallActive = false;
    await _stopRecording();
    await _wsService.stopStreaming();
    notifyListeners();
  }

  /// Called when a call is detected (from phone_state plugin or manually)
  Future<void> onCallStarted({String? callerNumber}) async {
    if (!_isMonitoring) return;
    _resetForNewCall();
    _isCallActive = true;
    notifyListeners();

    // Start real-time WebSocket streaming
    final host = _baseUrl
        .replaceAll('https://', '')
        .replaceAll('http://', '')
        .split(':').first;
    // Use the authenticated HTTP chunk pipeline. The WebSocket stream is
    // currently rejected by Render with HTTP 403 for this mobile client, and
    // was competing with the same microphone capture used by chunk recording.
    // The chunk pipeline below persists analysis results to the user's call log.

    // Cancel any previous WS listener before creating a new one (prevents duplicate listeners)
    await _wsSubscription?.cancel();
    _wsSubscription = null;
    /* _wsService threat listener disabled; HTTP chunk endpoint is authoritative.
    _wsSubscription = _wsService.threatStream.listen((data) {
      if (!_isMonitoring || !_isCallActive) return;
      final transcript = (data['transcript'] ?? '').toString().trim();
      if (transcript.isEmpty ||
          transcript.startsWith('[Transcription unavailable') ||
          transcript == '[No speech detected]') {
        debugPrint('[WS] No usable speech transcript; suppressing threat alert');
        return;
      }
      final result = ThreatResult.fromJson(data);
      _latestThreat = result;
      _currentCallId ??= result.callLogId;
      if (result.alertRequired) {
        _triggerAlert(result);
      }
      notifyListeners();
    });
    */

    await _startChunkedRecording(callerNumber: callerNumber);
  }

  Future<void> onCallEnded() async {
    if (!_isCallActive) return;
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
    if (_chunkInProgress || !_isMonitoring || !_isCallActive) return;
    _chunkInProgress = true;
    // Use the app's proper temp directory — /tmp/ does not exist on real Android devices
    final tmpDir = await getTemporaryDirectory();
    final tmpPath = '${tmpDir.path}/echoshield_chunk_$_chunkIndex.wav';

    try {
      if (!_isMonitoring || !_isCallActive) return;
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

      debugPrint('[CALL] Captured audio chunk $_chunkIndex (${file.lengthSync()} bytes); sending to API');
      if (_token == null || _token!.isEmpty) {
        debugPrint('[AUTH] No access token; stopping audio upload.');
        _error = 'Session expired. Please log out and log in again.';
        return;
      }
      final result = await _sendAudioChunk(
        file,
        callId: _currentCallId,
        chunkIndex: _chunkIndex,
        callerNumber: callerNumber,
      );

      if (result != null &&
          _isMonitoring &&
          _isCallActive &&
          result.transcript.trim().isNotEmpty &&
          !result.transcript.startsWith('[Transcription unavailable') &&
          result.transcript != '[No speech detected]') {
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
    } finally {
      _chunkInProgress = false;
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
        debugPrint('[CALL] API analysis succeeded for chunk $chunkIndex');
        return ThreatResult.fromJson(jsonDecode(response.body));
      }
      debugPrint('[CALL] Audio API failed: HTTP ${response.statusCode}; responseBytes=${response.body.length}');
      if (response.statusCode == 401) {
        _error = 'Login session expired. Please log out and log in again.';
        _token = null;
        notifyListeners();
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
    if (await Vibration.hasVibrator()) {
      final pattern = result.threatLevel == ThreatLevel.critical
          ? [0, 500, 200, 500, 200, 500]
          : [0, 300, 200, 300];
      Vibration.vibrate(pattern: pattern);
    }

    // Push notification
    await NotificationService.showThreatAlert(
      level: result.threatLevel.name.toUpperCase(),
      score: result.overallThreatScore,
    );
  }

  /// Simulate a scam call for testing
  Future<void> simulateScamCall() async {
    if (_token == null || _token!.isEmpty) {
      _error = 'Please log in again to run the simulation.';
      notifyListeners();
      return;
    }

    _isCallActive = true;
    _error = null;
    notifyListeners();

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
      } else {
        _error = response.statusCode == 401
          ? 'Login session expired. Please log out and log in again.'
          : 'Simulation failed (HTTP ${response.statusCode}). Please try again.';
      if (response.statusCode == 401) _token = null;
        debugPrint('Simulate call failed with status ${response.statusCode}');
        notifyListeners();
      }
    } catch (e) {
      _error = 'Unable to reach EchoShield server. Check your connection.';
      debugPrint('Simulate call error: ${e.runtimeType}');
      notifyListeners();
    } finally {
      await Future.delayed(const Duration(seconds: 2));
      _isCallActive = false;
      notifyListeners();
    }
  }

  /// Clear the currently visible alert without starting another analysis.
  void dismissThreatAlert() {
    _latestThreat = null;
    notifyListeners();
  }

  void _resetForNewCall() {
    _latestThreat = null;
    _currentCallId = null;
    _chunkIndex = 0;
    _error = null;
  }

  @override
  void dispose() {
    _chunkTimer?.cancel();
    _wsSubscription?.cancel();
    _recorder.dispose();
    _wsService.dispose();
    super.dispose();
  }
}
