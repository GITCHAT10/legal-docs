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
  List<Map<String, dynamic>> _activeDemands = [];

  Future<void> _submitDemand() async {
    if (_itemController.text.isEmpty) return;
    setState(() => _isSubmitting = true);

    final demandId = 'DEMAND-${const Uuid().v4().substring(0, 8)}';
    final payload = {
      'event_type': 'DEMAND_CREATED',
      'aggregate_id': demandId,
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
          setState(() {
            _activeDemands.insert(0, {
              'id': demandId,
              'item': _itemController.text,
              'status': 'PROCESSING',
              'time': 'Just now'
            });
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Demand Sent to ELEONE'), backgroundColor: Colors.green),
          );
          _itemController.clear();
          _amountController.clear();
        } else {
          _showError('Server Error: ${response.statusCode}');
        }
      }
    } catch (e) {
      _showError('Connection Failed. Is AEGIS Backend Running?');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BUBBLE | Demand Layer', style: TextStyle(fontWeight: FontWeight.black, letterSpacing: -1)),
        centerTitle: true,
        backgroundColor: Colors.blue[900],
        actions: [
          IconButton(icon: const Icon(Icons.history), onPressed: () {})
        ],
      ),
      body: Column(
        children: [
          // Demand Form
          Padding(
            padding: const EdgeInsets.all(20.0),
            child: Card(
              color: Colors.slate[900],
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text('CREATE DEMAND', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blue)),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _itemController,
                      decoration: const InputDecoration(labelText: 'Item Name', border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _amountController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Budget (USD)', prefixText: '\$ ', border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 12),
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'NORMAL', label: Text('Normal')),
                        ButtonSegment(value: 'URGENT', label: Text('Urgent')),
                        ButtonSegment(value: 'CRITICAL', label: Text('Critical')),
                      ],
                      selected: {_priority},
                      onSelectionChanged: (v) => setState(() => _priority = v.first),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: _isSubmitting ? null : _submitDemand,
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blue[700], padding: const EdgeInsets.all(16)),
                      child: _isSubmitting ? const CircularProgressIndicator() : const Text('DISPATCH TO ECOSYSTEM'),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Tracking List
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
            child: Row(
              children: [
                Icon(Icons.radar, size: 16, color: Colors.green),
                SizedBox(width: 8),
                Text('ACTIVE TRACKING', style: TextStyle(fontSize: 10, fontWeight: FontWeight.black, letterSpacing: 2)),
              ],
            ),
          ),

          Expanded(
            child: _activeDemands.isEmpty
              ? Center(child: Text('No active demands', style: TextStyle(color: Colors.slate[700], fontSize: 12)))
              : ListView.builder(
                  itemCount: _activeDemands.length,
                  itemBuilder: (context, index) {
                    final d = _activeDemands[index];
                    return ListTile(
                      leading: const CircleAvatar(backgroundColor: Colors.blue, child: Icon(Icons.package, size: 16)),
                      title: Text(d['item'], style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text(d['id'], style: const TextStyle(fontSize: 10, fontFeatures: [FontFeature.tabularFigures()])),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.blue.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                        child: Text(d['status'], style: const TextStyle(color: Colors.blue, fontSize: 10, fontWeight: FontWeight.bold)),
                      ),
                    );
                  },
                ),
          ),
        ],
      ),
    );
  }
}
