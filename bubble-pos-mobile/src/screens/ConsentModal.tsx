import React from 'react';
import { Modal, View, Text, TouchableOpacity, Switch } from 'react-native';

export const ConsentModal = ({ visible, onClose, onConsentGranted }) => {
  const [consentGiven, setConsentGiven] = React.useState(false);

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 }}>
        <View style={{ backgroundColor: 'white', padding: 20, borderRadius: 10 }}>
          <Text style={{ fontSize: 20, fontWeight: 'bold' }}>Data Consent Required</Text>
          <Text style={{ marginVertical: 15 }}>
            To process your order and generate MIRA-compliant records, we need your consent to store phone and purchase history.
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <Text>I consent to the above</Text>
            <Switch value={consentGiven} onValueChange={setConsentGiven} />
          </View>
          <TouchableOpacity
            onPress={() => onConsentGranted("TOKEN_123")}
            disabled={!consentGiven}
            style={{ backgroundColor: consentGiven ? '#007AFF' : '#CCC', padding: 10, marginTop: 20 }}
          >
            <Text style={{ color: 'white', textAlign: 'center' }}>Grant Consent</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};
