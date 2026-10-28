import 'dart:math';
import 'package:flutter/material.dart';

class ThreatGauge extends StatefulWidget {
  final double score;
  final String threatLevel;

  const ThreatGauge({super.key, required this.score, required this.threatLevel});

  @override
  State<ThreatGauge> createState() => _ThreatGaugeState();
}

class _ThreatGaugeState extends State<ThreatGauge>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _animation;
  double _prevScore = 0;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 800));
    _animation = Tween<double>(begin: 0, end: widget.score).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeOut),
    );
    _ctrl.forward();
  }

  @override
  void didUpdateWidget(ThreatGauge old) {
    super.didUpdateWidget(old);
    if (old.score != widget.score) {
      _animation = Tween<double>(begin: _prevScore, end: widget.score).animate(
        CurvedAnimation(parent: _ctrl, curve: Curves.easeOut),
      );
      _prevScore = widget.score;
      _ctrl.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Color _scoreColor(double s) {
    if (s >= 0.85) return const Color(0xFFFF0055);
    if (s >= 0.60) return const Color(0xFFFF6600);
    if (s >= 0.35) return const Color(0xFFFFAA00);
    return const Color(0xFF00FF88);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1B2A),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF1A2E4A)),
      ),
      child: Column(
        children: [
          AnimatedBuilder(
            animation: _animation,
            builder: (_, __) {
              final s = _animation.value;
              return SizedBox(
                height: 160,
                child: CustomPaint(
                  painter: _GaugePainter(score: s, color: _scoreColor(s)),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text(
                          '${(s * 100).toStringAsFixed(0)}%',
                          style: TextStyle(
                            color: _scoreColor(s),
                            fontSize: 36,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          widget.threatLevel,
                          style: TextStyle(
                            color: _scoreColor(s).withOpacity(0.7),
                            fontSize: 12,
                            letterSpacing: 3,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _indicator('LOW', const Color(0xFF00FF88), widget.score < 0.35),
              _indicator('MEDIUM', const Color(0xFFFFAA00), widget.score >= 0.35 && widget.score < 0.60),
              _indicator('HIGH', const Color(0xFFFF6600), widget.score >= 0.60 && widget.score < 0.85),
              _indicator('CRITICAL', const Color(0xFFFF0055), widget.score >= 0.85),
            ],
          ),
        ],
      ),
    );
  }

  Widget _indicator(String label, Color color, bool active) {
    return Column(
      children: [
        Container(
          width: active ? 12 : 8,
          height: active ? 12 : 8,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: active ? color : color.withOpacity(0.25),
            boxShadow: active
                ? [BoxShadow(color: color.withOpacity(0.6), blurRadius: 8)]
                : null,
          ),
        ),
        const SizedBox(height: 4),
        Text(label,
            style: TextStyle(
                color: active ? color : Colors.white24,
                fontSize: 9,
                letterSpacing: 1,
                fontWeight: active ? FontWeight.bold : FontWeight.normal)),
      ],
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double score;
  final Color color;

  _GaugePainter({required this.score, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.85);
    final radius = min(size.width / 2, size.height) * 0.85;
    const startAngle = pi * 0.75;
    const sweepAngle = pi * 1.5;

    // Track
    final trackPaint = Paint()
      ..color = Colors.white.withOpacity(0.07)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 16
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius),
        startAngle, sweepAngle, false, trackPaint);

    // Fill
    if (score > 0) {
      final fillPaint = Paint()
        ..shader = SweepGradient(
          colors: [color.withOpacity(0.5), color],
          startAngle: startAngle,
          endAngle: startAngle + sweepAngle * score,
        ).createShader(Rect.fromCircle(center: center, radius: radius))
        ..style = PaintingStyle.stroke
        ..strokeWidth = 16
        ..strokeCap = StrokeCap.round;
      canvas.drawArc(
          Rect.fromCircle(center: center, radius: radius),
          startAngle,
          sweepAngle * score,
          false,
          fillPaint);

      // Glow
      final glowPaint = Paint()
        ..color = color.withOpacity(0.2)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 28
        ..strokeCap = StrokeCap.round
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);
      canvas.drawArc(
          Rect.fromCircle(center: center, radius: radius),
          startAngle,
          sweepAngle * score,
          false,
          glowPaint);
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) => old.score != score || old.color != color;
}
