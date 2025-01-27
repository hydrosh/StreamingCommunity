import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import { Container, Row, Col, Card, Button, Badge, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { FaTrash } from 'react-icons/fa';

import { SERVER_WATCHLIST_URL } from './ApiUrl';

const Watchlist = ({ theme }) => {
  const [watchlistItems, setWatchlistItems] = useState([]);
  const [newSeasons, setNewSeasons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newSeasonsMessage, setNewSeasonsMessage] = useState(""); 

  // Funzione per recuperare i dati della watchlist
  const fetchWatchlistData = async () => {
    try {
      const watchlistResponse = await axios.get(`${SERVER_WATCHLIST_URL}/get`);
      // Assicuriamoci che watchlistResponse.data sia un array
      const items = Array.isArray(watchlistResponse.data) ? watchlistResponse.data : [];
      setWatchlistItems(items);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching watchlist:", error);
      setWatchlistItems([]); // In caso di errore, impostiamo un array vuoto
      setLoading(false);
    }
  };

  // Funzione per controllare se ci sono nuove stagioni (attivata dal bottone)
  const checkNewSeasons = async () => {
    try {
      const newSeasonsResponse = await axios.get(`${SERVER_WATCHLIST_URL}/check`);
      
      if (Array.isArray(newSeasonsResponse.data)) {
        setNewSeasons(newSeasonsResponse.data);

        // Crea un messaggio per i titoli con nuove stagioni
        const titlesWithNewSeasons = newSeasonsResponse.data.map(season => season.name);
        if (titlesWithNewSeasons.length > 0) {
          setNewSeasonsMessage(`Nuove stagioni disponibili per: ${titlesWithNewSeasons.join(", ")}`);
          
          // Dopo aver mostrato il messaggio, aggiorniamo i titoli con le nuove stagioni
          updateTitlesWithNewSeasons(newSeasonsResponse.data);
        } else {
          setNewSeasonsMessage("Nessuna nuova stagione disponibile.");
        }
      } else {
        setNewSeasons([]);  // In caso contrario, non ci sono nuove stagioni
        setNewSeasonsMessage("Nessuna nuova stagione disponibile.");
      }
    } catch (error) {
      console.error("Error fetching new seasons:", error);
    }
  };

  // Funzione per inviare la richiesta POST per aggiornare il titolo nella watchlist
  const updateTitlesWithNewSeasons = async (newSeasonsList) => {
    try {
      for (const season of newSeasonsList) {
        // Manda una richiesta POST per ogni titolo con nuove stagioni
        console.log(`Updated watchlist for ${season.name} with new season ${season.nNewSeason}, url: ${season.title_url}`);
        
        await axios.post(`${SERVER_WATCHLIST_URL}/update`, {
          url: season.title_url,
          season: season.season
        });
        
      }
    } catch (error) {
      console.error("Error updating title watchlist:", error);
    }
  };

  // Funzione per rimuovere un elemento dalla watchlist
  const handleRemoveFromWatchlist = async (serieName) => {
    try {
      await axios.post(`${SERVER_WATCHLIST_URL}/remove`, {
        name: serieName
      });
  
      setWatchlistItems((prev) => prev.filter((item) => item.name !== serieName));
    } catch (error) {
      console.error("Error removing from watchlist:", error);
    }
  };
  
  
  // Carica inizialmente la watchlist
  useEffect(() => {
    fetchWatchlistData();
  }, []);

  if (loading) {
    return (
      <Container fluid className="p-4">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container fluid className="watchlist-container p-4">
      <Container>
        <h2 className="mb-4">My Watchlist</h2>
        
        <Button onClick={checkNewSeasons} variant="primary" className="mb-4">
          Check for New Seasons
        </Button>

        {newSeasonsMessage && (
          <Alert variant={newSeasonsMessage.includes("Nuove stagioni") ? "success" : "info"}>
            {newSeasonsMessage}
          </Alert>
        )}

        {(!watchlistItems || watchlistItems.length === 0) ? (
          <Alert variant="info">Your watchlist is empty.</Alert>
        ) : (
          <Row xs={1} md={3} className="g-4">
            {watchlistItems.map((item) => {
              const hasNewSeason = newSeasons && Array.isArray(newSeasons) && newSeasons.some(
                (season) => season.name === item.name
              );

              return (
                <Col key={item.name}>
                  <Card className="h-100">
                    <Card.Body>
                      <div className="d-flex justify-content-between align-items-start">
                        <Card.Title>
                          {item.name.replace(/-/g, ' ')}
                          {hasNewSeason && (
                            <Badge bg="danger" className="ms-2">New Season</Badge>
                          )}
                        </Card.Title>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => handleRemoveFromWatchlist(item.name)}
                        >
                          <FaTrash />
                        </Button>
                      </div>
                      <Card.Text>
                        <small className="text-secondary">
                          Added on: {new Date(item.added_on).toLocaleDateString()}
                        </small>
                        <br />
                        <small className="text-secondary">Seasons: {item.season}</small>
                      </Card.Text>
                      <Link
                        to={`/title/${item.name}`}
                        className="btn btn-primary btn-sm"
                      >
                        View Details
                      </Link>
                    </Card.Body>
                  </Card>
                </Col>
              );
            })}
          </Row>
        )}
      </Container>
    </Container>
  );
};

Watchlist.propTypes = {
  theme: PropTypes.oneOf(['light', 'dark']).isRequired,
};

export default Watchlist;
