'use client';

import { useState } from 'react';

interface Task {
  id: number;
  text: string;
  completed: boolean;
}

export default function HomePage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskText, setTaskText] = useState('');

  const addTask = () => {
    if (taskText.trim() === '') return;
    setTasks([...tasks, { id: Date.now(), text: taskText, completed: false }]);
    setTaskText('');
  };

  const toggleTaskCompletion = (id: number) => {
    setTasks(tasks.map(task => task.id === id ? { ...task, completed: !task.completed } : task));
  };

  const deleteTask = (id: number) => {
    setTasks(tasks.filter(task => task.id !== id));
  };

  const clearTasks = () => {
    setTasks([]);
  };

  return (
    <main className="p-4">
      <h1 className="text-2xl font-bold mb-4">Lista de Tareas (Estilo Windows 95)</h1>
      <div className="mb-4">
        <input
          type="text"
          value={taskText}
          onChange={e => setTaskText(e.target.value)}
          placeholder="Escribe una tarea..."
          className="border border-gray-300 p-2 mr-2 rounded"
        />
        <button onClick={addTask} className="bg-windows-bg text-windows-text px-4 py-2 rounded border border-black">Añadir tarea</button>
      </div>
      <ul>
        {tasks.map(task => (
          <li key={task.id} className="flex justify-between items-center mb-2">
            <span className={`flex-1 ${task.completed ? 'line-through' : ''}`}>{task.text}</span>
            <button onClick={() => toggleTaskCompletion(task.id)} className="bg-windows-bg text-windows-text px-2 py-1 rounded border border-black ml-2">{task.completed ? 'Deshacer' : 'Hecho'}</button>
            <button onClick={() => deleteTask(task.id)} className="bg-windows-bg text-windows-text px-2 py-1 rounded border border-black ml-2">Eliminar</button>
          </li>
        ))}
      </ul>
      {tasks.length > 0 && (
        <button onClick={clearTasks} className="bg-windows-bg text-windows-text px-4 py-2 rounded border border-black mt-4">Eliminar todas las tareas</button>
      )}
    </main>
  );
}