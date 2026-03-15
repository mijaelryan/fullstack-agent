'use client';

import { useState } from 'react';

interface Task {
  text: string;
  completed: boolean;
}

export default function HomePage() {
  const [tasks, setTasks] = useState<Task[]>([]);

  const addTask = (task: string) => {
    if (task.trim() !== '') {
      setTasks([...tasks, { text: task, completed: false }]);
    }
  };

  const toggleCompleteTask = (index: number) => {
    setTasks(prevTasks =>
      prevTasks.map((task, i) =>
        i === index ? { ...task, completed: !task.completed } : task
      )
    );
  };

  const deleteTask = (index: number) => {
    setTasks(tasks.filter((_, i) => i !== index));
  };

  const deleteAllTasks = () => {
    setTasks([]);
  };

  const pendingTasks = tasks.filter(task => !task.completed).length;

  return (
    <main className="min-h-screen bg-gray-100 p-4 font-sans">
      <div className="max-w-xl mx-auto bg-gray-200 shadow-lg p-8 border-2 border-gray-500">
        <h1 className="text-center text-2xl mb-4 font-bold">Lista de Tareas Estilo Windows 95</h1>
        <div className="flex gap-2 items-center mb-4">
          <input
            id="taskInput"
            className="flex-grow border-2 border-gray-400 p-2"
            type="text"
            placeholder="Escribe una tarea..."
          />
          <button
            className="bg-buttonBg text-buttonText px-4 py-2 border border-gray-400 hover:bg-slate-300"
            onClick={() => {
              const inputElement = document.getElementById('taskInput') as HTMLInputElement;
              addTask(inputElement.value);
              inputElement.value = '';
            }}
          >
            Aadir
          </button>
        </div>
        <div className="text-center text-lg mb-4">Tareas pendientes: {pendingTasks}</div>
        <ul className="list-disc pl-5">
          {tasks.map((task, index) => (
            <li
              key={index}
              className={`flex justify-between items-center bg-gray-100 p-2 mb-2 border border-gray-400 ${
                task.completed ? 'line-through text-gray-500' : ''
              }`}
            >
              <span>{task.text}</span>
              <div className="inline-flex space-x-2">
                <button
                  className="bg-buttonBg text-buttonText px-2 py-1 border border-gray-400 hover:bg-slate-300"
                  onClick={() => toggleCompleteTask(index)}
                >
                  {task.completed ? 'Desmarcar' : 'Marcar como completada'}
                </button>
                <button
                  className="bg-buttonBg text-buttonText px-2 py-1 border border-gray-400 hover:bg-slate-300"
                  onClick={() => deleteTask(index)}
                >
                  Eliminar
                </button>
              </div>
            </li>
          ))}
        </ul>
        <button
          onClick={deleteAllTasks}
          className="mt-4 w-full bg-buttonBg text-buttonText p-3 border border-gray-400 hover:bg-slate-300"
        >
          Eliminar todas las tareas
        </button>
      </div>
    </main>
  );
}