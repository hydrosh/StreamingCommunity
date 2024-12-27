import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';
import { Container, Row, Col, Card, Button, Badge, Modal } from 'react-bootstrap';
import { FaTrash, FaPlay, FaDownload, FaClock } from 'react-icons/fa';
import { toast } from 'react-toastify';

import { SERVER_PATH_URL, SERVER_DELETE_URL, API_URL } from './ApiUrl';

const Downloads = ({ theme }) => {
  const [downloads, setDownloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadStatus, setDownloadStatus] = useState({ current_download: null, queue: [] });
  const [showPlayer, setShowPlayer] = useState(false);
  const [currentVideo, setCurrentVideo] = useState("");

  // Fetch all downloads and status
  const fetchDownloads = async () => {
    try {
      const [downloadsResponse, statusResponse] = await Promise.all([
        axios.get(`${SERVER_PATH_URL}/get`),
        axios.get(`${API_URL}/downloads/status`)
      ]);
      setDownloads(downloadsResponse.data);
      setDownloadStatus(statusResponse.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching downloads:", error);
      setLoading(false);
    }
  };

  // Delete a TV episode
  const handleDeleteEpisode = async (id, season, episode) => {
    try {
      await axios.delete(`${SERVER_DELETE_URL}/episode`, {
        params: { series_id: id, season_number: season, episode_number: episode }
      });
      fetchDownloads(); // Refresh the list
    } catch (error) {
      console.error("Error deleting episode:", error);
    }
  };

  // Delete a movie
  const handleDeleteMovie = async (id) => {
    try {
      await axios.delete(`${SERVER_DELETE_URL}/movie`, {
        params: { movie_id: id }
      });
      fetchDownloads(); // Refresh the list
    } catch (error) {
      console.error("Error deleting movie:", error);
    }
  };

  // Watch video
  const handleWatchVideo = async (videoPath) => {
    if (!videoPath) {
      toast.error('Video path not found');
      return;
    }
    
    try {
      // Ottieni il nome del file dal path completo
      const filename = videoPath.split(/[\\/]/).pop();
      
      // Verifica che il file esista nel database
      const response = await axios.get(`${SERVER_PATH_URL}/get`);
      const downloads = response.data;
      
      // Trova il download corrispondente
      const download = downloads.find(d => d.path.includes(filename));
      
      if (download?.path) {
        const encodedPath = encodeURIComponent(filename);
        const videoUrl = `${API_URL}/downloaded/${encodedPath}`;
        setCurrentVideo(videoUrl);
        setShowPlayer(true);
      } else {
        toast.error('File not found in downloads');
      }
    } catch (error) {
      console.error('Error getting video path:', error);
      toast.error('Failed to get video path');
    }
  };

  // Get status badge
  const getStatusBadge = (item) => {
    const isCurrentDownload = downloadStatus.current_download && 
      downloadStatus.current_download.id === item.id &&
      downloadStatus.current_download.type === item.type;

    if (isCurrentDownload) {
      return <Badge bg="primary"><FaDownload /> Downloading</Badge>;
    }

    const isQueued = downloadStatus.queue.some(queueItem => 
      queueItem.id === item.id && queueItem.type === item.type
    );

    if (isQueued) {
      return <Badge bg="warning"><FaClock /> In Queue</Badge>;
    }

    if (item.status === "completed") {
      return <Badge bg="success">Completed</Badge>;
    }

    if (item.status === "failed") {
      return <Badge bg="danger">Failed</Badge>;
    }

    return null;
  };

  // Initial fetch and periodic updates
  useEffect(() => {
    fetchDownloads();
    const interval = setInterval(fetchDownloads, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
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
    <Container fluid className="p-0" id="downloads-container">
      <Container className="mt-4">
        <h2 className="mb-4">My Downloads</h2>

        {/* Current Download Status */}
        {downloadStatus.current_download && (
          <div className="mb-4">
            <h4>Currently Downloading</h4>
            <Card className={theme === 'dark' ? 'bg-secondary text-white' : ''}>
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <h5>{downloadStatus.current_download.slug.replace(/-/g, ' ')}</h5>
                    {downloadStatus.current_download.type === 'tv' && (
                      <p className="mb-0">
                        Season {downloadStatus.current_download.season}, 
                        Episode {downloadStatus.current_download.episode}
                      </p>
                    )}
                  </div>
                  <Badge bg="primary"><FaDownload /> Downloading</Badge>
                </div>
              </Card.Body>
            </Card>
          </div>
        )}

        {/* Download Queue */}
        {downloadStatus.queue.length > 0 && (
          <div className="mb-4">
            <h4>Download Queue</h4>
            {downloadStatus.queue.map((item, index) => (
              <Card key={index} className={`mb-2 ${theme === 'dark' ? 'bg-secondary text-white' : ''}`}>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <h5>{item.slug.replace(/-/g, ' ')}</h5>
                      {item.type === 'tv' && (
                        <p className="mb-0">
                          Season {item.season}, 
                          Episode {item.episode}
                        </p>
                      )}
                    </div>
                    <Badge bg="warning"><FaClock /> In Queue</Badge>
                  </div>
                </Card.Body>
              </Card>
            ))}
          </div>
        )}

        {/* Movies Section */}
        <h3 className="mt-4 mb-3">Movies</h3>
        {movies.length === 0 ? (
          <p>No movies downloaded.</p>
        ) : (
          <Row xs={1} md={3} className="g-4">
            {movies.map((movie) => (
              <Col key={movie.id}>
                <Card className={theme === 'dark' ? 'bg-secondary text-white' : ''}>
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <Card.Title>{movie.slug.replace(/-/g, ' ')}</Card.Title>
                        {getStatusBadge(movie)}
                      </div>
                      <div className="d-flex">
                        {movie.path && (
                          <Button
                            variant="primary"
                            className="me-2"
                            onClick={() => handleWatchVideo(movie.path)}
                          >
                            <FaPlay />
                          </Button>
                        )}
                        <Button
                          variant="danger"
                          onClick={() => handleDeleteMovie(movie.id)}
                        >
                          <FaTrash />
                        </Button>
                      </div>
                    </div>
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
            <Card key={slug} className={`mb-4 ${theme === 'dark' ? 'bg-secondary text-white' : ''}`}>
              <Card.Header>
                <h4>{slug.replace(/-/g, ' ')}</h4>
              </Card.Header>
              <Card.Body>
                <Row xs={1} md={2} lg={3} className="g-3">
                  {episodes.map((episode) => (
                    <Col key={`${episode.id}-${episode.n_s}-${episode.n_ep}`}>
                      <Card className={theme === 'dark' ? 'bg-dark text-white' : ''}>
                        <Card.Body>
                          <div className="d-flex justify-content-between align-items-start">
                            <div>
                              <Card.Title>
                                S{episode.n_s}E{episode.n_ep}
                              </Card.Title>
                              {getStatusBadge(episode)}
                            </div>
                            <div className="d-flex">
                              {episode.path && (
                                <Button
                                  variant="primary"
                                  className="me-2"
                                  onClick={() => handleWatchVideo(episode.path)}
                                >
                                  <FaPlay />
                                </Button>
                              )}
                              <Button
                                variant="danger"
                                onClick={() => handleDeleteEpisode(episode.id, episode.n_s, episode.n_ep)}
                              >
                                <FaTrash />
                              </Button>
                            </div>
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card.Body>
            </Card>
          ))
        )}
      </Container>

      {/* Video Player Modal */}
      <Modal 
        show={showPlayer} 
        onHide={() => setShowPlayer(false)} 
        size="lg"
        centered
        contentClassName={theme === 'dark' ? 'bg-dark' : 'bg-light'}
      >
        <Modal.Header 
          closeButton 
          className={theme === 'dark' ? 'bg-dark text-white border-secondary' : 'bg-light'}
          closeVariant={theme === 'dark' ? 'white' : 'dark'}
        >
          <Modal.Title>Video Player</Modal.Title>
        </Modal.Header>
        <Modal.Body className={theme === 'dark' ? 'bg-dark' : 'bg-light'}>
          <video 
            controls 
            autoPlay 
            style={{ width: '100%' }}
            src={currentVideo}
          >
            Your browser does not support the video tag.
          </video>
        </Modal.Body>
      </Modal>
    </Container>
  );
};

Downloads.propTypes = {
  theme: PropTypes.oneOf(['light', 'dark']).isRequired,
};

export default Downloads;