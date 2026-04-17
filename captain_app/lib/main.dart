import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'services/triple_key_engine.dart';
import 'database/database_helper.dart';
import 'package:intl/intl.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const CaptainApp());
}

class CaptainApp extends StatelessWidget {
  const CaptainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DMTE Captain App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String selectedVessel = "123";
  final List<String> vessels = ["123", "456", "789"];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("DMTE Captain App")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text("Select Vessel:", style: TextStyle(fontSize: 18)),
            DropdownButton<String>(
              value: selectedVessel,
              items: vessels.map((v) => DropdownMenuItem(value: v, child: Text("Vessel $v"))).toList(),
              onChanged: (val) => setState(() => selectedVessel = val!),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => VerificationScreen(vesselId: selectedVessel)),
              ),
              child: const Text("START DISPATCH"),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _syncLogs,
              child: const Text("Sync Logs to Sovereign"),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _syncLogs() async {
    final db = DatabaseHelper();
    final logs = await db.getUnsyncedLogs();
    if (logs.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("No logs to sync")));
      return;
    }

    try {
      final response = await http.post(
        Uri.parse("http://localhost:8002/sync-logs"),
        headers: {"Content-Type": "application/json"},
        body: json.encode(logs),
      );

      if (response.statusCode == 200) {
        for (var log in logs) {
          await db.markAsSynced(log['id']);
        }
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Sync Successful")));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Sync Failed: Backend Offline")));
    }
  }
}

class VerificationScreen extends StatefulWidget {
  final String vesselId;
  const VerificationScreen({super.key, required this.vesselId});

  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  final engine = TripleKeyEngine();
  Map<String, dynamic>? identity;
  Map<String, dynamic>? compliance;
  Map<String, dynamic>? environment;
  String? result;

  @override
  void initState() {
    super.initState();
    _runChecks();
  }

  Future<void> _runChecks() async {
    final idRes = await engine.checkIdentity();
    setState(() => identity = idRes);

    final compRes = await engine.checkCompliance(widget.vesselId);
    setState(() => compliance = compRes);

    final envRes = await engine.checkEnvironment();
    setState(() => environment = envRes);

    final authRes = await engine.authorizeDispatch(
      identity: idRes,
      compliance: compRes,
      environment: envRes,
    );

    setState(() => result = authRes);

    // Write to local ledger
    final db = DatabaseHelper();
    final dispatchId = const Uuid().v4();
    await db.insertLog({
      "id": dispatchId,
      "vessel_id": widget.vesselId,
      "captain_id": idRes["captain_id"],
      "status": authRes,
      "timestamp": DateFormat('yyyy-MM-dd HH:mm:ss').format(DateTime.now()),
      "synced": 0,
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Verification")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildStatusRow("Identity", identity),
            _buildStatusRow("Compliance", compliance),
            _buildStatusRow("Weather", environment),
            const Spacer(),
            if (result != null)
              Center(
                child: ElevatedButton(
                  onPressed: () => Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => ResultScreen(status: result!)),
                  ),
                  child: const Text("VIEW RESULT"),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusRow(String label, dynamic data) {
    IconData icon = Icons.hourglass_empty;
    Color color = Colors.orange;

    if (data != null) {
      bool success = false;
      if (label == "Identity") success = data["verified"] == true;
      if (label == "Compliance") success = data["status"] == "CLEARED";
      if (label == "Weather") success = data["risk"] != null && data["risk"] <= 5;

      icon = success ? Icons.check_circle : Icons.cancel;
      color = success ? Colors.green : Colors.red;
    }

    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(label),
      trailing: data == null ? const CircularProgressIndicator() : null,
    );
  }
}

class ResultScreen extends StatelessWidget {
  final String status;
  const ResultScreen({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final isSuccess = status == "VERIFIED";
    return Scaffold(
      backgroundColor: isSuccess ? Colors.green : Colors.red,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              isSuccess ? "DISPATCH AUTHORIZED" : "DISPATCH BLOCKED",
              style: const TextStyle(fontSize: 24, color: Colors.white, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            if (isSuccess)
              Container(
                color: Colors.white,
                padding: const EdgeInsets.all(16),
                child: const Icon(Icons.qr_code, size: 200),
              )
            else
              Text(
                "Reason: $status",
                style: const TextStyle(fontSize: 18, color: Colors.white),
              ),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
              child: const Text("RETURN HOME"),
            ),
          ],
        ),
      ),
    );
  }
}
