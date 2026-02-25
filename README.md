# Washing Machine Booking System

This is a robust and scalable web application for managing washing machine bookings in residential complexes or laundromats. Built with [FastAPI](https://fastapi.tiangolo.com/) backend and vanilla JavaScript frontend. The project follows a layered architecture pattern, ensuring clear separation of concerns, easy maintenance, and scalability.

## 🏗️ Project Architecture

The application is structured into several modular directories. Here is a breakdown of the core components:

### `app/` - Core Application
This is the root directory for all application code.

* **`main.py`**: The entry point of the application. It initializes the FastAPI instance, configures CORS, registers all routers, and starts the scheduler.
* **`dependencies.py`**: Contains reusable dependencies injected into endpoints (e.g., database sessions, current user authentication).

#### **Application Layers**
* **`routers/`**: The presentation layer. Contains the API endpoints and page routes:
  * `admin.py` - Admin panel API endpoints for managing machines, users, and bookings
  * `auth.py` - Authentication and authorization endpoints (login, registration, logout)
  * `bookings.py` - Booking management endpoints
  * `machines.py` - Washing machine endpoints and schedule retrieval
  * `pages.py` - HTML template routes for web pages
  * `payments.py` - Payment processing endpoints

* **`services/`**: The business logic layer. Contains the core logic of the application:
  * `user_service.py` - User account management and profile operations
  * `booking_service.py` - Booking creation, cancellation, and schedule management
  * `machine_service.py` - Machine management and availability handling
  * `payment_service.py` - Payment processing and transaction handling
  * `notification_service.py` - User notifications (email, Telegram, in-app)

* **`schemas/`**: The data validation layer. Contains Pydantic models for request/response validation:
  * `user.py` - User data schemas
  * `booking.py` - Booking data schemas
  * `machine.py` - Machine data schemas

* **`models/`**: The data access layer. Contains SQLAlchemy ORM models:
  * `user.py` - User model with authentication and profile data
  * `booking.py` - Booking model with schedule management
  * `machine.py` - Washing machine model

#### **Infrastructure & Utilities**
* **`core/`**: Contains app-wide functionality:
  * `security.py` - JWT authentication, password hashing, and authorization utilities
  * `scheduler.py` - Background task scheduler for reminders, notifications, and maintenance

* **`db/`**: Handles database operations:
  * `database.py` - Database connection and session management
  * `migrations/` - Database schema migrations

#### **Frontend**
* **`static/`**: Static assets served to the client:
  * `css/` - Stylesheets for different pages (booking, errors, main)
  * `js/` - JavaScript modules:
    * `admin.js` - Admin dashboard functionality
    * `admin_bookings.js` - Admin booking management
    * `admin_users.js` - Admin user management
    * `booking.js` - Booking interface and calendar
    * `dashboard.js` - User dashboard
    * `global.js` - Shared utilities and helpers
    * `login.js` - Login page logic
    * `pricing.js` - Pricing display
    * `register.js` - Registration form logic

* **`templates/`**: HTML templates for server-side rendering:
  * `base.html` - Base template with common layout
  * `booking.html` - Booking calendar and schedule
  * `dashboard.html` - User dashboard
  * `login.html` - Login page
  * `register.html` - Registration page
  * `pricing.html` - Pricing information
  * `profile_edit.html` - User profile edit form
  * `admin.html` - Admin panel overview
  * `admin_bookings.html` - Admin booking management
  * `admin_users.html` - Admin user management
  * `401.html` - Unauthorized error page
  * `403.html` - Forbidden error page
  * `404.html` - Not found error page

### Root Level Files
* **`.env`**: Stores local environment variables and secrets (not tracked by git)
* **`requirements.txt`**: Lists all Python dependencies required to run the project

## 🚀 Features

* **User Management**: Registration, login, profile management, and role-based access control
* **Booking System**: Calendar-based booking interface with time slots, cancellation support
* **Machine Management**: Add, edit, and manage washing machines with availability tracking
* **Admin Dashboard**: Overview of statistics, user management, booking controls, and system monitoring
* **Payment Integration**: Support for payment processing and transaction management
* **Notifications**: User notifications via multiple channels (email, Telegram, in-app)
* **Background Tasks**: Scheduler for reminders, notifications, and automated tasks
* **Authentication**: Secure JWT-based authentication with role-based access control