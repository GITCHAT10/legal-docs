import React from 'react';
import { View, Text, ScrollView } from 'react-native';
import { MVR } from '../lib/mvr';

export const ReceiptScreen = ({ receipt }) => {
  return (
    <ScrollView style={{ flex: 1, padding: 20, backgroundColor: '#F9F9F9' }}>
      <View style={{ backgroundColor: 'white', padding: 20, borderRadius: 5, shadowColor: '#000', shadowOpacity: 0.1 }}>
        <Text style={{ textAlign: 'center', fontWeight: 'bold' }}>{receipt.business.name}</Text>
        <Text style={{ textAlign: 'center', fontSize: 12 }}>TIN: {receipt.business.tin}</Text>
        <Text style={{ marginVertical: 10 }}>--------------------------------</Text>

        {receipt.line_items.map((item, idx) => (
          <View key={idx} style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text>{item.sku} x{item.qty}</Text>
            <Text>{MVR.format(item.price * item.qty)}</Text>
          </View>
        ))}

        <Text style={{ marginVertical: 10 }}>--------------------------------</Text>
        <Text style={{ textAlign: 'right' }}>Subtotal: {MVR.format(receipt.totals.subtotal_mvr)}</Text>
        <Text style={{ textAlign: 'right' }}>TGST (17%): {MVR.format(receipt.totals.tgst_amount_mvr)}</Text>
        <Text style={{ textAlign: 'right', fontWeight: 'bold', fontSize: 18 }}>TOTAL: {MVR.format(receipt.totals.total_mvr)}</Text>

        <Text style={{ marginTop: 20, fontSize: 10, color: '#666' }}>Invoice: {receipt.invoice_id}</Text>
        <Text style={{ fontSize: 10, color: '#666' }}>Audit: {receipt.shadow_audit_hash}</Text>
      </View>
    </ScrollView>
  );
};
