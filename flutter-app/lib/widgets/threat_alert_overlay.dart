import 'package:flutter/material.dart';
import '../services/call_monitor_service.dart';

class ThreatAlertOverlay extends StatefulWidget {
  final ThreatResult result;
  final VoidCallback onDismiss;

  const ThreatAlertOverlay({
    super.key,
    required this.result,
    required this.onDismiss,
  });

  @override
  State<ThreatAlertOverlay> createState() => _ThreatAlertOverlayState();
}

class _ThreatAlertOverlayState extends State<ThreatAlertOverlay>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _pulse;
  bool _expanded = false;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000));
    _pulse = Tween<double>(begin: 1.0, end: 1.04).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
    _ctrl.repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Color get _levelColor {
    switch (widget.result.threatLevel) {
      case ThreatLevel.critical:
        return const Color(0xFFFF0055);
      case ThreatLevel.high:
        return const Color(0xFFFF6600);
      default:
        return const Color(0xFFFFAA00);
    }
  }

  String get _levelLabel {
    switch (widget.result.threatLevel) {
      case ThreatLevel.critical:
        return '⚠ CRITICAL THREAT';
      case ThreatLevel.high:
        return '⚠ HIGH THREAT';
      default:
        return '⚠ THREAT DETECTED';
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = _levelColor;
    return Positioned(
      bottom: 0,
      left: 0,
      right: 0,
      child: ScaleTransition(
        scale: _pulse,
        child: Container(
          margin: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF0D1020),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: c, width: 1.5),
            boxShadow: [
              BoxShadow(color: c.withValues(alpha: 0.4), blurRadius: 20, spreadRadius: 2),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Header
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, color: c, size: 28),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_levelLabel,
                              style: TextStyle(
                                  color: c, fontWeight: FontWeight.bold, fontSize: 15, letterSpacing: 1)),
                          Text(
                            '${(widget.result.overallThreatScore * 100).toStringAsFixed(0)}% threat score',
                            style: TextStyle(color: c.withValues(alpha: 0.7), fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    GestureDetector(
                      onTap: () => setState(() => _expanded = !_expanded),
                      child: Icon(
                        _expanded ? Icons.keyboard_arrow_down : Icons.keyboard_arrow_up,
                        color: Colors.white38,
                      ),
                    ),
                  ],
                ),
              ),

              // Expandable detail
              if (_expanded) ...[
                Divider(color: c.withValues(alpha: 0.2), height: 1),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (widget.result.isDeepfake)
                        _badge('🤖 DEEPFAKE VOICE DETECTED', const Color(0xFFFF6600)),
                      if (widget.result.urgencyDetected)
                        _badge('🚨 SCAM TACTICS DETECTED', const Color(0xFFFF0055)),
                      const SizedBox(height: 12),
                      Text('EVIDENCE & SAFE NEXT STEPS',
                          style: TextStyle(
                              color: const Color(0xFF00F5FF).withValues(alpha: 0.7),
                              fontSize: 10,
                              letterSpacing: 1.5)),
                      const SizedBox(height: 8),
                      Text(
                        widget.result.transcript.isEmpty
                            ? 'Transcript evidence is unavailable for this result.'
                            : 'Transcript evidence: "${widget.result.transcript}"',
                        style: const TextStyle(color: Colors.white70, fontSize: 12, height: 1.45),
                      ),
                      if (widget.result.urgencyPhrasesFound.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        const Text('Signals flagged:', style: TextStyle(color: Colors.white60, fontSize: 11)),
                        const SizedBox(height: 4),
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: widget.result.urgencyPhrasesFound.map((phrase) => Chip(
                            label: Text(phrase, style: const TextStyle(fontSize: 10)),
                            backgroundColor: const Color(0xFFFF0055).withValues(alpha: 0.12),
                            side: const BorderSide(color: Color(0x66FF0055)),
                          )).toList(),
                        ),
                      ],
                      const SizedBox(height: 12),
                      const Text(
                        '• Do not transfer money or share OTPs, PINs, passwords, or remote-access codes.\n'
                        '• End the call if you feel pressured.\n'
                        '• Verify the claim with the organization using a contact you find independently.\n'
                        '• This score is an AI estimate, not proof; legitimate callers can be flagged and scams can be missed. EchoShield does not autonomously engage or block the caller.',
                        style: TextStyle(color: Colors.white70, fontSize: 12, height: 1.5),
                      ),
                    ],
                  ),
                ),
              ],

              // Dismiss
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: SizedBox(
                  width: double.infinity,
                  child: TextButton(
                    onPressed: widget.onDismiss,
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.white38,
                      backgroundColor: Colors.white.withValues(alpha: 0.05),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    child: const Text('DISMISS', style: TextStyle(letterSpacing: 2, fontSize: 12)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _badge(String text, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(text, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }
}
