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

    return Container(
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
                ]),
              ],
            ),
          ),
        ],
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
