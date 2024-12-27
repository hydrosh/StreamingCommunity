import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import PropTypes from 'prop-types';
import axios from 'axios';
import { Container, Row, Col, Image, Button, Modal } from 'react-bootstrap';
import { FaDownload, FaPlay, FaPlus, FaTrash } from 'react-icons/fa';
import { toast } from 'react-toastify';

import SearchBar from './SearchBar.js';

import { API_URL, SERVER_PATH_URL, SERVER_WATCHLIST_URL } from './ApiUrl';

const TitleDetail = ({ theme }) => {
  const { url } = useParams();
  const [titleDetails, setTitleDetails] = useState(null);
  const [episodes, setEpisodes] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(1);
  const [downloadStatus, setDownloadStatus] = useState({ tv: {}, movies: {} });
  const [isInWatchlist, setIsInWatchlist] = useState(false);

  // Fetch title details
  useEffect(() => {
    const fetchTitleDetails = async () => {
      try {
        const response = await axios.get(`${API_URL}/getInfo`, {
          params: { url }
        });
        const titleData = response.data;
        setTitleDetails(titleData);

        // If it's a TV show, fetch first season episodes
        if (titleData.type === 'tv') {
          fetchSeasonEpisodes(1);
        }

        // Check watchlist status
        const watchlistStatus = await axios.get(`${SERVER_WATCHLIST_URL}/check`, {
          params: { title_url: url }
        });
        setIsInWatchlist(watchlistStatus.data.in_watchlist);
      } catch (error) {
        console.error("Error fetching title details:", error);
      }
    };

    fetchTitleDetails();
  }, [url]);

  const fetchSeasonEpisodes = async (seasonNumber) => {
    try {
      const response = await axios.get(`${API_URL}/getInfoSeason`, {
        params: { 
          url,
          n: seasonNumber 
        }
      });
      setEpisodes(response.data);
    } catch (error) {
      console.error("Error fetching season episodes:", error);
    }
  };

  const handleDownloadSeason = async (seasonNumber) => {
    try {
      await axios.get(`${API_URL}/download/season`, {
        params: {
          season: seasonNumber,
          titleID: titleDetails.id,
          slug: titleDetails.slug
        }
      });
      toast.success(`Season ${seasonNumber} queued for download`);
    } catch (error) {
      console.error("Error downloading season:", error);
      toast.error("Failed to queue season for download");
    }
  };

  const handleDownloadEpisode = async (seasonNum, episodeNum) => {
    try {
      const response = await axios.get(`${API_URL}/download/episode`, {
        params: {
          n_s: seasonNum,
          n_ep: episodeNum,
          titleID: titleDetails.id,
          slug: titleDetails.slug
        }
      });
      
      if (response.data.status === "queued") {
        // Update local state
        setDownloadStatus(prev => ({
          tv: {
            ...prev.tv,
            [`S${seasonNum}E${episodeNum}`]: {
              ...prev.tv[`S${seasonNum}E${episodeNum}`],
              queued: true
            }
          }
        }));
      }
    } catch (error) {
      console.error("Error downloading episode:", error);
    }
  };

  const handleWatchVideo = async (videoPath) => {
    if (!videoPath) {
      // If no path provided, attempt to get path from downloads
      try {
        const response = await axios.get(`${SERVER_PATH_URL}/get`);
        const downloads = response.data;
        
        const download = downloads.find(d => {
          if (titleDetails.type === 'movie') {
            return d.type === 'movie' && d.id === titleDetails.id;
          } else {
            return d.type === 'tv' && 
                   d.id === titleDetails.id && 
                   d.season === selectedSeason;
          }
        });

        if (download?.path) {
          const encodedPath = encodeURIComponent(download.path.replace(/^.*[\\\/]/, ''));
          const videoUrl = `${API_URL}/downloaded/${encodedPath}`;
          window.open(videoUrl, '_blank');
        } else {
          toast.error('Video path not found');
        }
      } catch (error) {
        console.error('Error getting video path:', error);
        toast.error('Failed to get video path');
      }
    } else {
      const encodedPath = encodeURIComponent(videoPath.replace(/^.*[\\\/]/, ''));
      const videoUrl = `${API_URL}/downloaded/${encodedPath}`;
      window.open(videoUrl, '_blank');
    }
  };

  const handleAddToWatchlist = async () => {
    try {
      await axios.post(`${SERVER_WATCHLIST_URL}/add`, {
        name: titleDetails.slug,
        url,
        season: titleDetails.season_count
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

  const getDownloadStatus = (type, seasonNum = null, episodeNum = null) => {
    if (type === 'movie') {
      const status = downloadStatus.movies;
      if (!status) return null;
      
      if (status.downloading) return <span className="badge bg-primary"><FaDownload /> Downloading</span>;
      if (status.queued) return <span className="badge bg-warning">In Queue</span>;
      if (status.downloaded) return <span className="badge bg-success">Downloaded</span>;
      return null;
    } else {
      const status = downloadStatus.tv?.[`S${seasonNum}E${episodeNum}`];
      if (!status) return null;
      
      if (status.downloading) return <span className="badge bg-primary"><FaDownload /> Downloading</span>;
      if (status.queued) return <span className="badge bg-warning">In Queue</span>;
      if (status.downloaded) return <span className="badge bg-success">Downloaded</span>;
      return null;
    }
  };

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
              {getDownloadStatus('movie')}
              {downloadStatus.movies?.downloaded ? (
                <Button 
                  variant="success" 
                  onClick={() => handleWatchVideo(downloadStatus.movies.path)}
                >
                  <FaPlay className="me-2" /> Watch
                </Button>
              ) : (
                <Button 
                  variant="primary" 
                  onClick={() => handleDownloadEpisode(1, 1)}
                >
                  <FaDownload className="me-2" /> Download Film
                </Button>
              )}
            </Col>
          </Row>
        )}

        {/* TV Show Seasons and Episodes */}
        {titleDetails.type === 'tv' && (
          <>
            {[...Array(titleDetails.season_count)].map((_, index) => (
              <div key={index} className="mb-4">
                <h4 className="d-flex justify-content-between align-items-center">
                  <span>Season {index + 1}</span>
                  <Button 
                    variant="primary"
                    onClick={() => handleDownloadSeason(index + 1)}
                    className="me-2"
                  >
                    <FaDownload /> Download Season
                  </Button>
                </h4>
                <Row xs={2} md={4} className="g-4">
                  {episodes.filter(ep => ep.season === index + 1).map((episode) => {
                    const episodeKey = `S${selectedSeason}E${episode.number}`;
                    const isDownloaded = downloadStatus.tv?.[episodeKey]?.downloaded;
                    
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
                          
                          {getDownloadStatus('tv', selectedSeason, episode.number)}
                          {isDownloaded ? (
                            <Button 
                              variant="success" 
                              onClick={() => handleWatchVideo(downloadStatus.tv[episodeKey].path)}
                            >
                              <FaPlay className="me-2" /> Watch
                            </Button>
                          ) : (
                            <Button 
                              variant="primary" 
                              onClick={() => handleDownloadEpisode(selectedSeason, episode.number)}
                            >
                              <FaDownload className="me-2" /> Download
                            </Button>
                          )}
                        </div>
                      </Col>
                    );
                  })}
                </Row>
              </div>
            ))}
          </>
        )}
      </Container>

      {/* Modal Video Player */}
      <Modal show={false} onHide={() => {}} size="lg" centered>
        <Modal.Body>
          <video 
            src="" 
            controls 
            autoPlay 
            style={{ width: '100%' }}
          />
        </Modal.Body>
      </Modal>
    </Container>
  );
};

TitleDetail.propTypes = {
  theme: PropTypes.string.isRequired
};

export default TitleDetail;