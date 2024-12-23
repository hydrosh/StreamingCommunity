import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { Form, InputGroup, Button } from 'react-bootstrap';
import { FaSearch } from 'react-icons/fa';

const SearchBar = ({ onSearch, theme }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // If onSearch prop is provided, call it
      if (onSearch) {
        onSearch(searchQuery);
      }
      
      // Navigate to search results page
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <Form onSubmit={handleSearch} className="w-100">
      <InputGroup>
        <Form.Control
          type="text"
          placeholder="Search movies or TV shows..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-bar-input"
        />
        <Button type="submit" variant="primary" className="search-bar-button">
          <FaSearch />
        </Button>
      </InputGroup>
    </Form>
  );
};

SearchBar.propTypes = {
  onSearch: PropTypes.func,
  theme: PropTypes.string
};

export default SearchBar;