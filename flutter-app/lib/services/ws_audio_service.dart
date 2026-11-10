import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';

/// WebSocket-based real-time audio streaming service.
///
/// Connects to `ws://<host>/ws/analyze?token=<jwt>`.
/// Streams raw PCM audio frames (16kHz mono int16) and emits
/// parsed ThreatResult objects via [threatStream].
class WsAudioService {
  WebSocketChannel? _channel;
  final AudioRecorder _recorder = AudioRecorder();
  final _threatController = StreamController<Map<String, dynamic>>.broadcast();
  Timer? _pingTimer;
  StreamSubscription<Uint8List>? _audioSubscription;
  bool _isStreaming = false;

  Stream<Map<String, dynamic>> get threatStream => _threatController.stream;
  bool get isStreaming => _isStreaming;

  /// Connect to the WebSocket endpoint and start streaming audio.
  Future<void> startStreaming({
    required String host,
    required String token,
    int port = 8000,
  }) async {
    if (_isStreaming) return;

    final hasMic = await Permission.microphone.request().isGranted;
    if (!hasMic) {
      debugPrint('[WS] Microphone permission denied');
      return;
    }

    final wsUrl = Uri.parse('ws://$host:$port/ws/analyze?token=$token');
    debugPrint('[WS] Connecting to audio analysis endpoint');

    try {
      _channel = WebSocketChannel.connect(wsUrl);

      // Listen for JSON threat results from backend
      _channel!.stream.listen(
        (message) {
          try {
            final data = jsonDecode(message as String) as Map<String, dynamic>;
            debugPrint('[WS] Received: threat=${data['threat_level']}, score=${data['overall_threat_score']}');
            _threatController.add(data);
          } catch (e) {
            debugPrint('[WS] Parse error: ${e.runtimeType}');
          }
        },
        onError: (e) {
          debugPrint('[WS] Stream error: ${e.runtimeType}');
          stopStreaming();
        },
        onDone: () {
          debugPrint('[WS] Connection closed');
          _isStreaming = false;
        },
      );

      // Start microphone streaming
      final stream = await _recorder.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
        ),
      );

      _audioSubscription = stream.listen((data) {
        final channel = _channel;
        if (_isStreaming && channel != null) channel.sink.add(data);
      }, onError: (e) {
        debugPrint('[WS] Audio stream error: ${e.runtimeType}');
        stopStreaming();
      });

      _isStreaming = true;
      debugPrint('[WS] Audio streaming started');
    } catch (e) {
      debugPrint('[WS] Failed to start streaming: ${e.runtimeType}');
    }
  }

  /// Send raw PCM bytes to the server.
  void sendAudioFrame(Uint8List pcmBytes) {
    if (_channel != null && _isStreaming) {
      _channel!.sink.add(pcmBytes);
    }
  }

  /// Stop streaming and close connections.
  Future<void> stopStreaming() async {
    _isStreaming = false;
    _pingTimer?.cancel();
    _pingTimer = null;
    await _audioSubscription?.cancel();
    _audioSubscription = null;

    if (await _recorder.isRecording()) {
      await _recorder.stop();
    }

    await _channel?.sink.close();
    _channel = null;
    debugPrint('[WS] Streaming stopped');
  }

  void dispose() {
    stopStreaming();
    _threatController.close();
    _recorder.dispose();
  }
}
