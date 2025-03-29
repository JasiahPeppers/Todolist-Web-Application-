document.addEventListener("DOMContentLoaded", () => {
    const today = new Date();
    const dateElement = document.getElementById("currentDate");
    const tomorrowElement = document.getElementById("tomorrowDate");

    dateElement.textContent = today.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    tomorrowElement.textContent = tomorrow.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const taskInput = document.getElementById("taskInput");
    const descInput = document.getElementById("descInput");
    const addButton = document.getElementById("addButton");
    const taskList = document.getElementById("taskList");
    let taskCount = 0;

    function fetchTasks() {
        fetch('https://todolistalt.onrender.com/tasks')
            .then(response => response.json())
            .then(tasks => {
                tasks.forEach(task => {
                    addTaskToList(task);
                });
            })
            .catch(error => {
                console.error('Error fetching tasks:', error);
                alert('Failed to fetch tasks. Please try again later.');
            });
    }

    fetchTasks();

    addButton.addEventListener("click", () => {
        const taskValue = taskInput.value.trim();
        const descValue = descInput.value.trim();

        if (taskValue) {
            const task = {
                task: taskValue,
                description: descValue,
                task_date: today.toISOString().split('T')[0],
                priority: 'low' // Default priority
            };

            fetch('https://todolistalt.onrender.com/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(task)
            })
            .then(response => response.json())
            .then(newTask => {
                addTaskToList(newTask);
                taskInput.value = '';
                descInput.value = '';
            })
            .catch(error => {
                console.error('Error adding task:', error);
                alert('Failed to add task. Please try again later.');
            });
        }
    });

    function addTaskToList(task) {
        const listItem = document.createElement("li");
        listItem.draggable = true;
        taskCount++;
        listItem.classList.add(`${task.priority}-priority`);
        listItem.innerHTML = `
            <div class="task-wrapper">
                <span class="task-title">
                    <span class="task-number">${taskCount}.</span> ${task.task}
                </span>
                <span class="desc">${task.description}</span>
            </div>
            <div class="action-buttons" style="display:none;">
                <button class="delete-btn">Delete</button>
                <button class="complete-btn">Complete</button>
                <button class="incomplete-btn" style="display: none;">Incomplete</button>
                <button class="priority-btn">${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)} <span class="dropdown-arrow">▼</span></button>
                <div class="priority-dropdown" style="display: none;">
                    <button class="priority-option" data-priority="low">Low</button>
                    <button class="priority-option" data-priority="medium">Medium</button>
                    <button class="priority-option" data-priority="high">High</button>
                </div>
            </div>
        `;

        taskList.appendChild(listItem);

        const actionButtons = listItem.querySelector('.action-buttons');
        listItem.addEventListener('click', function() {
            const isActionButtonsVisible = actionButtons.style.display === 'inline-block';
            actionButtons.style.display = isActionButtonsVisible ? 'none' : 'inline-block';
        });

        const deleteButton = listItem.querySelector('.delete-btn');
        deleteButton.addEventListener('click', function() {
            fetch(`https://todolistalt.onrender.com/tasks/${task.id}`, {
                method: 'DELETE'
            })
            .then(() => {
                taskList.removeChild(listItem);
            })
            .catch(error => {
                console.error('Error deleting task:', error);
                alert('Failed to delete task. Please try again later.');
            });
        });

        const completeButton = listItem.querySelector('.complete-btn');
        const incompleteButton = listItem.querySelector('.incomplete-btn');
        completeButton.addEventListener('click', function() {
            listItem.classList.toggle('completed');
            completeButton.style.display = 'none';
            incompleteButton.style.display = 'inline-block';

            fetch(`https://todolistalt.onrender.com/tasks/${task.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: false })
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error marking task as complete:', error);
                alert('Failed to mark task as complete. Please try again later.');
            });
        });

        incompleteButton.addEventListener('click', function() {
            listItem.classList.remove('completed');
            completeButton.style.display = 'inline-block';
            incompleteButton.style.display = 'none';

            fetch(`https://todolistalt.onrender.com/tasks/${task.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: true })
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error marking task as incomplete:', error);
                alert('Failed to mark task as incomplete. Please try again later.');
            });
        });

        const priorityBtn = listItem.querySelector('.priority-btn');
        const priorityDropdown = listItem.querySelector('.priority-dropdown');
        const priorityOptions = listItem.querySelectorAll('.priority-option');

        priorityBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            priorityDropdown.style.display = priorityDropdown.style.display === 'none' ? 'block' : 'none';
        });

        priorityOptions.forEach(option => {
            option.addEventListener('click', (event) => {
                event.stopPropagation();
                const newPriority = option.dataset.priority;
                task.priority = newPriority;
                priorityBtn.firstChild.textContent = newPriority.charAt(0).toUpperCase() + newPriority.slice(1);
                priorityDropdown.style.display = 'none';

                // Update the task's priority on the server
                fetch(`https://todolistalt.onrender.com/tasks/${task.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ priority: newPriority })
                })
                .then(response => response.json())
                .catch(error => {
                    console.error('Error updating task priority:', error);
                    alert('Failed to update task priority. Please try again later.');
                });

                updatePriorityColor(listItem, newPriority);
                listItem.classList.remove('low-priority', 'medium-priority', 'high-priority');
                listItem.classList.add(`${newPriority}-priority`);
            });
        });

        // Description editing functionality
        const descElement = listItem.querySelector('.desc');
        descElement.addEventListener('click', function() {
            const currentDesc = descElement.textContent.trim();
            const textarea = document.createElement('textarea');
            textarea.value = currentDesc;
            textarea.style.width = '100%';
            textarea.style.height = '40px';

            const taskWrapper = listItem.querySelector('.task-wrapper');
            taskWrapper.appendChild(textarea);

            descElement.style.display = 'none';

            textarea.focus();
            textarea.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    descElement.textContent = textarea.value;
                    textarea.replaceWith(descElement);
                    descElement.style.display = 'block';

                    const updatedDesc = textarea.value.trim();
                    task.description = updatedDesc;

                    fetch(`https://todolistalt.onrender.com/tasks/${task.id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ description: updatedDesc })
                    })
                    .then(response => response.json())
                    .catch(error => {
                        console.error('Error updating task description:', error);
                        alert('Failed to update task description. Please try again later.');
                    });
                }
            });
        });
    }

    // Update the color based on priority
    function updatePriorityColor(listItem, priority) {
        const colorMap = {
            low: '#ffa203',
            medium: '#EE4B2B',
            high: '#af69ee'
        };
        listItem.style.backgroundColor = colorMap[priority] || '#ffffff';
    }
});
