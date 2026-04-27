import React, { useEffect, useState } from 'react';
import { getSalesTasks } from './api';
import { SalesTask } from './types';

const SalesTasksView: React.FC = () => {
  const [tasks, setTasks] = useState<SalesTask[]>([]);

  useEffect(() => {
    getSalesTasks().then(setTasks);
  }, []);

  return (
    <div className="space-y-3">
      {tasks.length === 0 && <p className="text-slate-500 text-sm italic">No active tasks for Irina.</p>}
      {tasks.map(task => (
        <div key={task.task_id} className="p-4 bg-slate-800 border-l-4 border-red-500 rounded shadow-sm">
          <div className="flex justify-between items-start">
            <h3 className="font-semibold">{task.type}: {task.email}</h3>
            <span className="text-[10px] bg-red-900/50 text-red-300 px-2 py-0.5 rounded">
              {task.priority}
            </span>
          </div>
          <div className="mt-2 flex gap-2">
            <button className="text-xs bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded transition">
              Mark Contacted
            </button>
            <button className="text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded transition">
              View History
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SalesTasksView;
