import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/call_monitor_service.dart';
import '../services/api_service.dart';
import '../widgets/threat_gauge.dart';
import '../widgets/threat_alert_overlay.dart';
import '../widgets/call_log_tile.dart' hide StatCard;
import '../widgets/stat_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _navIndex = 0;
  Map<String, dynamic>? _stats;
  List<dynamic> _logs = [];
  bool _loadingData = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _initialize());
  }

  Future<void> _initialize() async {
    final auth = context.read<AuthService>();
    final monitor = context.read<CallMonitorService>();
    monitor.setToken(auth.token);
    await _loadData();
  }

  Future<void> _loadData() async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;
    setState(() => _loadingData = true);
    final api = ApiService(token: auth.token!);
    final stats = await api.getStats();
    final logs = await api.getCallLogs(limit: 30);
    setState(() {
      _stats = stats;
      _logs = logs;
      _loadingData = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final monitor = context.watch<CallMonitorService>();
    const cyan = Color(0xFF00F5FF);
    const green = Color(0xFF00FF88);
    const red = Color(0xFFFF0055);

    return Scaffold(
      backgroundColor: const Color(0xFF050A14),
      body: Stack(
        children: [
          SafeArea(
            child: Column(
              children: [
                // Top bar
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      const Icon(Icons.shield_outlined, color: cyan, size: 24),
                      const SizedBox(width: 10),
                      const Text('ECHOSHIELD',
                          style: TextStyle(
                              color: cyan, fontWeight: FontWeight.bold,
                              fontSize: 16, letterSpacing: 3)),
                      const Spacer(),
                      // Monitoring toggle
                      GestureDetector(
                        onTap: () {
                          if (monitor.isMonitoring) {
                            monitor.stopMonitoring();
                          } else {
                            monitor.startMonitoring();
                          }
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: monitor.isMonitoring
                                ? green.withOpacity(0.15)
                                : Colors.white10,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                                color: monitor.isMonitoring ? green : Colors.white24),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 8, height: 8,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: monitor.isMonitoring ? green : Colors.white38,
                                  boxShadow: monitor.isMonitoring
                                      ? [BoxShadow(color: green.withOpacity(0.6), blurRadius: 6)]
                                      : null,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                monitor.isMonitoring ? 'ACTIVE' : 'OFF',
                                style: TextStyle(
                                    color: monitor.isMonitoring ? green : Colors.white38,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: 1),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      PopupMenuButton<dynamic>(
                        icon: const Icon(Icons.person_outline, color: Colors.white54),
                        color: const Color(0xFF0D1B2A),
                        itemBuilder: (context) => <PopupMenuEntry<dynamic>>[
                          PopupMenuItem(
                            child: Text(
                              auth.user?.username ?? 'User',
                              style: const TextStyle(color: Colors.white70),
                            ),
                          ),
                          const PopupMenuDivider(),
                          PopupMenuItem(
                            onTap: () {
                              auth.logout().then((_) {
                                Navigator.pushReplacementNamed(context, '/login');
                              });
                            },
                            child: const Text(
                              'Logout',
                              style: TextStyle(color: Color(0xFFFF0055)),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // Nav tabs
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Row(
                    children: [
                      _navTab('Dashboard', 0),
                      _navTab('History', 1),
                      _navTab('Analyzer', 2),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Divider(color: Colors.white.withOpacity(0.06), height: 1),

                Expanded(
                  child: RefreshIndicator(
                    onRefresh: _loadData,
                    color: cyan,
                    child: IndexedStack(
                      index: _navIndex,
                      children: [
                        _buildDashboard(monitor, _stats),
                        _buildHistory(_logs),
                        _buildAnalyzer(auth, monitor),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Threat overlay
          if (monitor.latestThreat != null &&
              monitor.latestThreat!.alertRequired)
            ThreatAlertOverlay(
              result: monitor.latestThreat!,
              onDismiss: () => monitor.simulateScamCall(),
            ),
        ],
      ),
    );
  }

  Widget _navTab(String label, int index) {
    const cyan = Color(0xFF00F5FF);
    final selected = _navIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _navIndex = index),
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? cyan.withOpacity(0.12) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
              color: selected ? cyan.withOpacity(0.4) : Colors.transparent),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? cyan : Colors.white38,
            fontSize: 12,
            fontWeight: selected ? FontWeight.bold : FontWeight.normal,
            letterSpacing: 1,
          ),
        ),
      ),
    );
  }

  Widget _buildDashboard(CallMonitorService monitor, Map<String, dynamic>? stats) {
    const cyan = Color(0xFF00F5FF);
    final threat = monitor.latestThreat;
    final score = threat?.overallThreatScore ?? 0.0;

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        // Threat gauge
        ThreatGauge(score: score, threatLevel: threat?.threatLevel.name.toUpperCase() ?? 'IDLE'),
        const SizedBox(height: 20),

        // Stats row
        if (stats != null) ...[
          Row(children: [
            Expanded(child: StatCard(
              label: 'Total Calls',
              value: '${stats['total_calls_analyzed'] ?? 0}',
              icon: Icons.phone_outlined,
              color: cyan,
            )),
            const SizedBox(width: 12),
            Expanded(child: StatCard(
              label: 'Scams Blocked',
              value: '${stats['scam_calls_detected'] ?? 0}',
              icon: Icons.block_outlined,
              color: const Color(0xFFFF0055),
            )),
          ]),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: StatCard(
              label: 'Deepfakes',
              value: '${stats['deepfake_calls_detected'] ?? 0}',
              icon: Icons.face_retouching_off_outlined,
              color: const Color(0xFFFFAA00),
            )),
            const SizedBox(width: 12),
            Expanded(child: StatCard(
              label: 'Avg Threat',
              value: '${((stats['average_threat_score'] ?? 0.0) * 100).toStringAsFixed(0)}%',
              icon: Icons.analytics_outlined,
              color: const Color(0xFF00FF88),
            )),
          ]),
          const SizedBox(height: 20),
        ],

        // Simulate button
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: monitor.isMonitoring
                ? () => monitor.simulateScamCall()
                : null,
            icon: const Icon(Icons.play_arrow_outlined),
            label: const Text('SIMULATE SCAM CALL'),
            style: OutlinedButton.styleFrom(
              foregroundColor: cyan,
              side: BorderSide(color: cyan.withOpacity(0.4)),
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Latest threat
        if (threat != null) ...[
          Text('LATEST ANALYSIS',
              style: TextStyle(
                  color: Colors.white.withOpacity(0.3),
                  fontSize: 11,
                  letterSpacing: 2)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF0D1B2A),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF1A2E4A)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(threat.transcript,
                    style: const TextStyle(color: Colors.white70, fontSize: 13),
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis),
                const SizedBox(height: 12),
                if (threat.urgencyPhrasesFound.isNotEmpty) ...[
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: threat.urgencyPhrasesFound
                        .map((p) => Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFFFF0055).withOpacity(0.15),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: const Color(0xFFFF0055).withOpacity(0.3)),
                              ),
                              child: Text(p,
                                  style: const TextStyle(
                                      color: Color(0xFFFF0055), fontSize: 11)),
                            ))
                        .toList(),
                  ),
                  const SizedBox(height: 12),
                ],
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: cyan.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: cyan.withOpacity(0.2)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.smart_toy_outlined, color: cyan, size: 16),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          threat.negotiatorStrategy,
                          style: TextStyle(color: cyan.withOpacity(0.85), fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildHistory(List<dynamic> logs) {
    if (_loadingData) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00F5FF)));
    }
    if (logs.isEmpty) {
      return const Center(
        child: Text('No call history yet.\nStart monitoring to detect scam calls.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white38, height: 1.6)),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: logs.length,
      itemBuilder: (_, i) => CallLogTile(log: logs[i]),
    );
  }

  Widget _buildAnalyzer(AuthService auth, CallMonitorService monitor) {
    return const _TextAnalyzerTab();
  }
}

