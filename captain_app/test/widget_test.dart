import 'package:flutter_test/flutter_test.dart';
import 'package:captain_app/main.dart';

void main() {
  testWidgets('DMTE App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const CaptainApp());

    // Verify that our app starts at Home Screen.
    expect(find.text('DMTE Captain App'), findsOneWidget);
    expect(find.text('START DISPATCH'), findsOneWidget);
  });
}
