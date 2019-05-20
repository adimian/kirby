import pytest

from kirby.scheduler.supervisor import Supervisor


def test_scheduler_can_be_created_with_defaults():
    assert Supervisor()


def test_scheduler_can_get_due_processes():
    scheduler = Supervisor()

    assert Supervisor().get_due_processes()
