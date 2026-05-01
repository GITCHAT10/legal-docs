import React from 'react';
import { View, Text, FlatList, TouchableOpacity, Alert } from 'react-native';
import { useOfflineCart } from '../hooks/useOfflineCart';
import { PosTransactionService } from '../services/PosTransactionService';
import { MVR } from '../lib/mvr';

export const PosScreen = ({ businessActorId }) => {
  const { cart, addItem, clearCart, syncStatus } = useOfflineCart(businessActorId);

  const handleCheckout = async () => {
    const taxBreakdown = PosTransactionService.calculateTotals(cart.items, {
      businessType: 'TOURISM' // Hardcoded for demo
    });

    try {
      const receipt = await PosTransactionService.createSignedReceipt({
        businessActorId,
        items: cart.items,
        taxBreakdown
      });

      Alert.alert("Success", `Receipt Generated: ${receipt.invoice_id}`);
      clearCart();
    } catch (error) {
      Alert.alert("Error", "Checkout failed");
    }
  };

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold' }}>BUBBLE POS - SALA NODE</Text>
      <Text>Sync Status: {syncStatus}</Text>

      <TouchableOpacity
        onPress={() => addItem({ sku: 'coffee', price: 50, qty: 1, category: 'FOOD' })}
        style={{ backgroundColor: '#007AFF', padding: 10, marginVertical: 10 }}
      >
        <Text style={{ color: 'white' }}>Add Coffee (Rf 50)</Text>
      </TouchableOpacity>

      <Text style={{ marginTop: 20 }}>Cart Total: {MVR.format(cart.subtotal)}</Text>

      <TouchableOpacity
        onPress={handleCheckout}
        disabled={cart.items.length === 0}
        style={{ backgroundColor: '#4CD964', padding: 15, marginTop: 'auto' }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontWeight: 'bold' }}>CHECKOUT</Text>
      </TouchableOpacity>
    </View>
  );
};
