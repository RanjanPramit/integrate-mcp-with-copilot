// Global state
let currentUser = null;
let authToken = null;

// DOM Elements
const authModal = document.getElementById('auth-modal');
const appDiv = document.getElementById('app');
const loginForm = document.getElementById('login-form-element');
const registerForm = document.getElementById('register-form-element');
const logoutBtn = document.getElementById('logout-btn');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// ============================================
// Authentication Functions
// ============================================

function switchForm(formType) {
    document.getElementById('login-form').classList.toggle('hidden', formType === 'register');
    document.getElementById('register-form').classList.toggle('hidden', formType === 'login');
}

function showMessage(elementId, message, isError = false) {
    const msgElement = document.getElementById(elementId);
    msgElement.textContent = message;
    msgElement.className = `message ${isError ? 'error' : 'success'}`;
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error('Invalid credentials');
        }

        const data = await response.json();
        authToken = data.access_token;
        currentUser = data.user;

        // Save to localStorage
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(currentUser));

        showAuthUI();
        loadActivities();
    } catch (error) {
        showMessage('login-message', error.message, true);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const email = document.getElementById('register-email').value;
    const fullName = document.getElementById('register-name').value;
    const gradeLevel = parseInt(document.getElementById('register-grade').value);
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                full_name: fullName,
                grade_level: gradeLevel,
                password
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        showMessage('register-message', 'Registered successfully! Please login.', false);
        setTimeout(() => switchForm('login'), 2000);
    } catch (error) {
        showMessage('register-message', error.message, true);
    }
}

function logout() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    showLoginUI();
}

function showLoginUI() {
    authModal.classList.remove('hidden');
    appDiv.classList.add('hidden');
}

function showAuthUI() {
    authModal.classList.add('hidden');
    appDiv.classList.remove('hidden');
    document.getElementById('user-name').textContent = currentUser.full_name;
    
    // Show/hide admin panel
    const adminTabs = document.querySelectorAll('.admin-only');
    if (currentUser.role === 'admin') {
        adminTabs.forEach(tab => tab.classList.remove('hidden'));
    } else {
        adminTabs.forEach(tab => tab.classList.add('hidden'));
    }
}

// ============================================
// API Helpers
// ============================================

async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(endpoint, {
        ...options,
        headers
    });

    if (response.status === 401) {
        logout();
        throw new Error('Session expired');
    }

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

// ============================================
// Activity Functions
// ============================================

async function loadActivities() {
    try {
        const activities = await apiCall('/activities');
        displayActivities(activities);
    } catch (error) {
        console.error('Error loading activities:', error);
    }
}

function displayActivities(activities) {
    const list = document.getElementById('activities-list');
    list.innerHTML = '';

    if (activities.length === 0) {
        list.innerHTML = '<p>No activities available.</p>';
        return;
    }

    activities.forEach(activity => {
        const card = createActivityCard(activity);
        list.appendChild(card);
    });

    // Update select for category filter
    const categoryFilter = document.getElementById('category-filter');
    categoryFilter.addEventListener('change', filterActivities);
}

function createActivityCard(activity) {
    const card = document.createElement('div');
    card.className = 'activity-card';

    const isMember = currentUser && activity.students && activity.students.some(s => s.id === currentUser.id);
    const isFull = activity.available_spots <= 0;

    card.innerHTML = `
        <h4>${activity.name}</h4>
        <p class="category"><span class="badge">${activity.category}</span></p>
        <p>${activity.description}</p>
        <p><strong>Schedule:</strong> ${activity.schedule}</p>
        <p><strong>Location:</strong> ${activity.location || 'TBD'}</p>
        <p><strong>Availability:</strong> ${activity.available_spots}/${activity.max_participants} spots</p>
        <div class="card-actions">
            ${isMember ? 
                `<button class="btn btn-danger" onclick="unregisterActivity(${activity.id})">Unregister</button>` :
                `<button class="btn btn-success ${isFull ? 'disabled' : ''}" onclick="signupActivity(${activity.id})" ${isFull ? 'disabled' : ''}>
                    ${isFull ? 'Activity Full' : 'Sign Up'}
                </button>`
            }
        </div>
    `;

    return card;
}

