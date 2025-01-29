import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import axios from 'axios';
import { Container, Row, Col, Image, Button, Dropdown, Modal, Alert, Spinner } from 'react-bootstrap';
import { FaDownload, FaPlay, FaPlus, FaTrash } from 'react-icons/fa';

import SearchBar from './SearchBar.js';

import { API_URL, API_BASE_URL, SERVER_WATCHLIST_URL, SERVER_PATH_URL } from './ApiUrl.js';

const TitleDetail = ({ theme, toggleTheme }) => {
  const [titleDetails, setTitleDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSeason, setSelectedSeason] = useState(1);
  const [episodes, setEpisodes] = useState([]);
  const [hoveredEpisode, setHoveredEpisode] = useState(null);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [downloadStatus, setDownloadStatus] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [showPlayer, setShowPlayer] = useState(false);
  const [currentVideo, setCurrentVideo] = useState("");
  const location = useLocation();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const titleUrl = location.state?.url || location.pathname.split('/title/')[1];

        // Fetch title information
        const response = await axios.get(`${API_URL}/getInfo`, {
          params: { url: titleUrl }
        });
        
        const titleData = response.data;
        setTitleDetails(titleData);
        await checkDownloadStatus();
        await checkWatchlistStatus(titleData.slug);

        // For TV shows, fetch first season episodes directly
        if (titleData.type === 'tv') {
          setEpisodes(titleData.episodes || []);
        }

        setLoading(false);
      } catch (error) {
        console.error("Error fetching title details:", error);
        setLoading(false);
      }
    };

    fetchData();
  }, [location]);

  // Check download status
  const checkDownloadStatus = async () => {
    try {
      if (!titleDetails) return;

      const response = await axios.get(`${SERVER_PATH_URL}/get`);
      
      if (titleDetails.type === 'movie') {
        const downloadedMovie = response.data.find(
          download => download.type === 'movie' && 
                     download.id === titleDetails.id.toString()
        );
        
        if (downloadedMovie) {
          console.log("Found movie in downloads:", downloadedMovie);
          setDownloadStatus(downloadedMovie.status);
          setDownloadProgress(downloadedMovie.progress || 0);
        } else {
          setDownloadStatus(null);
          setDownloadProgress(0);
        }
      } else if (titleDetails.type === 'tv') {
        const response = await axios.get(`${SERVER_PATH_URL}/get`);
        const downloadedEpisodes = response.data.filter(
          download => download.type === 'tv' && download.slug === titleDetails.slug
        );
        
        const episodeStatus = {};
        downloadedEpisodes.forEach(episode => {
          episodeStatus[`S${episode.n_s}E${episode.n_ep}`] = 'completed';
        });
        setDownloadStatus(episodeStatus);
      }
    } catch (error) {
      console.error("Error checking download status:", error);
    }
  };

  // Fetch download status periodically
  useEffect(() => {
    const interval = setInterval(checkDownloadStatus, 5000);
    return () => clearInterval(interval);
  }, [titleDetails]);

  // Check watchlist status
  const checkWatchlistStatus = async (slug) => {
    try {
      const response = await axios.get(`${SERVER_WATCHLIST_URL}/get`);
      const inWatchlist = response.data.some(item => item.name === slug);
      setIsInWatchlist(inWatchlist);
    } catch (error) {
      console.error("Error checking watchlist status:", error);
    }
  };

  const handleSeasonSelect = async (seasonNumber) => {
    if (titleDetails.type === 'tv') {
      try {
        setLoading(true);
        const seasonResponse = await axios.get(`${API_URL}/getInfoSeason`, {
          params: { 
            url: location.state?.url,
            n: seasonNumber 
          }
        });
        
        setSelectedSeason(seasonNumber);
        setEpisodes(seasonResponse.data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching season details:", error);
        setLoading(false);
      }
    }
  };

  const handleDownloadFilm = async () => {
    try {
      setDownloadStatus('downloading');
      setDownloadProgress(0);
      
      await axios.get(`${API_URL}/download/film`, {
        params: {
          id: titleDetails.id,
          slug: titleDetails.slug
        }
      });
    } catch (error) {
      console.error('Error starting download:', error);
      setDownloadStatus(null);
      setDownloadProgress(0);
      alert("Error downloading film. Please try again.");
    }
  };

  const handleDownloadEpisode = async (seasonNumber, episodeNumber, titleID, titleSlug) => {
    try {
      await axios.get(`${API_URL}/download/episode`, {
        params: {
          n_s: seasonNumber,
          n_ep: episodeNumber,
          titleID: titleID,
          slug: titleSlug 
        }
      });
      setDownloadStatus(prev => ({
        tv: {
          ...prev.tv,
          [`S${seasonNumber}E${episodeNumber}`]: 'downloading'
        }
      }));
      setDownloadProgress(0);
    } catch (error) {
      console.error('Error starting download:', error);
      alert("Error downloading episode. Please try again.");
    }
  };

  const handleWatchVideo = async (videoPath) => {
    if (!videoPath) {
      // If no path provided, attempt to get path from downloads
      try {
        let path;
        if (titleDetails.type === 'movie') {
          const response = await axios.get(`${SERVER_PATH_URL}/movie`, {
            params: { id: titleDetails.id }
          });
          console.log("Got path from server:", response.data.path);
          path = response.data.path;
        } else {
          alert("Please select a specific episode to watch.");
          return;
        }
        
        setCurrentVideo(path);
      } catch (error) {
        console.error("Error getting video path:", error);
        alert("Please download the content first.");
        return;
      }
    } else {
      setCurrentVideo(videoPath);
    }
    setShowPlayer(true);
  };

  const handleAddToWatchlist = async () => {
    try {
      await axios.post(`${SERVER_WATCHLIST_URL}/add`, {
        name: titleDetails.slug,
        url: location.state?.url || location.pathname.split('/title/')[1],
        season: titleDetails.season_count  // Changed 'season_count' to 'season'
      });
      setIsInWatchlist(true);
    } catch (error) {
      console.error("Error adding to watchlist:", error);
      alert("Error adding to watchlist. Please try again.");
    }
 };
 
  const handleRemoveFromWatchlist = async () => {
    try {
      await axios.post(`${SERVER_WATCHLIST_URL}/remove`, {
        name: titleDetails.slug
      });
      setIsInWatchlist(false);
    } catch (error) {
      console.error("Error removing from watchlist:", error);
      alert("Error removing from watchlist. Please try again.");
    }
  };

  const renderDownloadButton = () => {
    if (downloadStatus === 'downloading') {
      return (
        <Button variant="primary" disabled className="d-flex align-items-center gap-2">
          <Spinner
            as="span"
            animation="border"
            size="sm"
            role="status"
            aria-hidden="true"
          />
          Downloading... {downloadProgress}%
        </Button>
      );
    } else if (downloadStatus === 'completed') {
      return (
        <Button variant="success" onClick={() => handleWatchVideo(null)}>
          <FaPlay className="me-2" /> Watch
        </Button>
      );
    } else {
      return (
        <Button variant="primary" onClick={handleDownloadFilm}>
          <FaDownload className="me-2" /> Download
        </Button>
      );
    }
  };

  if (loading) {
    return <div className="text-center mt-5">Loading...</div>;
  }

  if (!titleDetails) {
    return <Container>Title not found</Container>;
  }

  return (
    <Container fluid className="p-0" style={{ 
      backgroundColor: theme === 'dark' ? '#121212' : '#ffffff', 
      color: theme === 'dark' ? '#ffffff' : '#000000' 
    }}>
      <SearchBar />
      
      {/* Background Image */}
      <div 
        style={{
          backgroundImage: `url(${titleDetails.image.background})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          height: '50vh',
          position: 'relative'
        }}
      >
        <div 
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
            padding: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <h1 className="text-white">{titleDetails.name}</h1>
          
          {/* Watchlist Button */}
          {titleDetails.type === 'tv' && (
            <div>
              {isInWatchlist ? (
                <Button 
                  variant="outline-light" 
                  onClick={handleRemoveFromWatchlist}
                >
                  <FaTrash className="me-2" /> Remove from Watchlist
                </Button>
              ) : (
                <Button 
                  variant="outline-light" 
                  onClick={handleAddToWatchlist}
                >
                  <FaPlus className="me-2" /> Add to Watchlist
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      <Container className="mt-4">
        {/* Plot */}
        <Row className="mb-4">
          <Col>
            <p>{titleDetails.plot}</p>
          </Col>
        </Row>

        {/* Download/Watch Button for Movies */}
        {titleDetails.type === 'movie' && (
          <Row className="mb-4">
            <Col>
              {renderDownloadButton()}
            </Col>
          </Row>
        )}

        {/* TV Show Seasons and Episodes */}
        {titleDetails.type === 'tv' && (
          <>
            <Row className="mb-3">
              <Col>
                <Dropdown>
                  <Dropdown.Toggle variant="secondary">
                    Season {selectedSeason}
                  </Dropdown.Toggle>

                  <Dropdown.Menu>
                    {[...Array(titleDetails.season_count)].map((_, index) => (
                      <Dropdown.Item 
                        key={index + 1} 
                        onClick={() => handleSeasonSelect(index + 1)}
                      >
                        Season {index + 1}
                      </Dropdown.Item>
                    ))}
                  </Dropdown.Menu>
                </Dropdown>
              </Col>
            </Row>

            <Row xs={2} md={4} className="g-4">
              {episodes.map((episode) => {
                const episodeKey = `S${selectedSeason}E${episode.number}`;
                const isDownloaded = downloadStatus?.tv?.[episodeKey] === 'completed';
                
                return (
                  <Col key={episode.id}>
                    <div className="episode-thumbnail-wrapper position-relative">
                      <Image 
                        src={episode.image} 
                        alt={`Episode ${episode.number}`} 
                        fluid 
                        rounded 
                        className="mb-2"
                      />
                      <div 
                        className="episode-number position-absolute top-0 start-0 m-2 px-2 py-1" 
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.7)', 
                          color: '#333', 
                          borderRadius: '4px',
                          fontSize: '0.8rem'
                        }}
                      >
                        Ep {episode.number}
                      </div>
                      <h6>{episode.name}</h6>
                      
                      {isDownloaded ? (
                        <Button 
                          variant="success" 
                          onClick={() => handleWatchVideo(null)}
                        >
                          <FaPlay className="me-2" /> Watch
                        </Button>
                      ) : (
                        <Button 
                          variant="primary" 
                          onClick={() => handleDownloadEpisode(selectedSeason, episode.number, titleDetails.id, titleDetails.slug)}
                        >
                          <FaDownload className="me-2" /> Download
                        </Button>
                      )}
                    </div>
                  </Col>
                );
              })}
            </Row>
          </>
        )}
      </Container>

      {/* Modal Video Player */}
      <Modal show={showPlayer} onHide={() => setShowPlayer(false)} size="lg" centered>
        <Modal.Body>
          <video 
            src={`${API_BASE_URL}/server/downloaded/${currentVideo}`}
            controls 
            autoPlay 
            style={{ width: '100%' }}
            className="video-player"
          />
        </Modal.Body>
      </Modal>
    </Container>
  );
};

TitleDetail.propTypes = {
  toggleTheme: PropTypes.func.isRequired,
  theme: PropTypes.oneOf(['light', 'dark']).isRequired,
};

export default TitleDetail;