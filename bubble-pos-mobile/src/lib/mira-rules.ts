/**
 * MIRA Tax Applicability Logic
 * TGST (17%) for tourism, GST (8%) for general retail.
 * Service Charge (10%) applied on subtotal.
 */

export interface TaxBreakdown {
  subtotal_mvr: number;
  service_charge_mvr: number;
  tgst_amount_mvr: number;
  gst_amount_mvr: number;
  total_mvr: number;
}

export const MiraRules = {
  calculate: (items: any[], businessType: string): TaxBreakdown => {
    const rawSubtotal = items.reduce((sum, item) => sum + (item.price * item.qty), 0);
    const serviceCharge = rawSubtotal * 0.10;
    const taxableAmount = rawSubtotal + serviceCharge;

    let tgst = 0;
    let gst = 0;

    if (businessType === 'TOURISM') {
      tgst = taxableAmount * 0.17;
    } else {
      gst = taxableAmount * 0.08;
    }

    return {
      subtotal_mvr: rawSubtotal,
      service_charge_mvr: serviceCharge,
      tgst_amount_mvr: tgst,
      gst_amount_mvr: gst,
      total_mvr: taxableAmount + tgst + gst
    };
  }
};