class _TextAnalyzerTab extends StatefulWidget {
  const _TextAnalyzerTab();

  @override
  State<_TextAnalyzerTab> createState() => _TextAnalyzerTabState();
}

class _TextAnalyzerTabState extends State<_TextAnalyzerTab> {
  final _ctrl = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;

  Future<void> _analyze() async {
    if (_ctrl.text.trim().isEmpty) return;
    final auth = context.read<AuthService>();
    if (auth.token == null) return;
    setState(() => _loading = true);
    final api = ApiService(token: auth.token!);
    final r = await api.analyzeText(_ctrl.text.trim());
    setState(() {
      _result = r;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    const cyan = Color(0xFF00F5FF);
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('TEXT ANALYZER',
            style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 11, letterSpacing: 2)),
        const SizedBox(height: 12),
        TextField(
          controller: _ctrl,
          maxLines: 5,
          decoration: const InputDecoration(
            hintText: 'Paste suspicious call transcript here...',
            hintStyle: TextStyle(color: Colors.white24),
            alignLabelWithHint: true,
          ),
          style: const TextStyle(color: Colors.white, fontSize: 14),
        ),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: _loading ? null : _analyze,
          icon: const Icon(Icons.search_outlined),
          label: _loading
              ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
              : const Text('ANALYZE'),
        ),
        if (_result != null) ...[
          const SizedBox(height: 24),
          _buildResultCard(_result!),
        ],
      ],
    );
  }

  Widget _buildResultCard(Map<String, dynamic> r) {
    const cyan = Color(0xFF00F5FF);
    final level = r['threat_level'] ?? 'LOW';
    final score = ((r['overall_threat_score'] ?? 0.0) * 100).toStringAsFixed(0);
    final colors = {
      'CRITICAL': const Color(0xFFFF0055),
      'HIGH': const Color(0xFFFF6600),
      'MEDIUM': const Color(0xFFFFAA00),
      'LOW': const Color(0xFF00FF88),
    };
    final c = colors[level] ?? Colors.white38;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: c.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: c.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(level,
                  style: TextStyle(color: c, fontWeight: FontWeight.bold, letterSpacing: 2)),
            ),
            const SizedBox(width: 12),
            Text('$score% threat',
                style: const TextStyle(color: Colors.white54, fontSize: 13)),
          ]),
          const SizedBox(height: 16),
          if (r['negotiator_strategy'] != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: cyan.withOpacity(0.05),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: cyan.withOpacity(0.2)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.smart_toy_outlined, color: cyan, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      r['negotiator_strategy'],
                      style: TextStyle(color: cyan.withOpacity(0.85), fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