async function signupActivity(activityId) {
    try {
        const result = await apiCall(`/activities/${activityId}/signup`, { method: 'POST' });
        alert(`Successfully signed up for ${result.activity.name}!`);
        loadActivities();
        loadMyActivities();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function unregisterActivity(activityId) {
    if (confirm('Are you sure you want to unregister from this activity?')) {
        try {
            await apiCall(`/activities/${activityId}/unregister`, { method: 'DELETE' });
            alert('Unregistered successfully!');
            loadActivities();
            loadMyActivities();
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

async function loadMyActivities() {
    try {
        const activities = await apiCall('/my-activities');
        const list = document.getElementById('my-activities-list');
        list.innerHTML = '';

        if (activities.length === 0) {
            list.innerHTML = '<p>You haven\'t signed up for any activities yet.</p>';
            return;
        }

        activities.forEach(activity => {
            const card = createActivityCard(activity);
            list.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading my activities:', error);
    }
}

async function loadStats() {
    try {
        const stats = await apiCall('/stats/my-activities');
        document.getElementById('stat-signups').textContent = stats.total_activities;
        document.getElementById('stat-attended').textContent = stats.attended_activities;
        
        const rate = stats.total_activities > 0 
            ? Math.round((stats.attended_activities / stats.total_activities) * 100) 
            : 0;
        document.getElementById('stat-rate').textContent = rate + '%';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function filterActivities() {
    const category = document.getElementById('category-filter').value;
    const cards = document.querySelectorAll('#activities-list .activity-card');
    
    cards.forEach(card => {
        if (!category) {
            card.style.display = '';
        } else {
            const badge = card.querySelector('.badge');
            card.style.display = badge && badge.textContent === category ? '' : 'none';
        }
    });
}

// ============================================
// Admin Functions
// ============================================

async function loadAdminPanel() {
    await loadAdminActivities();
    await loadMeritList();
}

async function loadAdminActivities() {
    try {
        const activities = await apiCall('/activities');
        const list = document.getElementById('admin-activities-list');
        list.innerHTML = '';

        activities.forEach(activity => {
            const div = document.createElement('div');
            div.className = 'admin-activity-item';
            div.innerHTML = `
                <h5>${activity.name}</h5>
                <p>Category: ${activity.category}</p>
                <p>Participants: ${activity.participant_count}/${activity.max_participants}</p>
                <button class="btn btn-danger btn-sm" onclick="deleteActivity(${activity.id})">Delete</button>
            `;
            list.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading admin activities:', error);
    }
}

async function loadMeritList() {
    try {
        const meritList = await apiCall('/admin/merit-list');
        const div = document.getElementById('merit-list');
        div.innerHTML = '';

        if (meritList.length === 0) {
            div.innerHTML = '<p>No students yet.</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'merit-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Student</th>
                    <th>Activities Signed Up</th>
                    <th>Attended</th>
                </tr>
            </thead>
            <tbody>
                ${meritList.map(item => `
                    <tr>
                        <td>${item.student.full_name} (${item.student.grade_level})</td>
                        <td>${item.total_activities}</td>
                        <td>${item.attended_activities}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        div.appendChild(table);
    } catch (error) {
        console.error('Error loading merit list:', error);
    }
}

async function createActivity(e) {
    e.preventDefault();
    
    const activityData = {
        name: document.getElementById('admin-name').value,
        description: document.getElementById('admin-description').value,
        category: document.getElementById('admin-category').value,
        schedule: document.getElementById('admin-schedule').value,
        location: document.getElementById('admin-location').value,
        max_participants: parseInt(document.getElementById('admin-max').value)
    };

    try {
        await apiCall('/admin/activities', {
            method: 'POST',
            body: JSON.stringify(activityData)
        });
        
        showMessage('admin-message', 'Activity created successfully!', false);
        document.getElementById('create-activity-form').reset();
        await loadAdminActivities();
    } catch (error) {
        showMessage('admin-message', error.message, true);
    }
}

async function deleteActivity(activityId) {
    if (confirm('Are you sure you want to delete this activity?')) {
        try {
            await apiCall(`/admin/activities/${activityId}`, { method: 'DELETE' });
            await loadAdminActivities();
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

// ============================================
// Tab Navigation
// ============================================

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Update active button
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update visible content
        tabContents.forEach(content => content.classList.add('hidden'));
        document.getElementById(tabName).classList.remove('hidden');
        
        // Load data for specific tabs
        if (tabName === 'my-activities') {
            loadMyActivities();
        } else if (tabName === 'stats') {
            loadStats();
        } else if (tabName === 'admin') {
            loadAdminPanel();
        }
    });
});

// ============================================
// Event Listeners
// ============================================

loginForm.addEventListener('submit', handleLogin);
registerForm.addEventListener('submit', handleRegister);
logoutBtn.addEventListener('click', logout);

document.getElementById('create-activity-form').addEventListener('submit', createActivity);

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');

    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        showAuthUI();
        loadActivities();
    } else {
        showLoginUI();
    }
});

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
