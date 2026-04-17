import 'dart:convert';
import 'package:http/http.dart' as http;

class TripleKeyEngine {
  static const String edgeNodeUrl = "http://localhost:8001"; // In real RPi, this would be the IP

  Future<Map<String, dynamic>> checkIdentity() async {
    // Mock e-Faas OIDC sandbox
    await Future.delayed(Duration(milliseconds: 500));
    return {"verified": true, "captain_id": "CAP-001"};
  }

  Future<Map<String, dynamic>> checkCompliance(String vesselId) async {
    try {
      final response = await http.get(Uri.parse("$edgeNodeUrl/compliance?vessel_id=$vesselId"));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      // Offline fallback or error
    }
    return {"status": "ERROR", "reason": "Edge Node Unreachable"};
  }

  Future<Map<String, dynamic>> checkEnvironment() async {
    try {
      final response = await http.get(Uri.parse("$edgeNodeUrl/environment"));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      // Offline fallback
    }
    return {"risk": 1, "weather": "Unknown (Offline)"};
  }

  Future<String> authorizeDispatch({
    required Map<String, dynamic> identity,
    required Map<String, dynamic> compliance,
    required Map<String, dynamic> environment,
  }) async {
    if (!identity["verified"]) {
      return "BLOCKED: IDENTITY";
    }

    if (compliance["status"] != "CLEARED") {
      return "BLOCKED: COMPLIANCE";
    }

    if (environment["risk"] > 5) {
      return "BLOCKED: WEATHER";
    }

    return "VERIFIED";
  }
}
