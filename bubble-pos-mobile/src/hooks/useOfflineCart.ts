import { useState, useEffect } from 'react';

export const useOfflineCart = (businessActorId: string) => {
  const [cart, setCart] = useState<any>({ items: [], subtotal: 0, requiresPiiConsent: false });
  const [syncStatus, setSyncStatus] = useState<'synced' | 'pending' | 'conflict'>('synced');

  // Simulated WatermelonDB observable
  const addItem = async (item: any) => {
    const updatedItems = [...cart.items, item];
    setCart({
      ...cart,
      items: updatedItems,
      subtotal: updatedItems.reduce((sum, i) => sum + (i.price * i.qty), 0),
      requiresPiiConsent: updatedItems.some(i => i.requiresConsent)
    });
    setSyncStatus('pending');
  };

  const clearCart = () => {
    setCart({ items: [], subtotal: 0, requiresPiiConsent: false });
    setSyncStatus('synced');
  };

  return { cart, addItem, clearCart, syncStatus };
};
