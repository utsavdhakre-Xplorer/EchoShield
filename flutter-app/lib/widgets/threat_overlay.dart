import 'package:flutter/material.dart';

/// Floating threat overlay widget — shown like a Truecaller banner
/// when a scam call is detected during an active call.
class ThreatOverlay extends StatefulWidget {
  final double threatScore;       // 0.0 – 1.0
  final String threatLevel;       // LOW / MEDIUM / HIGH / CRITICAL
  final String transcript;
  final List<String> phrases;
  final VoidCallback? onDismiss;

  const ThreatOverlay({
    super.key,
    required this.threatScore,
    required this.threatLevel,
    required this.transcript,
    this.phrases = const [],
    this.onDismiss,
  });

  @override
  State<ThreatOverlay> createState() => _ThreatOverlayState();
}

class _ThreatOverlayState extends State<ThreatOverlay>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _slideAnim;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 450),
    );
    _slideAnim = Tween<Offset>(begin: const Offset(0, -1), end: Offset.zero)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutBack));
    _fadeAnim = Tween<double>(begin: 0.0, end: 1.0)
        .animate(CurvedAnimation(parent: _controller, curve: Curves.easeIn));
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color get _levelColor {
    switch (widget.threatLevel.toUpperCase()) {
      case 'CRITICAL': return const Color(0xFFD32F2F);
      case 'HIGH':     return const Color(0xFFF57C00);
      case 'MEDIUM':   return const Color(0xFFFBC02D);
      default:         return const Color(0xFF388E3C);
    }
  }

  IconData get _levelIcon {
    switch (widget.threatLevel.toUpperCase()) {
      case 'CRITICAL': return Icons.gpp_bad_rounded;
      case 'HIGH':     return Icons.warning_amber_rounded;
      case 'MEDIUM':   return Icons.info_outline_rounded;
      default:         return Icons.verified_user_rounded;
    }
  }

  String get _levelLabel {
    switch (widget.threatLevel.toUpperCase()) {
      case 'CRITICAL': return '⚠️ SCAM CALL DETECTED';
      case 'HIGH':     return '🚨 HIGH RISK CALL';
      case 'MEDIUM':   return '⚡ Suspicious Activity';
      default:         return '✅ Call Appears Safe';
    }
  }

  @override
  Widget build(BuildContext context) {
    final percent = (widget.threatScore * 100).round();

    return SlideTransition(
      position: _slideAnim,
      child: FadeTransition(
        opacity: _fadeAnim,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Material(
            elevation: 12,
            borderRadius: BorderRadius.circular(20),
            color: Colors.transparent,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    _levelColor.withOpacity(0.95),
                    _levelColor.withOpacity(0.75),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: _levelColor.withOpacity(0.45),
                    blurRadius: 20,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // ── Header row ───────────────────────────────────────────
                  Row(
                    children: [
                      Icon(_levelIcon, color: Colors.white, size: 28),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _levelLabel,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                            letterSpacing: 0.3,
                          ),
                        ),
                      ),
                      // Circular risk percentage
                      SizedBox(
                        width: 52,
                        height: 52,
                        child: Stack(
                          fit: StackFit.expand,
                          children: [
                            CircularProgressIndicator(
                              value: widget.threatScore,
                              backgroundColor: Colors.white24,
                              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                              strokeWidth: 5,
                            ),
                            Center(
                              child: Text(
                                '$percent%',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),

                  // ── Detected phrases ─────────────────────────────────────
                  if (widget.phrases.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: widget.phrases.take(4).map((p) => Chip(
                          label: Text(p,
                            style: TextStyle(
                              color: _levelColor,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          backgroundColor: Colors.white,
                          padding: EdgeInsets.zero,
                          visualDensity: VisualDensity.compact,
                        )).toList(),
                      ),
                    ),
                  ],

                  // ── Transcript snippet ───────────────────────────────────
                  if (widget.transcript.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.black26,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '"${widget.transcript.length > 120 ? '${widget.transcript.substring(0, 120)}…' : widget.transcript}"',
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  ],

                  // ── Dismiss button ───────────────────────────────────────
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: widget.onDismiss,
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.white,
                        backgroundColor: Colors.white24,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(20),
                        ),
                      ),
                      child: const Text('Dismiss',
                        style: TextStyle(fontWeight: FontWeight.bold)),
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
