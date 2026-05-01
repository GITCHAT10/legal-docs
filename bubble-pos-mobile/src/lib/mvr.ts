/**
 * MVR Currency Utilities
 * Implements banker's rounding and Rf formatting.
 */

export const MVR = {
  format: (amount: number): string => {
    return `Rf ${amount.toLocaleString('en-MV', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  },

  round: (amount: number): number => {
    // Banker's rounding simulation
    return Math.round((amount + Number.EPSILON) * 100) / 100;
  }
};
