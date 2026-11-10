import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

const Duration _authTimeout = Duration(seconds: 15);

const String _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.216.203.21:8000', // Your PC's Wi-Fi IP — change if IP changes
);

class AuthUser {
  final String id;
  final String email;
  final String username;
  final String? fullName;

  AuthUser({
    required this.id,
    required this.email,
    required this.username,
    this.fullName,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
        id: json['id']?.toString() ?? '',
        email: json['email']?.toString() ?? '',
        username: json['username']?.toString() ?? '',
        fullName: json['full_name'],
      );
}

class AuthService extends ChangeNotifier {
  final _storage = const FlutterSecureStorage();

  AuthUser? _user;
  String? _token;
  bool _loading = false;
  String? _error;

  AuthUser? get user => _user;
  String? get token => _token;
  bool get isAuthenticated => _token != null && _user != null;
  bool get loading => _loading;
  String? get error => _error;

  Future<void> initialize() async {
    _token = await _storage.read(key: 'access_token');
    final userJson = await _storage.read(key: 'user_data');
    if (_token != null && userJson != null) {
      try {
        _user = AuthUser.fromJson(jsonDecode(userJson));
      } catch (_) {
        await logout();
      }
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      ).timeout(_authTimeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        _user = AuthUser.fromJson(data['user']);
        await _storage.write(key: 'access_token', value: _token);
        await _storage.write(key: 'user_data', value: jsonEncode(data['user']));
        _loading = false;
        notifyListeners();
        return true;
      } else {
        final data = _decodeError(response.body);
        _error = data ?? 'Login failed';
        _loading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Unable to connect. Please check your network and try again.';
      _loading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> signup({
    required String email,
    required String username,
    required String password,
    String? fullName,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'username': username,
          'password': password,
          if (fullName != null) 'full_name': fullName,
        }),
      ).timeout(_authTimeout);

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        _user = AuthUser.fromJson(data['user']);
        await _storage.write(key: 'access_token', value: _token);
        await _storage.write(key: 'user_data', value: jsonEncode(data['user']));
        _loading = false;
        notifyListeners();
        return true;
      } else {
        final data = _decodeError(response.body);
        _error = data ?? 'Signup failed';
        _loading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Connection error: $e';
      _loading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _token = null;
    _user = null;
    await _storage.deleteAll();
    notifyListeners();
  }

  String? _decodeError(String body) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) {
        final detail = decoded['detail'];
        if (detail is String && detail.isNotEmpty) return detail;
      }
    } catch (_) {}
    return null;
  }

  Map<String, String> get authHeaders => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };
}
