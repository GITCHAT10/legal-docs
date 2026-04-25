import React from 'react';

/**
 * SalaOS Dashboard Entry Point.
 * Layout: COCKPIT_DASHBOARD
 */
export const SalaOSHotelUIPrototype: React.FC = () => {
  return (
    <div className="cockpit-dashboard">
      <header>SALA-OS COCKPIT</header>
      <main>
        <section id="overview">
          {/* Real-time arrivals and room status */}
        </section>
        <aside id="right-panel-alerts">
          {/* SILVIA recommendations injected here */}
        </aside>
      </main>
    </div>
  );
};

export default SalaOSHotelUIPrototype;
