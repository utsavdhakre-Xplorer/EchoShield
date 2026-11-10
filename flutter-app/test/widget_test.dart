import 'package:flutter_test/flutter_test.dart';
import 'package:echoshield/services/auth_service.dart';

void main() {
  test('AuthUser normalizes numeric identifiers to strings', () {
    final user = AuthUser.fromJson({
      'id': 42,
      'email': 'muskan@example.com',
      'username': 'muskan',
      'full_name': 'Muskan',
    });

    expect(user.id, '42');
    expect(user.email, 'muskan@example.com');
    expect(user.username, 'muskan');
    expect(user.fullName, 'Muskan');
  });
}
