import 'package:flutter/material.dart';

class CallLogTile extends StatelessWidget {
  final Map<String, dynamic> log;

  const CallLogTile({super.key, required this.log});

  Color _levelColor(String level) {
    switch (level) {
      case 'CRITICAL': return const Color(0xFFFF0055);
      case 'HIGH': return const Color(0xFFFF6600);
      case 'MEDIUM': return const Color(0xFFFFAA00);
      default: return const Color(0xFF00FF88);
    }
  }

  IconData _levelIcon(String level) {
    switch (level) {
      case 'CRITICAL': return Icons.dangerous_outlined;
      case 'HIGH': return Icons.warning_amber_rounded;
      case 'MEDIUM': return Icons.info_outline;
      default: return Icons.check_circle_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final level = log['threat_level'] ?? 'LOW';
    final c = _levelColor(level);
    final score = ((log['overall_threat_score'] ?? 0.0) * 100).toStringAsFixed(0);
    final transcript = log['transcript'] ?? 'No transcript';
    final caller = log['caller_number'] ?? 'Unknown';
    final time = log['call_start'] != null
        ? DateTime.tryParse(log['call_start'].toString())
        : null;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _showCallDetails(context, log),
        borderRadius: BorderRadius.circular(14),
        child: Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF0D1B2A),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: c.withOpacity(0.25)),
          ),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: c.withOpacity(0.12),
                  shape: BoxShape.circle,
                ),
                child: Icon(_levelIcon(level), color: c, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: c.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(level,
                            style: TextStyle(color: c, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
                      ),
                      const SizedBox(width: 8),
                      Text('$score%', style: TextStyle(color: c.withOpacity(0.7), fontSize: 11)),
                      const Spacer(),
                      if (time != null)
                        Text(
                          '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}',
                          style: const TextStyle(color: Colors.white24, fontSize: 11),
                        ),
                    ]),
                    const SizedBox(height: 6),
                    Text(
                      transcript,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: Colors.white54, fontSize: 12),
                    ),
                    const SizedBox(height: 4),
                    Row(children: [
                      const Icon(Icons.phone_outlined, size: 11, color: Colors.white24),
                      const SizedBox(width: 4),
                      Text(caller, style: const TextStyle(color: Colors.white24, fontSize: 11)),
                      if (log['is_deepfake'] == true) ...[
                        const SizedBox(width: 8),
                        const Text('🤖 Deepfake',
                            style: TextStyle(color: Color(0xFFFF6600), fontSize: 11)),
                      ],
                      const Spacer(),
                      const Icon(Icons.chevron_right, size: 16, color: Colors.white24),
                    ]),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showCallDetails(BuildContext context, Map<String, dynamic> log) {
    final level = log['threat_level'] ?? 'LOW';
    final c = _levelColor(level);
    final score = ((log['overall_threat_score'] ?? 0.0) * 100).toStringAsFixed(0);
    final transcript = log['transcript'] ?? 'No transcript recorded.';
    final caller = log['caller_number'] ?? 'Unknown Caller';
    final strategy = log['negotiator_strategy'] ?? 'No specific negotiator strategy needed.';
    final isDeepfake = log['is_deepfake'] == true;
    final isUrgency = log['urgency_detected'] == true;
    final time = log['call_start'] != null
        ? DateTime.tryParse(log['call_start'].toString())
        : null;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0D1B2A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (_, scrollController) => ListView(
          controller: scrollController,
          padding: const EdgeInsets.all(20),
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: c.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: c.withOpacity(0.4)),
                  ),
                  child: Text(
                    level,
                    style: TextStyle(color: c, fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  'Threat Score: $score%',
                  style: TextStyle(color: c, fontWeight: FontWeight.w600, fontSize: 14),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.white54),
                  onPressed: () => Navigator.pop(ctx),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              caller,
              style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
            ),
            if (time != null)
              Text(
                '${time.toLocal()}'.split('.')[0],
                style: const TextStyle(color: Colors.white38, fontSize: 12),
              ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (isDeepfake)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFF6600).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: const Color(0xFFFF6600).withOpacity(0.3)),
                    ),
                    child: const Text('🤖 Deepfake Voice Detected',
                        style: TextStyle(color: Color(0xFFFF6600), fontSize: 12)),
                  ),
                if (isUrgency)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFF0055).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: const Color(0xFFFF0055).withOpacity(0.3)),
                    ),
                    child: const Text('🚨 Urgency Manipulation',
                        style: TextStyle(color: Color(0xFFFF0055), fontSize: 12)),
                  ),
                if (!isDeepfake && !isUrgency)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00FF88).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: const Color(0xFF00FF88).withOpacity(0.3)),
                    ),
                    child: const Text('✅ No Threat Signals Detected',
                        style: TextStyle(color: Color(0xFF00FF88), fontSize: 12)),
                  ),
              ],
            ),
            const SizedBox(height: 20),
            const Text(
              'CALL TRANSCRIPT',
              style: TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF050A14),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white10),
              ),
              child: Text(
                transcript,
                style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.5),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              '🤖 AI NEGOTIATOR STRATEGY',
              style: TextStyle(color: Color(0xFF00F5FF), fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF00F5FF).withOpacity(0.06),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF00F5FF).withOpacity(0.2)),
              ),
              child: Text(
                strategy,
                style: const TextStyle(color: Color(0xFF00F5FF), fontSize: 13, height: 1.5),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const StatCard({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 12),
          Text(value,
              style: TextStyle(
                  color: color, fontSize: 26, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(label,
              style: const TextStyle(color: Colors.white38, fontSize: 11)),
        ],
      ),
    );
  }
}
