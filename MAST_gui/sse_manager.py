"""
Server-Sent Events (SSE) manager for broadcasting notifications to connected clients
"""
import logging
import queue
import time
from threading import Lock
from typing import Dict

logger = logging.getLogger(__name__)


class SSEConnectionManager:
    """Manages SSE connections and broadcasts messages to all connected clients"""
    
    def __init__(self):
        self._clients: Dict[str, queue.Queue] = {}
        self._lock = Lock()
    
    def add_client(self, client_id: str) -> queue.Queue:
        """Add a new SSE client connection"""
        with self._lock:
            client_queue = queue.Queue(maxsize=100)
            self._clients[client_id] = client_queue
            logger.info(f"SSE client connected: {client_id} (total: {len(self._clients)})")
            return client_queue
    
    def remove_client(self, client_id: str):
        """Remove an SSE client connection"""
        with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(f"SSE client disconnected: {client_id} (total: {len(self._clients)})")
    
    def broadcast(self, event_type: str, data: dict):
        """Broadcast a message to all connected clients"""
        with self._lock:
            disconnected = []
            for client_id, client_queue in self._clients.items():
                try:
                    # Non-blocking put with timeout
                    client_queue.put({
                        'event': event_type,
                        'data': data,
                        'timestamp': time.time()
                    }, block=False)
                except queue.Full:
                    logger.warning(f"Client queue full, dropping message for {client_id}")
                    disconnected.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected:
                self.remove_client(client_id)
            
            if self._clients:
                logger.debug(f"Broadcast {event_type} to {len(self._clients)} clients")
    
    @property
    def client_count(self) -> int:
        """Get number of connected clients"""
        with self._lock:
            return len(self._clients)


# Global SSE manager instance
sse_manager = SSEConnectionManager()
