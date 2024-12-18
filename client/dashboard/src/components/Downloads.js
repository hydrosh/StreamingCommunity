import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Row, Col, Card, Button, Badge, Modal } from 'react-bootstrap';
import { FaTrash, FaPlay } from 'react-icons/fa';
import { Link } from 'react-router-dom';

const API_BASE_URL = "http://127.0.0.1:1234";

const Downloads = () => {
  const [downloads, setDownloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPlayer, setShowPlayer] = useState(false);
  const [currentVideo, setCurrentVideo] = useState("");

  // Fetch all downloads
  const fetchDownloads = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/downloads`);
      setDownloads(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching downloads:", error);
      setLoading(false);
    }
  };

  // Delete a TV episode
  const handleDeleteEpisode = async (id, season, episode) => {
    try {
      await axios.delete(`${API_BASE_URL}/deleteEpisode`, {
        params: { id, season, episode }
      });
      fetchDownloads(); // Refresh the list
    } catch (error) {
      console.error("Error deleting episode:", error);
    }
  };

  // Delete a movie
  const handleDeleteMovie = async (id) => {
    try {
      await axios.delete(`${API_BASE_URL}/deleteMovie`, {
        params: { id }
      });
      fetchDownloads(); // Refresh the list
    } catch (error) {
      console.error("Error deleting movie:", error);
    }
  };

  // Watch video
  const handleWatchVideo = (videoPath) => {
    setCurrentVideo(videoPath);
    setShowPlayer(true);
  };

  // Initial fetch of downloads
  useEffect(() => {
    fetchDownloads();
  }, []);

  if (loading) {
    return <div className="text-center mt-5">Loading...</div>;
  }

  // Separate movies and TV shows
  const movies = downloads.filter(item => item.type === 'movie');
  const tvShows = downloads.filter(item => item.type === 'tv');

  // Group TV shows by slug
  const groupedTvShows = tvShows.reduce((acc, show) => {
    if (!acc[show.slug]) {
      acc[show.slug] = [];
    }
    acc[show.slug].push(show);
    return acc;
  }, {});

  return (
    <Container fluid className="p-0">
      <Container className="mt-4">
        <h2 className="mb-4">My Downloads</h2>

        {/* Movies Section */}
        <h3 className="mt-4 mb-3">Movies</h3>
        {movies.length === 0 ? (
          <p>No movies downloaded.</p>
        ) : (
          <Row xs={1} md={3} className="g-4">
            {movies.map((movie) => (
              <Col key={movie.id}>
                <Card>
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <Card.Title>{movie.slug.replace(/-/g, ' ')}</Card.Title>
                      <Button
                        variant="outline-danger"
                        size="sm"
                        onClick={() => handleDeleteMovie(movie.id)}
                      >
                        <FaTrash />
                      </Button>
                    </div>
                    <Card.Text>
                      <small>Downloaded on: {new Date(movie.timestamp).toLocaleString()}</small>
                    </Card.Text>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleWatchVideo(movie.path)}
                    >
                      <FaPlay className="me-2" /> Watch
                    </Button>
                    <Link
                      to={`/title/${movie.slug}`}
                      state={{ url: movie.slug }}
                      className="btn btn-secondary btn-sm ms-2"
                    >
                      View Details
                    </Link>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {/* TV Shows Section */}
        <h3 className="mt-4 mb-3">TV Shows</h3>
        {Object.keys(groupedTvShows).length === 0 ? (
          <p>No TV shows downloaded.</p>
        ) : (
          Object.entries(groupedTvShows).map(([slug, episodes]) => (
            <div key={slug} className="mb-4">
              <h4>{slug.replace(/-/g, ' ')}</h4>
              <Row xs={1} md={3} className="g-4">
                {episodes.map((episode) => (
                  <Col key={`${episode.n_s}-${episode.n_ep}`}>
                    <Card>
                      <Card.Body>
                        <div className="d-flex justify-content-between align-items-start">
                          <Card.Title>
                            S{episode.n_s} E{episode.n_ep}
                          </Card.Title>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => handleDeleteEpisode(episode.id, episode.n_s, episode.n_ep)}
                          >
                            <FaTrash />
                          </Button>
                        </div>
                        <Card.Text>
                          <small>Downloaded on: {new Date(episode.timestamp).toLocaleString()}</small>
                        </Card.Text>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleWatchVideo(episode.path)}
                        >
                          <FaPlay className="me-2" /> Watch
                        </Button>
                        <Link
                          to={`/title/${slug}`}
                          state={{ url: slug }}
                          className="btn btn-secondary btn-sm ms-2"
                        >
                          View Details
                        </Link>
                      </Card.Body>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          ))
        )}
      </Container>

      {/* Modal Video Player */}
      <Modal show={showPlayer} onHide={() => setShowPlayer(false)} size="lg" centered>
        <Modal.Body>
          <video 
            src={`http://127.0.0.1:1234/downloaded/${currentVideo}`} 
            controls 
            autoPlay 
            style={{ width: '100%' }}
          />
        </Modal.Body>
      </Modal>
    </Container>
  );
};

export default Downloads;