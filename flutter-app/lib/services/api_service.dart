import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

const Duration _requestTimeout = Duration(seconds: 15);
const int _maxTranscriptLength = 10000;

const String _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://echoshield-api-9lg0.onrender.com', // Your PC's IP address
);

class ApiService {
  final String token;
  ApiService({required this.token});

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };

  Future<Map<String, dynamic>?> getStats() async {
    try {
      final res = await http.get(Uri.parse('$_baseUrl/stats'), headers: _headers).timeout(_requestTimeout);
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return null;
  }

  Future<List<dynamic>> getCallLogs({int limit = 20}) async {
    try {
      final safeLimit = limit.clamp(1, 100);
      final res = await http.get(
        Uri.parse('$_baseUrl/call-logs?limit=$safeLimit'),
        headers: _headers,
      ).timeout(_requestTimeout);
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return [];
  }

  Future<Map<String, dynamic>?> analyzeText(String transcript) async {
    final normalizedTranscript = transcript.trim();
    if (normalizedTranscript.length < 5 ||
        normalizedTranscript.length > _maxTranscriptLength) {
      debugPrint('[API] Transcript rejected: invalid length');
      return null;
    }

    try {
      final res = await http.post(
        Uri.parse('$_baseUrl/analyze'),
        headers: _headers,
        body: jsonEncode({'transcript': normalizedTranscript}),
      ).timeout(const Duration(seconds: 65));

      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        if (decoded is Map<String, dynamic>) return decoded;
        debugPrint('[API] Analyze returned an unexpected response format');
      } else {
        debugPrint('[API] Analyze request failed with status ${res.statusCode}');
      }
    } on http.ClientException {
      debugPrint('[API] Analyze network request failed');
    } on FormatException {
      debugPrint('[API] Analyze response was not valid JSON');
    } catch (e) {
      debugPrint('[API] Analyze request failed: ${e.runtimeType}');
    }
    return null;
  }
}
