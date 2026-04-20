import 'package:flutter/material.dart';
import 'screens/demand_entry_screen.dart';

void main() {
  runApp(const BubbleApp());
}

class BubbleApp extends StatelessWidget {
  const BubbleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BUBBLE Demand',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const DemandEntryScreen(),
    );
  }
}
