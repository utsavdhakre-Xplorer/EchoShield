import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  final _loginFormKey = GlobalKey<FormState>();
  final _signupFormKey = GlobalKey<FormState>();

  // Login fields
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();

  // Signup fields
  final _sEmailCtrl = TextEditingController();
  final _sUsernameCtrl = TextEditingController();
  final _sPassCtrl = TextEditingController();
  final _sNameCtrl = TextEditingController();

  bool _obscurePass = true;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _sEmailCtrl.dispose();
    _sUsernameCtrl.dispose();
    _sPassCtrl.dispose();
    _sNameCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_loginFormKey.currentState!.validate()) return;
    final auth = context.read<AuthService>();
    final ok = await auth.login(_emailCtrl.text.trim(), _passCtrl.text);
    if (ok && mounted) {
      Navigator.pushReplacementNamed(context, '/dashboard');
    }
  }

  Future<void> _signup() async {
    if (!_signupFormKey.currentState!.validate()) return;
    final auth = context.read<AuthService>();
    final ok = await auth.signup(
      email: _sEmailCtrl.text.trim(),
      username: _sUsernameCtrl.text.trim(),
      password: _sPassCtrl.text,
      fullName: _sNameCtrl.text.trim().isEmpty ? null : _sNameCtrl.text.trim(),
    );
    if (ok && mounted) {
      Navigator.pushReplacementNamed(context, '/dashboard');
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    const cyan = Color(0xFF00F5FF);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF050A14), Color(0xFF0D1B2A), Color(0xFF050A14)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  // Logo
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: cyan, width: 1.5),
                      boxShadow: [
                        BoxShadow(color: cyan.withOpacity(0.3), blurRadius: 20, spreadRadius: 5),
                      ],
                    ),
                    child: const Icon(Icons.shield_outlined, color: cyan, size: 40),
                  ),
                  const SizedBox(height: 16),
                  const Text('ECHOSHIELD',
                      style: TextStyle(
                          color: cyan, fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 5)),
                  const SizedBox(height: 4),
                  Text('Real-Time AI Scammer Interceptor',
                      style: TextStyle(color: cyan.withOpacity(0.5), fontSize: 12, letterSpacing: 1)),
                  const SizedBox(height: 40),

                  // Tab bar
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF0D1B2A),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF1A2E4A)),
                    ),
                    child: TabBar(
                      controller: _tabs,
                      indicator: BoxDecoration(
                        color: cyan.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: cyan.withOpacity(0.5)),
                      ),
                      labelColor: cyan,
                      unselectedLabelColor: Colors.white38,
                      tabs: const [
                        Tab(text: 'LOGIN'),
                        Tab(text: 'SIGN UP'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Error
                  if (auth.error != null)
                    Container(
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFF0055).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFFF0055).withOpacity(0.5)),
                      ),
                      child: Text(auth.error!,
                          style: const TextStyle(color: Color(0xFFFF0055), fontSize: 13)),
                    ),

                  SizedBox(
                    height: 360,
                    child: TabBarView(
                      controller: _tabs,
                      children: [
                        // LOGIN FORM
                        Form(
                          key: _loginFormKey,
                          child: Column(
                            children: [
                              TextFormField(
                                controller: _emailCtrl,
                                decoration: const InputDecoration(
                                    labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)),
                                keyboardType: TextInputType.emailAddress,
                                validator: (v) => v!.isEmpty ? 'Required' : null,
                              ),
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _passCtrl,
                                obscureText: _obscurePass,
                                decoration: InputDecoration(
                                  labelText: 'Password',
                                  prefixIcon: const Icon(Icons.lock_outline),
                                  suffixIcon: IconButton(
                                    icon: Icon(_obscurePass ? Icons.visibility : Icons.visibility_off),
                                    onPressed: () => setState(() => _obscurePass = !_obscurePass),
                                    color: cyan.withOpacity(0.5),
                                  ),
                                ),
                                validator: (v) => v!.isEmpty ? 'Required' : null,
                              ),
                              const SizedBox(height: 24),
                              SizedBox(
                                width: double.infinity,
                                child: ElevatedButton(
                                  onPressed: auth.loading ? null : _login,
                                  child: auth.loading
                                      ? const SizedBox(
                                          height: 20, width: 20,
                                          child: CircularProgressIndicator(strokeWidth: 2))
                                      : const Text('LOGIN'),
                                ),
                              ),
                            ],
                          ),
                        ),

                        // SIGNUP FORM
                        Form(
                          key: _signupFormKey,
                          child: SingleChildScrollView(
                            child: Column(
                              children: [
                                TextFormField(
                                  controller: _sNameCtrl,
                                  decoration: const InputDecoration(
                                      labelText: 'Full Name (optional)',
                                      prefixIcon: Icon(Icons.person_outline)),
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _sEmailCtrl,
                                  decoration: const InputDecoration(
                                      labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)),
                                  validator: (v) => v!.isEmpty ? 'Required' : null,
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _sUsernameCtrl,
                                  decoration: const InputDecoration(
                                      labelText: 'Username', prefixIcon: Icon(Icons.badge_outlined)),
                                  validator: (v) => v!.isEmpty ? 'Required' : null,
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _sPassCtrl,
                                  obscureText: true,
                                  decoration: const InputDecoration(
                                      labelText: 'Password', prefixIcon: Icon(Icons.lock_outline)),
                                  validator: (v) => v!.length < 6 ? 'Min 6 chars' : null,
                                ),
                                const SizedBox(height: 20),
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                    onPressed: auth.loading ? null : _signup,
                                    child: auth.loading
                                        ? const SizedBox(
                                            height: 20, width: 20,
                                            child: CircularProgressIndicator(strokeWidth: 2))
                                        : const Text('CREATE ACCOUNT'),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
