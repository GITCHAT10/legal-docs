import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class DemandEntryScreen extends StatefulWidget {
  const DemandEntryScreen({super.key});

  @override
  State<DemandEntryScreen> createState() => _DemandEntryScreenState();
}

class _DemandEntryScreenState extends State<DemandEntryScreen> {
  final _itemController = TextEditingController();
  final _amountController = TextEditingController();
  String _priority = 'NORMAL';
  bool _isSubmitting = false;

  Future<void> _submitDemand() async {
    setState(() => _isSubmitting = true);

    final payload = {
      'event_type': 'DEMAND_CREATED',
      'aggregate_id': 'DEMAND-${const Uuid().v4().substring(0, 8)}',
      'aggregate_type': 'Demand',
      'payload': {
        'item': _itemController.text,
        'amount': double.tryParse(_amountController.text) ?? 0,
        'priority': _priority,
      },
      'occurred_at': DateTime.now().toIso8601String(),
      'idempotency_key': const Uuid().v4(),
      'source_system': 'BUBBLE',
      'signature': 'bubble_v1_sign',
    };

    try {
      final response = await http.post(
        Uri.parse('http://localhost:8000/api/v1/events'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (mounted) {
        if (response.statusCode == 201) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Demand Sent to ELEONE')),
          );
          _itemController.clear();
          _amountController.clear();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: ${response.body}')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Connection Failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BUBBLE | Demand Entry'),
        centerTitle: true,
        backgroundColor: Colors.blue[900],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Capture New Demand',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            TextField(
              controller: _itemController,
              decoration: const InputDecoration(
                labelText: 'Demand Item (e.g. Kitchen Supplies)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _amountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Estimated Amount (USD)',
                border: OutlineInputBorder(),
                prefixText: '\$ ',
              ),
            ),
            const SizedBox(height: 16),
            const Text('Priority Level'),
            Row(
              children: ['NORMAL', 'URGENT', 'CRITICAL'].map((p) => Expanded(
                child: RadioListTile<String>(
                  title: Text(p, style: const TextStyle(fontSize: 10)),
                  value: p,
                  groupValue: _priority,
                  onChanged: (v) => setState(() => _priority = v!),
                ),
              )).toList(),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submitDemand,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(20),
                backgroundColor: Colors.blue[700],
                foregroundColor: Colors.white,
              ),
              child: _isSubmitting
                ? const CircularProgressIndicator(color: Colors.white)
                : const Text('DISPATCH TO ELEONE', style: TextStyle(fontWeight: FontWeight.black)),
            ),
          ],
        ),
      ),
    );
  }
}
