-- ============================================================================
-- AI-Powered Employee Productivity & Performance Analyzer
-- MySQL Database Creation Script
--
-- NOTE: The Flask app uses SQLAlchemy and will auto-create these tables for
-- you (db.create_all()) against SQLite by default, or against MySQL if you
-- configure MYSQL_* environment variables in config.py. This script is
-- provided so the schema can also be created manually / reviewed directly,
-- as requested for enterprise deployments.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS employee_productivity_ai
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE employee_productivity_ai;

-- ---------------------------------------------------------------------------
-- Departments
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(255)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Users (login accounts)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'employee',
  is_active_account BOOLEAN DEFAULT TRUE,
  theme VARCHAR(10) DEFAULT 'light',
  language VARCHAR(10) DEFAULT 'en',
  profile_picture VARCHAR(255) DEFAULT 'default_avatar.png',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Employees
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_code VARCHAR(20) NOT NULL UNIQUE,
  user_id INT,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL,
  phone VARCHAR(20),
  gender VARCHAR(10),
  age INT,
  designation VARCHAR(100),
  salary FLOAT,
  joining_date DATE,
  address VARCHAR(255),
  experience_years FLOAT DEFAULT 0,
  education VARCHAR(150),
  status VARCHAR(20) DEFAULT 'Active',
  department_id INT,
  manager_id INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
  FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Attendance
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  date DATE NOT NULL,
  status VARCHAR(20) NOT NULL,
  check_in TIME,
  check_out TIME,
  working_hours FLOAT DEFAULT 0,
  overtime_hours FLOAT DEFAULT 0,
  late_entry BOOLEAN DEFAULT FALSE,
  early_exit BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_emp_date (employee_id, date),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Activity Logs (mouse/keyboard tracking pings)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  date DATE NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  mouse_active BOOLEAN DEFAULT FALSE,
  keyboard_active BOOLEAN DEFAULT FALSE,
  mouse_events INT DEFAULT 0,
  keyboard_events INT DEFAULT 0,
  mouse_clicks INT DEFAULT 0,
  mouse_moves INT DEFAULT 0,
  scroll_events INT DEFAULT 0,
  idle_seconds INT DEFAULT 0,
  active_application VARCHAR(120),
  interval_seconds INT DEFAULT 60,
  source VARCHAR(20) DEFAULT 'browser',
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  INDEX idx_activity_emp_date (employee_id, date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Desktop activity-agent authentication tokens
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_agent_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL UNIQUE,
  token_hash VARCHAR(128) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_used_at DATETIME,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tasks
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  category VARCHAR(100),
  priority VARCHAR(20) DEFAULT 'Medium',
  status VARCHAR(20) DEFAULT 'Pending',
  completed_percent INT DEFAULT 0,
  estimated_hours FLOAT DEFAULT 0,
  actual_hours FLOAT DEFAULT 0,
  assigned_date DATE,
  deadline DATE,
  completion_date DATE,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Performance (monthly aggregated metrics)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS performance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  month VARCHAR(7) NOT NULL,
  attendance_percent FLOAT DEFAULT 0,
  task_completion_rate FLOAT DEFAULT 0,
  work_efficiency FLOAT DEFAULT 0,
  time_management_score FLOAT DEFAULT 0,
  overtime_score FLOAT DEFAULT 0,
  punctuality_score FLOAT DEFAULT 0,
  consistency_score FLOAT DEFAULT 0,
  manager_rating FLOAT DEFAULT 0,
  customer_rating FLOAT DEFAULT 0,
  skill_score FLOAT DEFAULT 0,
  productivity_score FLOAT DEFAULT 0,
  performance_score FLOAT DEFAULT 0,
  performance_grade VARCHAR(20),
  risk_score FLOAT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_emp_month (employee_id, month),
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Predictions (ML output)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  predicted_grade VARCHAR(20),
  confidence FLOAT,
  probabilities TEXT,
  risk_level VARCHAR(20),
  attrition_risk_percent FLOAT DEFAULT 0,
  burnout_risk_percent FLOAT DEFAULT 0,
  promotion_eligible BOOLEAN DEFAULT FALSE,
  recommendations TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Leaves
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS leaves (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  reason VARCHAR(255),
  status VARCHAR(20) DEFAULT 'Pending',
  applied_on DATETIME DEFAULT CURRENT_TIMESTAMP,
  reviewed_by INT,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES employees(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Skills
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  proficiency INT DEFAULT 50,
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Achievements
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS achievements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  title VARCHAR(150) NOT NULL,
  description VARCHAR(255),
  date_awarded DATE,
  icon VARCHAR(50) DEFAULT 'fa-trophy',
  FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Notifications
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(150) NOT NULL,
  message VARCHAR(255),
  category VARCHAR(30) DEFAULT 'info',
  is_read BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- End of schema
-- ============================================================================
