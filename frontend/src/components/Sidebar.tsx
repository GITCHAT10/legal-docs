import React from 'react';

const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Overview', icon: '🏠' },
    { name: 'AIRBOX', icon: '📦' },
    { name: 'AIRDRIVE', icon: '☁️' },
    { name: 'AIR MAIL / EXMAIL', icon: '📧', active: true },
    { name: 'AIRCHAT', icon: '💬' },
    { name: 'API FABRIC', icon: '🕸️' },
    { name: 'SHADOW', icon: '🛡️' },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 h-screen p-4 flex flex-col">
      <div className="text-xl font-bold text-blue-500 mb-8 px-2">AIG AIR CLOUD</div>
      <nav className="flex-1">
        <ul className="space-y-1">
          {navItems.map(item => (
            <li key={item.name}>
              <a
                href="#"
                className={`flex items-center gap-3 px-3 py-2 rounded-md transition ${
                  item.active ? 'bg-blue-600/20 text-blue-400 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="mt-auto pt-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-2 text-xs text-slate-500">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          SOVEREIGN MODE ACTIVE
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
