import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';

const Navbar = ({ toggleTheme, theme }) => {
  return (
    <nav className={`navbar navbar-expand-lg custom-navbar`}>
      <div className="container-fluid" id="navbar">
        <Link className="navbar-brand" to="/">Home</Link>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav">
            <li className="nav-item">
              <Link className="nav-link" to="/watchlist">Watchlist</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/downloads">Downloads</Link>
            </li>
          </ul>
          <button
            className="theme-toggle-btn ms-auto"
            onClick={toggleTheme}
          >
            {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
        </div>
      </div>
    </nav>
  );
};

// Validazione delle proprietà
Navbar.propTypes = {
  toggleTheme: PropTypes.func.isRequired,
  theme: PropTypes.oneOf(['light', 'dark']).isRequired,
};

export default Navbar;