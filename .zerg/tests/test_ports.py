"""Tests for MAHABHARATHA v2 Port Allocator."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ports import PortAllocator, PortAssignment


class TestPortAssignment:
    """Tests for PortAssignment dataclass."""

    def test_port_assignment_creation(self):
        """Test PortAssignment can be created."""
        from datetime import datetime

        pa = PortAssignment(port=50000, worker_id="w1", assigned_at=datetime.now())
        assert pa.port == 50000
        assert pa.worker_id == "w1"


class TestPortAllocator:
    """Tests for PortAllocator class."""

    def test_allocator_initialization(self):
        """Test allocator initializes correctly."""
        pa = PortAllocator()
        assert pa.assignments == {}
        assert pa.used_ports == set()

    def test_allocate_returns_port(self):
        """Test allocation returns a port."""
        pa = PortAllocator()
        port = pa.allocate("w1")
        assert isinstance(port, int)

    def test_port_in_range(self):
        """Test allocated port is in ephemeral range."""
        pa = PortAllocator()
        port = pa.allocate("w1")
        assert 49152 <= port <= 65535

    def test_allocate_unique(self):
        """Test multiple workers get unique ports."""
        pa = PortAllocator()
        ports = [pa.allocate(f"w{i}") for i in range(10)]
        assert len(set(ports)) == 10

    def test_same_worker_same_port(self):
        """Test same worker always gets same port."""
        pa = PortAllocator()
        p1 = pa.allocate("w1")
        p2 = pa.allocate("w1")
        assert p1 == p2

    def test_release(self):
        """Test releasing a port."""
        pa = PortAllocator()
        pa.allocate("w1")
        pa.release("w1")
        assert pa.get_assignment("w1") is None

    def test_release_nonexistent(self):
        """Test releasing nonexistent worker doesn't raise."""
        pa = PortAllocator()
        # Should not raise
        pa.release("nonexistent")

    def test_get_assignment(self):
        """Test getting an assignment."""
        pa = PortAllocator()
        port = pa.allocate("w1")
        assignment = pa.get_assignment("w1")
        assert assignment is not None
        assert assignment.port == port
        assert assignment.worker_id == "w1"

    def test_get_assignment_nonexistent(self):
        """Test getting nonexistent assignment returns None."""
        pa = PortAllocator()
        assert pa.get_assignment("nonexistent") is None

    def test_release_frees_port(self):
        """Test released port is no longer in used_ports."""
        pa = PortAllocator()
        port = pa.allocate("w1")
        assert port in pa.used_ports
        pa.release("w1")
        assert port not in pa.used_ports


class TestPortAvailability:
    """Tests for port availability checking."""

    def test_port_availability_check(self):
        """Test _is_port_available method exists and works."""
        pa = PortAllocator()
        # High ephemeral port should typically be available
        result = pa._is_port_available(65000)
        assert isinstance(result, bool)

    def test_allocated_port_is_actually_available(self):
        """Test that allocated ports are actually usable."""
        import socket

        pa = PortAllocator()
        port = pa.allocate("w1")

        # Try to bind to the port - should work
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                s.listen(1)
                # Port is usable
                assert True
        except OSError:
            pytest.fail(f"Allocated port {port} is not actually available")


class TestConstants:
    """Tests for port range constants."""

    def test_ephemeral_range_constants(self):
        """Test ephemeral range constants are correct."""
        assert PortAllocator.EPHEMERAL_START == 49152
        assert PortAllocator.EPHEMERAL_END == 65535
