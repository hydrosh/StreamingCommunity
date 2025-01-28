import threading

class ProgressCallback:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.progress = 0
                    cls._instance.total_segments = 0
                    cls._instance.downloaded_segments = 0
                    cls._instance.callbacks = []
        return cls._instance

    def register_callback(self, callback):
        """Register a callback function to be called when progress updates"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback):
        """Unregister a callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def set_total_segments(self, total):
        """Set the total number of segments to download"""
        self.total_segments = total
        self.downloaded_segments = 0
        self.progress = 0
        self._notify_callbacks()

    def increment_progress(self):
        """Increment the progress by one segment"""
        self.downloaded_segments += 1
        self.progress = int((self.downloaded_segments / self.total_segments) * 100) if self.total_segments > 0 else 0
        self._notify_callbacks()

    def _notify_callbacks(self):
        """Notify all registered callbacks of the progress update"""
        for callback in self.callbacks:
            callback(self.progress)

    def reset(self):
        """Reset progress tracking"""
        self.progress = 0
        self.total_segments = 0
        self.downloaded_segments = 0
        self._notify_callbacks()
