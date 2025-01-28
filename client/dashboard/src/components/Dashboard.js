import React from 'react';
import PropTypes from 'prop-types';
import { Container } from 'react-bootstrap';
import SearchBar from './SearchBar.js';

const Dashboard = ({ theme, toggleTheme }) => {
  const handleSearch = (query) => {
    // Handle search through the SearchBar component
    console.log("Search query:", query);
  };

  return (
    <Container fluid className={`p-4 ${theme === 'dark' ? 'dark-mode' : 'light-mode'}`}>
      <h1 className="mb-4">Dashboard</h1>
      
      <div className="d-flex justify-content-between align-items-center mb-4">
        <SearchBar onSearch={handleSearch} theme={theme} />
      </div>
    </Container>
  );
};

Dashboard.propTypes = {
  toggleTheme: PropTypes.func.isRequired,
  theme: PropTypes.oneOf(['light', 'dark']).isRequired,
};

export default Dashboard;