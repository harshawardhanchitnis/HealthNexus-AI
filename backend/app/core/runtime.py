"""Explicit infrastructure policy; independent of provider or deployment hostname."""
import os


def low_memory():
    return os.getenv('HEALTHNEXUS_LOW_MEMORY', 'false').lower() == 'true'


def operational_country(country):
    if low_memory() and country != 'IN':
        raise ValueError('This public deployment is India-operational-only; foreign nodes are saved federation evidence only.')
